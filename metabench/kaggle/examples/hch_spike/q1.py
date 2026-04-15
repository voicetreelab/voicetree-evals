"""HCH spike Q1 — arithmetic sum + modulo.

Exercises the Factored Self-Assessment protocol in a single kbench task:
the model is prompted to PLAN / EXECUTE / INTEGRATE in one call. We parse
the SUBTASKS JSON, the SUB N START/END blocks, the final ANSWER, and the
final P_CORRECT. The assertion is on end-to-end correctness; the richer
metacog signals (per-sub p_solve, token_estimate, self-reported solved)
are emitted as judge notes so the pilot captures Axes B / C / D shape
even though the spike only strictly scores Axis D.
"""

import json
import re

import kaggle_benchmarks as kbench


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

QUESTION = (
    "Let a_n = n^2 + 3n for positive integers n. Let S be the sum of a_n "
    "for n from 1 to 10 inclusive. Find the remainder when S is divided "
    "by 17. Return only an integer in [0, 16]."
)

GOLD_ANSWER = "6"
# Derivation: sum n^2 (1..10) = 385, sum 3n (1..10) = 165, S = 550.
# 550 = 17 * 32 + 6, so remainder = 6.

PROMPT = f"""\
Question type: exactMatch
Subject: mathematics

QUESTION:
{QUESTION}

{HCH_PROMPT_BODY}"""


ANSWER_RE = re.compile(r"^\s*\**\s*ANSWER\**\s*:\s*(.+?)\s*\**\s*$", re.MULTILINE)
PC_RE = re.compile(
    r"^\s*\**\s*P_CORRECT\**\s*:\s*\**\s*([0-9]*\.?[0-9]+)\s*\**\s*$",
    re.MULTILINE,
)
SUBTASKS_RE = re.compile(
    r"SUBTASKS:\s*(?:```(?:json)?\s*)?(\[.*?\])(?:\s*```)?",
    re.DOTALL,
)
SUB_START_RE = re.compile(r"=== SUB\s+(\d+)\s+START ===")
SUB_END_RE = re.compile(r"=== SUB\s+(\d+)\s+END ===\s*(\{[^}]*\})?")


def _parse_json_array_loose(s: str):
    s = s.strip()
    try:
        return json.loads(s)
    except Exception:
        pass
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
                    return json.loads(s[start : i + 1])
                except Exception:
                    return None
    return None


def parse_trajectory(text: str) -> dict:
    subtasks = None
    m = SUBTASKS_RE.search(text)
    if m:
        subtasks = _parse_json_array_loose(m.group(1))

    starts = {int(m.group(1)): m.end() for m in SUB_START_RE.finditer(text)}
    ends = {}
    for m in SUB_END_RE.finditer(text):
        ends[int(m.group(1))] = (m.start(), m.group(2))
    sub_execs = []
    for sid in sorted(starts):
        if sid not in ends:
            sub_execs.append({"id": sid, "missing_end": True})
            continue
        work_end, status_blob = ends[sid]
        chars = max(0, work_end - starts[sid])
        solved, conf = None, None
        if status_blob:
            try:
                blob = json.loads(status_blob)
                solved = blob.get("solved")
                conf = blob.get("confidence")
            except Exception:
                pass
        sub_execs.append(
            {"id": sid, "solved": solved, "confidence": conf, "chars": chars}
        )

    answers = ANSWER_RE.findall(text)
    pcs = PC_RE.findall(text)
    answer = answers[-1].strip() if answers else None
    try:
        p_correct = float(pcs[-1]) if pcs else None
    except ValueError:
        p_correct = None

    return {
        "subtasks": subtasks,
        "sub_executions": sub_execs,
        "answer": answer,
        "p_correct": p_correct,
    }


def _normalize(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().strip(".").strip()


@kbench.task(
    name="hch_spike_q1_arith_mod17",
    description=(
        "HCH protocol spike: single-call PLAN/EXECUTE/INTEGRATE on a "
        "decomposable arithmetic + modulo question. Scores end-to-end "
        "correctness (Axis D); emits subtask plan and self-reports as "
        "judge notes for Axis B/C inspection."
    ),
)
def hch_spike_q1(llm) -> bool:
    raw = llm.prompt(PROMPT)
    traj = parse_trajectory(raw)
    predicted = _normalize(traj["answer"])
    correct = predicted == GOLD_ANSWER

    subtask_count = len(traj["subtasks"]) if traj["subtasks"] else 0
    self_solved = sum(
        1 for s in traj["sub_executions"] if s.get("solved") is True
    )

    kbench.assertions.assert_true(
        correct,
        expectation=(
            f"Final ANSWER must equal {GOLD_ANSWER!r}; "
            f"got {predicted!r}. subtasks_planned={subtask_count}, "
            f"self_solved={self_solved}/{len(traj['sub_executions'])}, "
            f"p_correct={traj['p_correct']}."
        ),
    )
    return correct
