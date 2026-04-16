#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "option_a_bridge"))
from kernel_bridge import (  # noqa: E402
    ExecutionTimeoutError,
    JupyterKernelBridge,
    KernelBridgeError,
    KernelBusyError,
    TokenRejectedError,
)


RESULT_START = "__VOICETREE_SUBMIT_RESULT_START__"
RESULT_END = "__VOICETREE_SUBMIT_RESULT_END__"

TASK_PATH = Path(__file__).resolve().parents[1] / "examples" / "coupled_jobshop_spike" / "cjs_5x6.py"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
DEFAULT_SEEDS = [1, 2, 3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the coupled jobshop 5x6 Kaggle spike for one model across seeds.")
    parser.add_argument("--model", required=True, help="Model slug, e.g. google/gemini-3.1-pro-preview")
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS, help="Seeds to run (default: 1 2 3)")
    parser.add_argument("--task-file", type=Path, default=TASK_PATH, help="Task file to submit")
    parser.add_argument("--notebook-url", default=None, help="Full Kaggle Jupyter URL with token query param")
    parser.add_argument("--idle-wait", type=float, default=60.0, help="Seconds to wait for kernel idle before each run")
    parser.add_argument("--task-timeout", type=float, default=2400.0, help="Seconds timeout per task")
    parser.add_argument("--sleep-between", type=float, default=15.0, help="Seconds to sleep between runs")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSONL output path")
    return parser.parse_args()


def parse_notebook_url(notebook_url: str) -> tuple[str, str]:
    parsed = urlparse(notebook_url)
    token = parse_qs(parsed.query).get("token", [None])[0]
    if not parsed.scheme or not parsed.netloc or not token:
        raise ValueError("Notebook URL must include scheme, host, and token query param.")
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    return base_url, token


def build_bridge(args: argparse.Namespace) -> JupyterKernelBridge:
    if args.notebook_url:
        base_url, token = parse_notebook_url(args.notebook_url)
        return JupyterKernelBridge(
            base_url=base_url,
            token=token,
            idle_wait_seconds=args.idle_wait,
        )
    return JupyterKernelBridge(idle_wait_seconds=args.idle_wait)


def _build_remote_code(task_path: Path, source: str, model_id: str, seed: int) -> str:
    encoded = base64.b64encode(source.encode("utf-8")).decode("ascii")
    remote_task_path = task_path.as_posix()

    model_override = f"""
import os as _os_override, sys as _sys_override
_os_override.environ['LLM_DEFAULT'] = {model_id!r}
for _k in list(_sys_override.modules.keys()):
    if _k.startswith('kaggle_benchmarks'):
        del _sys_override.modules[_k]
del _os_override, _sys_override
""".strip()

    return f"""
{model_override}

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
TARGET_SEED = {seed!r}


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
    module.__dict__["CJS_TARGET_SEED"] = TARGET_SEED
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


def extract_payload(stdout: str) -> dict[str, Any]:
    start = stdout.find(RESULT_START)
    end = stdout.find(RESULT_END)
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError("Bridge output missing payload marker")
    body = stdout[start + len(RESULT_START):end].strip()
    return json.loads(body)


def _error_row(model_id: str, seed: int, *, error: str, message: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        "model": model_id,
        "seed": seed,
        "n_jobs": 5,
        "n_machines": 6,
        "error": f"{error}: {message}",
        "bridge_error_type": error,
        "stop_reason": error.lower(),
        "killed": False,
        "infeasible": False,
        "wall_s": None,
    }
    if extra:
        row.update(extra)
    return row


def run_one_task(
    bridge: JupyterKernelBridge,
    task_file: Path,
    model_id: str,
    seed: int,
    timeout_s: float,
) -> dict[str, Any]:
    source = task_file.read_text(encoding="utf-8")
    remote_code = _build_remote_code(task_file, source, model_id, seed)

    t0 = time.time()
    try:
        execution = bridge.run(remote_code, timeout_seconds=timeout_s)
    except TokenRejectedError as exc:
        raise
    except KernelBusyError as exc:
        return _error_row(model_id, seed, error="KERNEL_BUSY", message=str(exc))
    except ExecutionTimeoutError as exc:
        return _error_row(model_id, seed, error="EXECUTION_TIMEOUT", message=str(exc))
    except KernelBridgeError as exc:
        return _error_row(model_id, seed, error="BRIDGE_ERROR", message=str(exc))
    except Exception as exc:
        return _error_row(model_id, seed, error="NETWORK_ERROR", message=str(exc))

    elapsed = time.time() - t0
    payload = extract_payload(execution.stdout)

    if payload.get("wrapper_error"):
        row = _error_row(
            model_id,
            seed,
            error=payload["wrapper_error"].get("type", "WRAPPER_ERROR"),
            message=payload["wrapper_error"].get("message", "wrapper failed"),
            extra={"wrapper_traceback": payload["wrapper_error"].get("traceback")},
        )
    else:
        result = payload.get("result")
        if isinstance(result, dict):
            row = result
        else:
            row = _error_row(
                model_id,
                seed,
                error="RESULT_PARSE_ERROR",
                message=f"Task returned non-dict result: {type(result).__name__}",
            )

    row["model"] = model_id
    row["seed"] = seed
    row["bridge_status"] = payload.get("status")
    row["bridge_passed"] = payload.get("passed")
    row["task_name"] = payload.get("task_name")
    row["run_id"] = payload.get("run_id")
    row["judge_notes"] = payload.get("judge_notes") or []
    row["bridge_elapsed_s"] = round(elapsed, 2)
    row["task_file"] = task_file.name
    row["run_file_names"] = sorted((payload.get("run_files") or {}).keys())
    return row


def output_path_for(args: argparse.Namespace) -> Path:
    if args.output is not None:
        return args.output
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    model_tag = re.sub(r"[^a-zA-Z0-9_-]", "_", args.model)
    return RESULTS_DIR / f"cjs_5x6_{model_tag}_{stamp}.jsonl"


def main() -> int:
    args = parse_args()
    task_file = args.task_file.resolve()
    if not task_file.is_file():
        print(f"Task file not found: {task_file}", file=sys.stderr)
        return 2

    output_path = output_path_for(args)
    bridge = build_bridge(args)

    rows: list[dict[str, Any]] = []
    with output_path.open("w", encoding="utf-8") as handle:
        for index, seed in enumerate(args.seeds):
            print(f"[run] seed={seed} model={args.model}")
            try:
                row = run_one_task(
                    bridge=bridge,
                    task_file=task_file,
                    model_id=args.model,
                    seed=seed,
                    timeout_s=args.task_timeout,
                )
            except TokenRejectedError as exc:
                print(str(exc), file=sys.stderr)
                print(f"[run] stopping on auth failure before seed={seed}", file=sys.stderr)
                return 3

            rows.append(row)
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()

            stop_reason = row.get("stop_reason")
            gap_pct = row.get("gap_pct")
            error = row.get("error")
            print(
                f"[done] seed={seed} stop_reason={stop_reason} "
                f"gap_pct={gap_pct} error={error}"
            )

            if index != len(args.seeds) - 1:
                time.sleep(args.sleep_between)

    print(f"[done] wrote {len(rows)} rows to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
