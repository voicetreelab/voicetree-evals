from __future__ import annotations

import argparse
import ast
import base64
import json
import sys
from pathlib import Path
from typing import Any

from kernel_bridge import (
    ExecutionTimeoutError,
    KernelBridgeError,
    KernelBusyError,
    TokenRejectedError,
    run_on_kaggle,
)

RESULT_START = "__VOICETREE_SUBMIT_RESULT_START__"
RESULT_END = "__VOICETREE_SUBMIT_RESULT_END__"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Submit one local @kbench.task file to the live Kaggle notebook kernel."
    )
    parser.add_argument("task_file", type=Path, help="Path to a Python file containing one @kbench.task task.")
    return parser.parse_args()


def _count_task_decorators(source: str) -> int:
    tree = ast.parse(source)
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                target = decorator.func
            else:
                target = decorator
            if isinstance(target, ast.Attribute) and target.attr == "task":
                count += 1
            elif isinstance(target, ast.Name) and target.id == "task":
                count += 1
    return count


def _build_remote_code(task_path: Path, source: str) -> str:
    encoded = base64.b64encode(source.encode("utf-8")).decode("ascii")
    remote_task_path = task_path.as_posix()

    return f"""
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
            f"Expected exactly one Task defined in {{TASK_PATH}}, found {{len(task_candidates)}}."
        )

    task_fn = task_candidates[0]
    task_params = list(inspect.signature(task_fn.func).parameters.values())
    if len(task_params) == 0:
        run = task_fn.run()
    elif len(task_params) == 1:
        run = task_fn.run(kbench.llm)
    else:
        raise RuntimeError(
            f"Expected task {{task_fn.name}} to take 0 or 1 parameters, found {{len(task_params)}}."
        )

    payload.update(
        {{
            "task_name": task_fn.name,
            "run_id": run.id,
            "status": getattr(run.status, "name", str(run.status)),
            "passed": bool(run.passed),
            "result": json_safe(run.result),
            "error_message": run.error_message,
            "judge_notes": [
                result.expectation for result in run.assertion_results if result.expectation
            ],
        }}
    )
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


def _extract_submission_payload(stdout: str) -> dict[str, Any]:
    start = stdout.find(RESULT_START)
    end = stdout.find(RESULT_END)
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError(
            "Bridge output did not contain a submission payload marker."
        )
    body = stdout[start + len(RESULT_START) : end].strip()
    return json.loads(body)


def _print_remote_outputs(payload: dict[str, Any]) -> None:
    print(f"status={payload.get('status', 'FAILED')}")
    print(f"passed={payload.get('passed', False)}")
    if payload.get("task_name"):
        print(f"task={payload['task_name']}")
    if payload.get("run_id"):
        print(f"run_id={payload['run_id']}")
    if "result" in payload:
        print(f"result={payload['result']!r}")

    judge_notes = payload.get("judge_notes") or []
    print(f"judge_notes={len(judge_notes)}")
    for note in judge_notes:
        print(f"judge_note={note}")

    for section in ("task_files", "run_files"):
        files = payload.get(section) or {}
        for name, contents in files.items():
            print(f"{section[:-1]}={name}")
            print(contents)

    if payload.get("error_message"):
        print("task_error_message=")
        print(payload["error_message"])

    if payload.get("wrapper_error"):
        print("wrapper_error=")
        print(payload["wrapper_error"]["traceback"])


def main() -> int:
    args = parse_args()
    task_file = args.task_file.resolve()

    if not task_file.is_file():
        print(f"Task file not found: {task_file}", file=sys.stderr)
        return 2

    source = task_file.read_text()
    decorator_count = _count_task_decorators(source)
    if decorator_count != 1:
        print(
            f"Expected exactly one @kbench.task in {task_file}, found {decorator_count}.",
            file=sys.stderr,
        )
        return 2

    remote_code = _build_remote_code(task_file, source)

    try:
        execution = run_on_kaggle(remote_code, timeout_seconds=300.0)
    except TokenRejectedError as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except KernelBusyError as exc:
        print(str(exc), file=sys.stderr)
        return 4
    except ExecutionTimeoutError as exc:
        print(str(exc), file=sys.stderr)
        return 5
    except KernelBridgeError as exc:
        print(f"Bridge failed: {exc}", file=sys.stderr)
        return 6

    if execution.stderr:
        print(execution.stderr, file=sys.stderr, end="")

    payload = _extract_submission_payload(execution.stdout)
    _print_remote_outputs(payload)

    if execution.error is not None:
        print("\n".join(execution.error.traceback), file=sys.stderr)
        return 7

    if payload.get("wrapper_error"):
        return 8

    return 0 if payload.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
