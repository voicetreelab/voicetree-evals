#!/usr/bin/env python3
"""
Run HLE questions through `claude -p` headless, one agent per (question, arm).

Tests the fix for the per-batch architecture bug: each question gets a fresh
context, so there is no cross-question synthesis-time format inversion.

Usage:
  python3 hle_per_question.py \
      --range 41 100 \
      --arms vanilla metacog \
      --model sonnet \
      --concurrency 4 \
      --out results.jsonl

Output: one JSON object per (qid, arm) appended to --out (JSONL).
Resume by re-running with the same --out; completed (qid,arm) pairs are skipped.
"""

import argparse
import concurrent.futures
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

VAULT = Path(__file__).resolve().parents[1]
DATASET = VAULT / "datasets" / "hle" / "hle_prompts_only.json"

FORMAT_BLOCK = """\
OUTPUT FORMAT — strict. Your response must END with exactly two lines:
ANSWER: <your answer>
P_CORRECT: <float in [0,1]>

If the question is multipleChoice, ANSWER is a single capital letter.
If the question is exactMatch, ANSWER is the literal numeric/symbolic/phrase answer (no letter).
"""

VANILLA_PROMPT = """\
Solve the following question directly. Show whatever reasoning you need, then emit your final answer.

Question type: {answer_type}
Subject: {raw_subject}

QUESTION:
{question}

{format_block}"""

METACOG_INSTRUCTION = """\
Address the following metacognitive reflection prompt at BOTH the start and the end of this task:

"Go through atleast 2-3 levels on your reasoning towards the task/prompt you are assigned. At each level, reflect on the cognitive patterns of the level below — not the content, the thinking, the cognitive patterns. For example in level 1, identify what cognitive pattern you are using to solve this problem. In level 2. identify what meta-pattern you used to notice & identify that, Biases/uncertainties, etc. Finally, after going to 2-3 meta-levels recursively, circle back to the task - has this relfection actually improved my confidence in how to solve this problem & whether that it is correct? provide a prediction probability claim for that question."

Do this reflection BEFORE attempting the question, then solve the question, then do the reflection AGAIN after your candidate answer, and let your final P_CORRECT incorporate both passes.
"""

METACOG_PROMPT = """\
You are solving the following question.

{metacog_instruction}

Question type: {answer_type}
Subject: {raw_subject}

QUESTION:
{question}

{format_block}"""


def load_questions(lo: int, hi: int):
    with open(DATASET) as f:
        data = json.load(f)
    text_only = [q for q in data["eval_data"] if not q.get("has_image")]
    # Q41..Q100 (1-indexed) == text_only[40:100]
    return list(enumerate(text_only[lo - 1 : hi], start=lo))


def build_prompt(arm: str, q: dict) -> str:
    if arm == "vanilla":
        return VANILLA_PROMPT.format(
            answer_type=q.get("answer_type", "?"),
            raw_subject=q.get("raw_subject", "?"),
            question=q["question"],
            format_block=FORMAT_BLOCK,
        )
    return METACOG_PROMPT.format(
        answer_type=q.get("answer_type", "?"),
        raw_subject=q.get("raw_subject", "?"),
        question=q["question"],
        format_block=FORMAT_BLOCK,
        metacog_instruction=METACOG_INSTRUCTION,
    )


ANSWER_RE = re.compile(r"^\s*ANSWER:\s*(.+?)\s*$", re.MULTILINE)
PC_RE = re.compile(r"^\s*P_CORRECT:\s*([0-9]*\.?[0-9]+)\s*$", re.MULTILINE)


def parse_output(stdout: str):
    answers = ANSWER_RE.findall(stdout)
    pcs = PC_RE.findall(stdout)
    answer = answers[-1].strip() if answers else None
    try:
        p_correct = float(pcs[-1]) if pcs else None
    except ValueError:
        p_correct = None
    # reasoning = everything before the last ANSWER: line (keeps full work log)
    m = list(re.finditer(r"^\s*ANSWER:\s*.+?\s*$", stdout, re.MULTILINE))
    reasoning = stdout[: m[-1].start()].strip() if m else stdout.strip()
    return answer, p_correct, reasoning


def run_one(arm: str, qnum: int, q: dict, model: str, timeout: int, dry_run: bool):
    prompt = build_prompt(arm, q)
    if dry_run:
        return {
            "qnum": qnum,
            "qid": q["id"],
            "arm": arm,
            "answer": None,
            "p_correct": None,
            "duration_s": 0.0,
            "returncode": 0,
            "dry_run": True,
            "prompt_len": len(prompt),
            "stdout_tail": "",
        }
    cmd = [
        "claude",
        "--model", model,
        "--dangerously-skip-permissions",
        "-p", prompt,
    ]
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        rc = proc.returncode
        err = None
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = (e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or "")
        rc = -1
        err = f"timeout after {timeout}s"
    dt = time.time() - t0
    answer, p, reasoning = parse_output(stdout)
    return {
        "qnum": qnum,
        "qid": q["id"],
        "arm": arm,
        "answer_type": q.get("answer_type"),
        "raw_subject": q.get("raw_subject"),
        "answer": answer,
        "p_correct": p,
        "reasoning": reasoning,
        "duration_s": round(dt, 2),
        "returncode": rc,
        "error": err,
        "stdout": stdout,
        "stderr_tail": stderr[-2000:] if stderr else "",
    }


def load_done(out_path: Path):
    done = set()
    if out_path.exists():
        with open(out_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    done.add((r["qnum"], r["arm"]))
                except Exception:
                    pass
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--range", nargs=2, type=int, default=[41, 100], metavar=("LO", "HI"))
    ap.add_argument("--arms", nargs="+", default=["vanilla", "metacog"], choices=["vanilla", "metacog"])
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=900, help="seconds per call")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true", help="Skip actual claude calls; still writes stub rows")
    args = ap.parse_args()

    lo, hi = args.range
    questions = load_questions(lo, hi)
    args.out.parent.mkdir(parents=True, exist_ok=True)

    done = load_done(args.out)
    jobs = []
    for qnum, q in questions:
        for arm in args.arms:
            if (qnum, arm) in done:
                continue
            jobs.append((qnum, arm, q))

    print(f"[hle_per_question] {len(jobs)} jobs to run "
          f"({len(done)} already done), concurrency={args.concurrency}, "
          f"model={args.model}, timeout={args.timeout}s, out={args.out}",
          file=sys.stderr)

    if not jobs:
        print("Nothing to do.", file=sys.stderr)
        return

    fh = open(args.out, "a", buffering=1)  # line-buffered
    completed = 0
    t_start = time.time()

    def _task(job):
        qnum, arm, q = job
        return run_one(arm, qnum, q, args.model, args.timeout, args.dry_run)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(_task, j): j for j in jobs}
        for fut in concurrent.futures.as_completed(futs):
            qnum, arm, q = futs[fut]
            try:
                result = fut.result()
            except Exception as e:
                result = {
                    "qnum": qnum, "qid": q["id"], "arm": arm,
                    "answer": None, "p_correct": None,
                    "error": f"exception: {e!r}", "returncode": -2,
                }
            fh.write(json.dumps(result, ensure_ascii=False) + "\n")
            completed += 1
            elapsed = time.time() - t_start
            rate = completed / elapsed if elapsed > 0 else 0
            eta = (len(jobs) - completed) / rate if rate > 0 else float("inf")
            print(f"[{completed}/{len(jobs)}] Q{qnum} {arm:7s} "
                  f"ans={result.get('answer')!r} p={result.get('p_correct')} "
                  f"rc={result.get('returncode')} dt={result.get('duration_s')}s "
                  f"eta={eta/60:.1f}min",
                  file=sys.stderr, flush=True)

    fh.close()
    print(f"[hle_per_question] done in {(time.time()-t_start)/60:.1f} min", file=sys.stderr)


if __name__ == "__main__":
    main()
