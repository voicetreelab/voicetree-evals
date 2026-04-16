#!/usr/bin/env python3
"""Direct-proxy runner spike — bypass Kaggle Jupyter bridge entirely.

Usage:
    cd ~/repos/voicetree-evals/metabench/kaggle
    python scripts/direct_runner_spike.py --model google/gemini-2.5-flash \
        --task examples/hch_hle12/q41_hch.py [--task examples/hch_hle12/q41_vanilla.py ...]

Emits one JSONL line per task to stdout (append to a results file with >>).
Requires MODEL_PROXY_URL + MODEL_PROXY_API_KEY in kaggle/.env (or env vars).
NOTE: proxy is IP-locked for inference — must be run from Kaggle's network.
"""

import argparse, importlib.util, json, os, re, sys, time, types
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

PROXY_BASE = os.environ["MODEL_PROXY_URL"].rstrip("/")  # e.g. .../openapi
PROXY_KEY  = os.environ["MODEL_PROXY_API_KEY"]
HEADERS    = {"Authorization": f"Bearer {PROXY_KEY}", "Content-Type": "application/json"}


# ── proxy helpers ──────────────────────────────────────────────────────────────

def list_models() -> list[str]:
    """GET /models — works from any IP (model discovery only)."""
    r = requests.get("https://mp-staging.kaggle.net/models", headers=HEADERS, timeout=15)
    r.raise_for_status()
    return [m["id"] for m in r.json().get("data", [])]


def chat(model: str, prompt: str, max_tokens: int = 32768) -> tuple[str, dict[str, Any]]:
    """POST /v1/chat/completions — returns (text, usage)."""
    t0 = time.monotonic()
    r = requests.post(
        f"{PROXY_BASE}/v1/chat/completions",
        headers=HEADERS,
        json={"model": model, "messages": [{"role": "user", "content": prompt}],
              "max_tokens": max_tokens},
        timeout=120,
    )
    elapsed = time.monotonic() - t0
    r.raise_for_status()
    data = r.json()
    text = data["choices"][0]["message"]["content"]
    usage = data.get("usage", {})
    return text, usage, elapsed


# ── task loader ────────────────────────────────────────────────────────────────

def load_task(path: str) -> types.ModuleType:
    """Import a task file while stubbing out kaggle_benchmarks."""
    # Stub kbench so the @kbench.task decorator is a no-op
    stub = types.ModuleType("kaggle_benchmarks")
    stub.task = lambda **_: (lambda fn: fn)
    stub.assertions = types.SimpleNamespace(assert_true=lambda *a, **kw: None)
    sys.modules["kaggle_benchmarks"] = stub

    spec = importlib.util.spec_from_file_location("_task", path)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── judge ──────────────────────────────────────────────────────────────────────

def judge_answer(model: str, gold: str, response: str) -> tuple[bool, str]:
    prompt = (
        f'Gold answer: "{gold}"\n'
        f'Model response: "{response}"\n'
        'Did the model correctly state the gold answer? Reply YES or NO only.'
    )
    try:
        raw, _, _ = chat(model, prompt, max_tokens=16)
        return raw.strip().upper().startswith("YES"), raw.strip()
    except Exception as e:
        return False, f"JUDGE_ERROR: {e}"


# ── main ───────────────────────────────────────────────────────────────────────

def run_task(model: str, task_path: str) -> dict:
    mod  = load_task(task_path)
    arm  = "hch" if task_path.endswith("_hch.py") else "vanilla"
    qnum = int(re.search(r"q(\d+)_", Path(task_path).name).group(1))

    t0  = time.monotonic()
    raw, usage, elapsed = chat(model, mod.PROMPT)
    judge_pass, judge_raw = judge_answer(model, mod.GOLD_ANSWER, raw)

    # Re-use the task file's answer parser for metadata (no kbench needed)
    if arm == "hch":
        traj = mod._parse_hch_trajectory(raw)
        answer = traj.get("answer")
        p_correct = traj.get("p_correct")
    else:
        parsed = mod._parse_vanilla(raw)
        answer = parsed.get("answer")
        p_correct = parsed.get("p_correct")

    return {
        "question_id": qnum,
        "arm": arm,
        "model": model,
        "answer": answer,
        "gold": mod.GOLD_ANSWER,
        "judge_pass": judge_pass,
        "judge_raw": judge_raw,
        "p_correct": p_correct,
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "elapsed_s": round(elapsed, 2),
        "raw_response": raw[:500],  # truncated for JSONL size
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="google/gemini-2.5-flash")
    ap.add_argument("--task", action="append", dest="tasks", default=[])
    ap.add_argument("--list-models", action="store_true")
    args = ap.parse_args()

    if args.list_models:
        for m in list_models():
            print(m)
        return

    if not args.tasks:
        ap.error("--task is required (unless --list-models)")

    for task_path in args.tasks:
        result = run_task(args.model, task_path)
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
