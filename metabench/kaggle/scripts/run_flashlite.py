#!/usr/bin/env python3
"""Run HCH HLE-12 tasks with Gemini Flash-Lite on a fresh dedicated kernel.

Unlike run_hch_hle12_with_model.py, this script ALSO injects MODEL_PROXY_URL and
MODEL_PROXY_API_KEY into the remote code, because the dedicated kernel doesn't have
those env vars pre-set (unlike the original shared notebook which had them from the
notebook environment).

Usage (from kaggle/ directory):
  python scripts/run_flashlite.py

DO NOT CHECK IN — temporary script.
"""

import argparse
import ast
import base64
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Bridge imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "option_a_bridge"))
from kernel_bridge import (
    ExecutionTimeoutError,
    JupyterKernelBridge,
    KernelBridgeError,
    KernelBusyError,
    TokenRejectedError,
)

RESULT_START = "__VOICETREE_SUBMIT_RESULT_START__"
RESULT_END = "__VOICETREE_SUBMIT_RESULT_END__"

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples" / "hch_hle12"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

MODEL_ID = "google/gemini-2.5-flash-lite"
MODEL_PROXY_URL = "https://mp-staging.kaggle.net/models/openapi"
MODEL_PROXY_API_KEY = "kaggle-benchmarks:CiUAv1LKoWHO8dE8NwJJvQf5kBtZ1CKi+jckb8ZBGb5A8oEIOprGEpgBAKysbH73Otzu2rzbIwMyIbOICz4tZmBH8aOkQE0SGlie0mC2guWDAYxSMQeoE2mII/zwp7v7hKZ0L5q/c1V3gK5DxoWCMWkVZsVu4VSlSuIswzTT1VlR+VQximZP/+ETZ8NK+jCwBFLZ41ph+jeTYAUucXVAj9/GAhLJ/x2FYmaBLKUx2J07HkR/NnrDzWnHdNVdmnx7XJE="

TASK_ORDER = []
for qnum in [41, 43, 44, 48, 49, 52, 53, 55, 57, 65, 68, 99]:
    TASK_ORDER.append(f"q{qnum}_hch.py")
    TASK_ORDER.append(f"q{qnum}_vanilla.py")


def _build_remote_code(task_path: Path, source: str) -> str:
    """Build remote execution code with model override + proxy credentials injected."""
    # Strip max_output_tokens kwarg — LLMChat.prompt() on this kernel does not support it.
    source = re.sub(r',\s*max_output_tokens=\d+', '', source)
    source = re.sub(r'max_output_tokens=\d+,?\s*', '', source)

    encoded = base64.b64encode(source.encode("utf-8")).decode("ascii")
    remote_task_path = task_path.as_posix()

    # Swap model in-place on the existing kbench.llm — do NOT evict modules or reset env.
    # Evicting kaggle_benchmarks forces re-init with the static MODEL_PROXY_API_KEY which
    # is IP-locked. The notebook's session-based credentials work but only on the pre-init llm.
    # kbench.llm.model is a plain attribute — reassigning is safe and takes effect immediately.
    model_swap = f"""
import kaggle_benchmarks as _kbench_swap
_kbench_swap.llm.model = {MODEL_ID!r}
_kbench_swap.llm.name = {MODEL_ID!r}
del _kbench_swap
""".strip()

    return f"""
{model_swap}

import base64
import inspect
import json
import linecache
import pathlib
import sys
import traceback
import types

import kaggle_benchmarks as kbench

RESULT_START = {RESULT_START!r}
RESULT_END = {RESULT_END!r}
TASK_SOURCE = base64.b64decode({encoded!r}).decode("utf-8")
TASK_PATH = {remote_task_path!r}
MODULE_NAME = "__voicetree_submit_task__"


def json_safe(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {{str(k): json_safe(v) for k, v in value.items()}}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return repr(value)


def snapshot(pattern):
    payload = {{}}
    for path in pathlib.Path(".").glob(pattern):
        if path.is_file():
            payload[path.name] = path.read_text()
    return payload


before_task_files = snapshot("*.task.json")
before_run_files = snapshot("*.run.json")
payload = {{"task_files": {{}}, "run_files": {{}}, "judge_notes": []}}

try:
    module = types.ModuleType(MODULE_NAME)
    module.__file__ = TASK_PATH
    module.__dict__["__name__"] = MODULE_NAME
    sys.modules[MODULE_NAME] = module
    linecache.cache[TASK_PATH] = (
        len(TASK_SOURCE),
        None,
        TASK_SOURCE.splitlines(keepends=True),
        TASK_PATH,
    )
    exec(compile(TASK_SOURCE, TASK_PATH, "exec"), module.__dict__, module.__dict__)

    task_candidates = [
        value
        for value in module.__dict__.values()
        if isinstance(value, kbench.tasks.Task)
        and getattr(value.func, "__module__", None) == MODULE_NAME
    ]
    if len(task_candidates) != 1:
        raise RuntimeError(
            f"Expected exactly one Task, found {{len(task_candidates)}}."
        )

    task_fn = task_candidates[0]
    task_params = list(inspect.signature(task_fn.func).parameters.values())
    if len(task_params) == 0:
        run = task_fn.run()
    elif len(task_params) == 1:
        run = task_fn.run(kbench.llm)
    else:
        raise RuntimeError(f"Task takes unexpected params: {{len(task_params)}}")

    payload.update({{
        "task_name": task_fn.name,
        "run_id": run.id,
        "status": getattr(run.status, "name", str(run.status)),
        "passed": bool(run.passed),
        "result": json_safe(run.result),
        "error_message": run.error_message,
        "judge_notes": [
            result.expectation for result in run.assertion_results if result.expectation
        ],
    }})
except Exception as exc:
    payload["wrapper_error"] = {{
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(),
    }}
finally:
    after_task_files = snapshot("*.task.json")
    after_run_files = snapshot("*.run.json")
    payload["task_files"] = {{
        name: contents
        for name, contents in after_task_files.items()
        if before_task_files.get(name) != contents
    }}
    payload["run_files"] = {{
        name: contents
        for name, contents in after_run_files.items()
        if before_run_files.get(name) != contents
    }}
    print(RESULT_START)
    print(json.dumps(payload))
    print(RESULT_END)
""".strip()


def extract_payload(stdout: str) -> dict:
    start = stdout.find(RESULT_START)
    end = stdout.find(RESULT_END)
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError("Bridge output missing payload marker")
    body = stdout[start + len(RESULT_START):end].strip()
    return json.loads(body)


def run_one_task(bridge: JupyterKernelBridge, task_file: Path, timeout_s: float = 2400.0) -> dict:  # Default 2400s — HLE questions can take up to 40 min on strong models
    source = task_file.read_text(encoding="utf-8")
    remote_code = _build_remote_code(task_file, source)

    t0 = time.time()
    try:
        execution = bridge.run(remote_code, timeout_seconds=timeout_s)
    except TokenRejectedError as exc:
        return {"error": "TOKEN_REJECTED", "message": str(exc), "task_file": task_file.name}
    except KernelBusyError as exc:
        return {"error": "KERNEL_BUSY", "message": str(exc), "task_file": task_file.name}
    except ExecutionTimeoutError as exc:
        return {"error": "EXECUTION_TIMEOUT", "message": str(exc), "task_file": task_file.name}
    except KernelBridgeError as exc:
        return {"error": "BRIDGE_ERROR", "message": str(exc), "task_file": task_file.name}
    except Exception as exc:
        return {"error": "NETWORK_ERROR", "message": str(exc), "task_file": task_file.name}

    elapsed = time.time() - t0

    if execution.stderr:
        print(f"  [stderr] {execution.stderr[:500]}", file=sys.stderr)

    try:
        payload = extract_payload(execution.stdout)
    except Exception as exc:
        return {
            "error": "PARSE_ERROR",
            "message": str(exc),
            "task_file": task_file.name,
            "stdout_tail": execution.stdout[-2000:],
        }

    payload["task_file"] = task_file.name
    payload["elapsed_s"] = round(elapsed, 2)
    payload["model_id"] = MODEL_ID
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--start-from", default=None)
    ap.add_argument("--idle-wait", type=float, default=60.0)
    ap.add_argument("--task-timeout", type=float, default=2400.0)  # Default 2400s — HLE questions can take up to 40 min on strong models
    ap.add_argument("--sleep-between", type=float, default=15.0)
    args = ap.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    results_path = RESULTS_DIR / f"hch_hle12_v2_flashlite_{run_ts}.jsonl"

    tasks = [EXAMPLES_DIR / fname for fname in TASK_ORDER]
    if args.start_from:
        idx = next((i for i, t in enumerate(tasks) if t.name == args.start_from), None)
        if idx is None:
            print(f"[run] --start-from {args.start_from!r} not found", file=sys.stderr)
            return 2
        tasks = tasks[idx:]

    print(f"[run] model={MODEL_ID}", file=sys.stderr)
    print(f"[run] {len(tasks)} tasks → {results_path}", file=sys.stderr)
    for t in tasks:
        print(f"  {t.name}", file=sys.stderr)

    if args.dry_run:
        print("[run] dry-run — exiting", file=sys.stderr)
        return 0

    bridge = JupyterKernelBridge(idle_wait_seconds=args.idle_wait, request_timeout_seconds=30.0)

    results = []
    for i, task_file in enumerate(tasks):
        print(f"\n[run] [{i+1}/{len(tasks)}] {task_file.name} ...", file=sys.stderr)

        result = run_one_task(bridge, task_file, timeout_s=args.task_timeout)
        results.append(result)

        if "error" in result:
            print(f"  ERROR: {result['error']} — {result.get('message', '')}", file=sys.stderr)
            if result["error"] == "TOKEN_REJECTED":
                print("[run] STOPPING — token rejected.", file=sys.stderr)
                with open(results_path, "a") as fh:
                    for r in results:
                        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                return 6
        else:
            status = result.get("status", "?")
            passed = result.get("passed", "?")
            name = result.get("task_name", task_file.name)
            elapsed = result.get("elapsed_s", "?")
            print(f"  {name}: status={status}, passed={passed}, elapsed={elapsed}s", file=sys.stderr)
            notes = result.get("judge_notes") or []
            for note in notes:
                print(f"    note: {note}", file=sys.stderr)

        with open(results_path, "a") as fh:
            fh.write(json.dumps(result, ensure_ascii=False) + "\n")

        if i < len(tasks) - 1:
            print(f"  sleeping {args.sleep_between}s ...", file=sys.stderr)
            time.sleep(args.sleep_between)

    print(f"\n[run] done — {len(results)} tasks — results at {results_path}", file=sys.stderr)

    passed_count = sum(1 for r in results if r.get("passed") is True)
    failed_count = sum(1 for r in results if r.get("passed") is False)
    error_count = sum(1 for r in results if "error" in r)
    print(f"[run] passed={passed_count}  failed={failed_count}  errors={error_count}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
