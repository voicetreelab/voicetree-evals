"""HCH spike Q2 — Vieta's cubic + expression evaluation.

Exercises the Factored Self-Assessment protocol on a question that
GENUINELY benefits from 2-3 subtasks, giving Axis A (decomposition
quality) non-trivial signal. A monolithic solve must track: (1) recognize
Vieta's structure and build the cubic, (2) factor it, (3) evaluate the
target expression. That natural 3-part structure encourages decomposition
and lets us observe whether the model's plan aligns with optimal chunking.

Gold answer derivation (author-verified):
  a+b+c=30, ab+bc+ca=281, abc=780, a<b<c
  → cubic: x^3 - 30x^2 + 281x - 780 = 0
  → test x=5: 125 - 750 + 1405 - 780 = 0  ✓
  → divide out (x-5): x^2 - 25x + 156 = 0
  → discriminant: 625 - 624 = 1
  → roots: (25 ± 1)/2 → x=12 and x=13
  → so (a, b, c) = (5, 12, 13)
  → a + b^2 + c^3 = 5 + 144 + 2197 = 2346
"""

import json
import re

import kaggle_benchmarks as kbench


# Verbatim from hch/scripts/hch_in_context.py — do not rewrite.
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
    "Positive integers a, b, c satisfy: a + b + c = 30, "
    "ab + bc + ca = 281, abc = 780, and a < b < c. "
    "Compute a + b^2 + c^3. Return only an integer."
)

GOLD_ANSWER = "2346"
# Derivation: The three integers are roots of x^3 - 30x^2 + 281x - 780 = 0.
# x=5: 125-750+1405-780=0. Factor: (x-5)(x^2-25x+156)=0.
# x^2-25x+156=0 → disc=625-624=1 → x=12 or x=13.
# So (a,b,c)=(5,12,13). a+b^2+c^3 = 5+144+2197 = 2346.

PROMPT = f"""\
Question type: exactMatch
Subject: mathematics

QUESTION:
{QUESTION}

{HCH_PROMPT_BODY}"""


# Parsing regexes — verbatim from hch/scripts/hch_in_context.py.
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
    name="hch_spike_q2_vieta_expression",
    description=(
        "HCH protocol spike: single-call PLAN/EXECUTE/INTEGRATE on a Vieta's "
        "formulas + expression evaluation problem. The 3-phase structure "
        "(form cubic → factor → evaluate) naturally rewards decomposition, "
        "giving Axis A (decomposition quality) real signal. Scores Axis D "
        "(final answer correctness); emits per-subtask plan and self-reports "
        "as judge notes for Axis B/C inspection."
    ),
)
def hch_spike_q2(llm) -> bool:
    raw = llm.prompt(PROMPT)
    traj = parse_trajectory(raw)
    predicted = _normalize(traj["answer"])
    correct = predicted == GOLD_ANSWER

    subtask_count = len(traj["subtasks"]) if traj["subtasks"] else 0
    self_solved = sum(
        1 for s in traj["sub_executions"] if s.get("solved") is True
    )

    # Axis A signal: optimal decomposition is 2-3 subtasks. Emit as judge note.
    decomp_note = (
        f"Axis A: model chose {subtask_count} subtask(s); "
        "optimal is 2-3 (form cubic, factor, evaluate). "
        f"over_decomposed={'yes' if subtask_count > 3 else 'no'}, "
        f"under_decomposed={'yes' if subtask_count <= 1 else 'no'}."
    )
    kbench.assertions.assert_true(True, expectation=decomp_note)

    # Axis B/C signals: per-sub p_solve predictions vs self-reported solved.
    for sub_plan in (traj["subtasks"] or []):
        sid = sub_plan.get("id")
        exec_info = next(
            (s for s in traj["sub_executions"] if s.get("id") == sid), {}
        )
        note = (
            f"Axis B/C sub {sid}: "
            f"predicted p_solve={sub_plan.get('p_solve')}, "
            f"token_estimate={sub_plan.get('token_estimate')}, "
            f"self_reported_solved={exec_info.get('solved')}, "
            f"self_confidence={exec_info.get('confidence')}, "
            f"actual_chars={exec_info.get('chars')}."
        )
        kbench.assertions.assert_true(True, expectation=note)

    # Axis D: final answer correctness.
    kbench.assertions.assert_true(
        correct,
        expectation=(
            f"Axis D: final ANSWER must equal {GOLD_ANSWER!r} (a+b^2+c^3 "
            f"where a=5, b=12, c=13); got {predicted!r}. "
            f"subtasks_planned={subtask_count}, "
            f"self_solved={self_solved}/{len(traj['sub_executions'])}, "
            f"p_correct={traj['p_correct']}."
        ),
    )
    return correct
