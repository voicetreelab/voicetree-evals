#!/usr/bin/env python3
"""
HCH in-context spike: one `claude -p` call per question with self-driven
decomposition (PLAN / EXECUTE / INTEGRATE).

Usage:
  python3 hch_in_context.py \
      --qnums 41 44 52 53 57 \
      --model sonnet \
      --concurrency 5 \
      --timeout 3600 \
      --out datasets/hle/hch_q41_44_52_53_57.jsonl
"""

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
import time
from pathlib import Path

VAULT = Path(__file__).resolve().parents[1]
DATASET = VAULT / "datasets" / "hle" / "hle_prompts_only.json"

# Manu's prompt — verbatim, do not rewrite.
HCH_PROMPT_BODY = """\
Solve the following question.

STEP 1 — PLAN. Decide how to tackle this. If the task is atomic, one subtask is fine; if it benefits from decomposition, break it up however you see fit (any number of subtasks, any structure). For each subtask you commit to, emit a JSON object with at minimum:
  {"id": <n>, "desc": "...", "p_solve": <float>, "token_estimate": <int>}
Emit all subtasks as a single JSON array under the heading `SUBTASKS:`.

STEP 2 — EXECUTE. For each subtask, wrap your work in markers:
  === SUB <id> START ===
  <your work>
  === SUB <id> END === {"solved": true|false, "confidence": <float>}

STEP 3 — INTEGRATE. Produce the final answer.
  ANSWER: <answer>
  P_CORRECT: <float>
"""

PROMPT_TEMPLATE = """\
Question type: {answer_type}
Subject: {raw_subject}

QUESTION:
{question}

{body}"""


def load_questions(qnums):
    with open(DATASET) as f:
        data = json.load(f)
    text_only = [q for q in data["eval_data"] if not q.get("has_image")]
    out = []
    for n in qnums:
        # 1-indexed: Q41 -> text_only[40]
        out.append((n, text_only[n - 1]))
    return out


def build_prompt(q):
    return PROMPT_TEMPLATE.format(
        answer_type=q.get("answer_type", "?"),
        raw_subject=q.get("raw_subject", "?"),
        question=q["question"],
        body=HCH_PROMPT_BODY,
    )


ANSWER_RE = re.compile(
    r"^\s*\**\s*ANSWER\**\s*:\s*(.+?)\s*\**\s*$", re.MULTILINE
)
PC_RE = re.compile(
    r"^\s*\**\s*P_CORRECT\**\s*:\s*\**\s*([0-9]*\.?[0-9]+)\s*\**\s*$",
    re.MULTILINE,
)
SUBTASKS_RE = re.compile(
    r"SUBTASKS:\s*(?:```(?:json)?\s*)?(\[.*?\])(?:\s*```)?",
    re.DOTALL,
)
SUB_START_RE = re.compile(r"=== SUB\s+(\d+)\s+START ===")
# end marker captures id + trailing JSON-ish status block
SUB_END_RE = re.compile(
    r"=== SUB\s+(\d+)\s+END ===\s*(\{[^}]*\})?",
)


def _parse_json_array_loose(s):
    """Try to parse a JSON array, tolerating trailing text."""
    s = s.strip()
    # First try direct
    try:
        return json.loads(s)
    except Exception:
        pass
    # Walk and find balanced []
    depth = 0
    start = None
    for i, ch in enumerate(s):
        if ch == "[":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(s[start:i + 1])
                except Exception:
                    return None
    return None


def parse_subtasks(text):
    m = SUBTASKS_RE.search(text)
    if not m:
        return None
    return _parse_json_array_loose(m.group(1))


def parse_sub_executions(text):
    """Pair START/END markers; compute char count of the work between them
    and parse the trailing status JSON (solved + confidence)."""
    starts = {int(m.group(1)): m.end() for m in SUB_START_RE.finditer(text)}
    ends = {}
    for m in SUB_END_RE.finditer(text):
        sid = int(m.group(1))
        # Position where the work ends (start of "=== SUB N END ===")
        ends[sid] = (m.start(), m.group(2))

    out = []
    for sid in sorted(starts):
        if sid not in ends:
            out.append({
                "id": sid, "solved": None, "confidence": None,
                "actual_chars": None, "missing_end": True,
            })
            continue
        work_start = starts[sid]
        work_end, status_blob = ends[sid]
        actual_chars = max(0, work_end - work_start)
        solved = None
        confidence = None
        if status_blob:
            try:
                blob = json.loads(status_blob)
                solved = blob.get("solved")
                confidence = blob.get("confidence")
            except Exception:
                pass
        out.append({
            "id": sid,
            "solved": solved,
            "confidence": confidence,
            "actual_chars": actual_chars,
        })
    return out


def parse_final(text):
    """Return (answer, p_correct, reasoning). reasoning = everything before
    last ANSWER: line."""
    answers = ANSWER_RE.findall(text)
    pcs = PC_RE.findall(text)
    answer = answers[-1].strip() if answers else None
    try:
        p = float(pcs[-1]) if pcs else None
    except ValueError:
        p = None
    m = list(ANSWER_RE.finditer(text))
    reasoning = text[: m[-1].start()].strip() if m else text.strip()
    return answer, p, reasoning


def parse_claude_json(stdout):
    """Parse `claude -p --output-format json` output.

    Returns dict with keys:
      result_text  — concatenation of ALL assistant text turns (so
                     SUBTASKS / SUB markers from earlier turns are included).
      final_text   — just the last assistant message's `result` field.
      usage        — usage dict (input_tokens, output_tokens, cache_*)
      total_cost   — total_cost_usd (float, may be None)
      raw          — full parsed JSON (None if parse failed)
    """
    try:
        parsed = json.loads(stdout)
    except Exception:
        return {"result_text": stdout, "final_text": stdout,
                "usage": None, "total_cost": None, "raw": None}

    events = parsed if isinstance(parsed, list) else [parsed]
    assistant_text_chunks = []
    seen_text_hashes = set()
    result_event = None
    for ev in events:
        if not isinstance(ev, dict):
            continue
        if ev.get("type") == "result":
            result_event = ev
            continue
        if ev.get("type") == "assistant":
            msg = ev.get("message") or {}
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "text":
                    txt = block.get("text", "")
                    h = hash(txt)
                    if h in seen_text_hashes:
                        continue
                    seen_text_hashes.add(h)
                    assistant_text_chunks.append(txt)

    full_text = "\n".join(assistant_text_chunks)
    final_text = (result_event or {}).get("result", "") if result_event else ""

    return {
        "result_text": full_text or final_text or stdout,
        "final_text": final_text,
        "usage": (result_event or {}).get("usage"),
        "total_cost": (result_event or {}).get("total_cost_usd"),
        "raw": parsed,
    }


def run_one(qnum, q, model, timeout, dry_run):
    prompt = build_prompt(q)
    if dry_run:
        return {
            "qnum": qnum, "qid": q["id"], "answer": None,
            "p_correct": None, "dry_run": True,
            "prompt_len": len(prompt),
        }

    cmd = [
        "claude",
        "--model", model,
        "--dangerously-skip-permissions",
        "--output-format", "json",
        "-p", prompt,
    ]
    t0 = time.time()
    err = None
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        rc = proc.returncode
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout.decode("utf-8", "replace")
                  if isinstance(e.stdout, bytes) else (e.stdout or ""))
        stderr = (e.stderr.decode("utf-8", "replace")
                  if isinstance(e.stderr, bytes) else (e.stderr or ""))
        rc = -1
        err = f"timeout after {timeout}s"
    dt = time.time() - t0

    parsed = parse_claude_json(stdout)
    text = parsed["result_text"] or stdout
    answer, p_correct, reasoning = parse_final(text)
    subtasks = parse_subtasks(text)
    sub_execs = parse_sub_executions(text)

    usage = parsed.get("usage") or {}
    total_tokens = None
    if isinstance(usage, dict):
        total_tokens = (
            (usage.get("input_tokens") or 0)
            + (usage.get("output_tokens") or 0)
            + (usage.get("cache_creation_input_tokens") or 0)
            + (usage.get("cache_read_input_tokens") or 0)
        ) or None

    return {
        "qnum": qnum,
        "qid": q["id"],
        "answer_type": q.get("answer_type"),
        "raw_subject": q.get("raw_subject"),
        "answer": answer,
        "p_correct": p_correct,
        "reasoning": reasoning,
        "subtasks": subtasks,
        "sub_executions": sub_execs,
        "total_tokens": total_tokens,
        "total_cost": parsed.get("total_cost"),
        "usage": usage if isinstance(usage, dict) else None,
        "duration_s": round(dt, 2),
        "returncode": rc,
        "error": err,
        "stdout": stdout,
        "stderr_tail": stderr[-2000:] if stderr else "",
    }


def load_done(path):
    done = set()
    if path.exists():
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    done.add(json.loads(line)["qnum"])
                except Exception:
                    pass
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qnums", nargs="+", type=int, required=True)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    questions = load_questions(args.qnums)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    done = load_done(args.out)

    jobs = [(qn, q) for qn, q in questions if qn not in done]
    print(f"[hch] {len(jobs)} jobs to run ({len(done)} already done), "
          f"concurrency={args.concurrency}, model={args.model}, "
          f"timeout={args.timeout}s, out={args.out}",
          file=sys.stderr)
    if not jobs:
        return

    fh = open(args.out, "a", buffering=1)
    completed = 0
    t_start = time.time()

    def _task(job):
        qn, q = job
        return run_one(qn, q, args.model, args.timeout, args.dry_run)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(_task, j): j for j in jobs}
        for fut in concurrent.futures.as_completed(futs):
            qn, q = futs[fut]
            try:
                result = fut.result()
            except Exception as e:
                result = {
                    "qnum": qn, "qid": q["id"],
                    "answer": None, "p_correct": None,
                    "error": f"exception: {e!r}", "returncode": -2,
                }
            fh.write(json.dumps(result, ensure_ascii=False) + "\n")
            completed += 1
            elapsed = time.time() - t_start
            print(f"[{completed}/{len(jobs)}] Q{qn} "
                  f"ans={result.get('answer')!r} "
                  f"p={result.get('p_correct')} "
                  f"subs={len(result.get('subtasks') or [])} "
                  f"tok={result.get('total_tokens')} "
                  f"rc={result.get('returncode')} "
                  f"dt={result.get('duration_s')}s",
                  file=sys.stderr, flush=True)

    fh.close()
    print(f"[hch] done in {(time.time()-t_start)/60:.1f} min",
          file=sys.stderr)


if __name__ == "__main__":
    main()
