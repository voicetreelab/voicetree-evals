"""
colab_runner.py — Run kbench task files in Colab (or locally) without Kaggle tokens.

Replaces the Option A bridge's `kbench.llm` (Kaggle-specific) with a
GoogleGenAI instance using a standard Google AI Studio key.

Usage (in a Colab cell or locally):
    !pip install kaggle-benchmarks google-genai
    import os; os.environ["GOOGLE_API_KEY"] = "AIza..."  # or set in env
    from colab_runner import run_task
    run_task("examples/hch_spike/q1.py")

Requires: GOOGLE_API_KEY env var (free Google AI Studio key works).
Alternatively set OPENAI_API_KEY and flip LLM_PROVIDER below.
"""

from __future__ import annotations

import ast
import base64
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

import kaggle_benchmarks as kbench
from google import genai
from kaggle_benchmarks.actors.llms import GoogleGenAI

# ── LLM configuration ─────────────────────────────────────────────────────────
# Swap model here if desired. gemini-2.5-flash matches Kaggle's default.
MODEL = os.environ.get("KBENCH_MODEL", "gemini-2.5-flash")


def _make_llm() -> GoogleGenAI:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "Set GOOGLE_API_KEY (free at aistudio.google.com) before running."
        )
    client = genai.Client(api_key=api_key)
    return GoogleGenAI(client=client, model=MODEL)


# ── Task runner ────────────────────────────────────────────────────────────────

def run_task(task_file: str | Path) -> dict:
    """Load and run a single @kbench.task file. Returns the run payload dict."""
    task_path = Path(task_file).resolve()
    source = task_path.read_text()

    module_name = "__colab_run_task__"
    module = types.ModuleType(module_name)
    module.__file__ = str(task_path)
    module.__dict__["__name__"] = module_name
    sys.modules[module_name] = module

    exec(compile(source, str(task_path), "exec"), module.__dict__)

    task_candidates = [
        v for v in module.__dict__.values()
        if isinstance(v, kbench.tasks.Task)
        and getattr(v.func, "__module__", None) == module_name
    ]
    if len(task_candidates) != 1:
        raise RuntimeError(
            f"Expected exactly 1 @kbench.task in {task_path}, found {len(task_candidates)}."
        )

    task_fn = task_candidates[0]
    import inspect
    params = list(inspect.signature(task_fn.func).parameters.values())

    llm = _make_llm()
    if len(params) == 0:
        run = task_fn.run()
    elif len(params) == 1:
        run = task_fn.run(llm)
    else:
        raise RuntimeError(f"Task {task_fn.name} has unexpected signature.")

    payload = {
        "task_name": task_fn.name,
        "status": getattr(run.status, "name", str(run.status)),
        "passed": bool(run.passed),
        "result": run.result,
        "error_message": run.error_message,
    }
    print(json.dumps(payload, indent=2, default=str))
    return payload


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run a kbench task file in Colab/local env.")
    parser.add_argument("task_file", type=Path)
    args = parser.parse_args()
    run_task(args.task_file)
