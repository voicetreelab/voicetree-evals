#!/usr/bin/env python3
"""Generate 24 task files for the HCH HLE-12 spike.

Creates:
  examples/hch_hle12/q{NN}_hch.py     — HCH v2 arm
  examples/hch_hle12/q{NN}_vanilla.py — Vanilla one-shot arm

Run from the kaggle/ directory:
  cd ~/repos/voicetree-evals/metabench/kaggle
  python scripts/gen_hch_hle12_tasks.py
"""

import json
import sys
from pathlib import Path

HLE_USER_PATH = Path(
    "/Users/bobbobby/Library/Containers/com.softwareambience.Unclutter"
    "/Data/Library/Application Support/Unclutter/FileStorage/hle_full.json"
)

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "examples" / "hch_hle12"

# (qnum, gold_answer)
QUESTIONS = [
    (41,  "46.24"),
    (43,  "C"),
    (44,  "flag{no_zeros}"),
    (48,  "5429515560378"),
    (49,  "D"),
    (52,  "A"),
    (53,  "0"),
    (55,  "TC\u2070"),   # TC⁰
    (57,  "C"),
    (65,  "D"),
    (68,  "B"),
    (99,  "dodecagon"),
]

# HCH v2 prompt body — verbatim from task spec (em-dashes via \u2014)
HCH_PROMPT_BODY = (
    "Solve the following question.\n\n"
    "STEP 0 \u2014 ATOMIC BASELINE PREDICTION. "
    "Before deciding whether to decompose, predict what would happen if you just answered "
    "this question directly with no decomposition. Emit:\n"
    "  ATOMIC_PREDICTION: {\"words_if_atomic\": <int>, \"p_correct_if_atomic\": <float>}\n\n"
    "STEP 1 \u2014 PLAN. Now decide whether to decompose. "
    "If atomic is best, emit one subtask. "
    "If decomposition will help (higher p_correct, fewer total words, or both), "
    "break it up however you see fit. For each subtask, emit:\n"
    "  {\"id\": <n>, \"desc\": \"...\", \"p_solve\": <float>, \"words_to_produce_solution\": <int>}\n"
    "Emit all subtasks as a single JSON array under the heading `SUBTASKS:`.\n\n"
    "STEP 2 \u2014 EXECUTE. For each subtask, wrap your work in markers:\n"
    "  === SUB <id> START ===\n"
    "  <your work>\n"
    "  === SUB <id> END === {\"correctly_solved\": true|false, \"confidence\": <float>}\n\n"
    "STEP 3 \u2014 INTEGRATE. Produce the final answer.\n"
    "The FINAL line of your response MUST be exactly:\n"
    "  ANSWER: <your answer>\n"
    "  P_CORRECT: <float between 0 and 1>\n"
    "Do NOT use LaTeX, \\boxed{}, or markdown for these two lines \u2014 plain text only."
)

VANILLA_PROMPT_BODY = (
    "Solve the following question. Output exactly:\n"
    "  ANSWER: <answer>\n"
    "  P_CORRECT: <float>"
)

# Shared parsing + comparison code that gets embedded verbatim in every task file.
# Written as actual Python source — all backslashes here are literal source chars.
SHARED_CODE = r"""
import json as _json
import re as _re

_ATOMIC_RE = _re.compile(r'ATOMIC_PREDICTION:\s*(\{[^}]*\})', _re.DOTALL)
_ANSWER_RE = _re.compile(
    r'^\s*\**\s*ANSWER\**\s*:\s*(.+?)\s*\**\s*$', _re.MULTILINE
)
_PC_RE = _re.compile(
    r'^\s*\**\s*P_CORRECT\**\s*:\s*\**\s*([0-9]*\.?[0-9]+)\s*\**\s*$',
    _re.MULTILINE,
)
_SUBTASKS_RE = _re.compile(
    r'SUBTASKS:\s*(?:```(?:json)?\s*)?(\[.*?\])(?:\s*```)?',
    _re.DOTALL,
)
_SUB_START_RE = _re.compile(r'=== SUB\s+(\d+)\s+START ===')
_SUB_END_RE = _re.compile(r'=== SUB\s+(\d+)\s+END ===\s*(\{[^}]*\})?')


def _parse_json_object_loose(s):
    s = s.strip()
    try:
        return _json.loads(s)
    except Exception:
        pass
    depth, start = 0, None
    for i, ch in enumerate(s):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return _json.loads(s[start:i + 1])
                except Exception:
                    return None
    return None


def _parse_json_array_loose(s):
    s = s.strip()
    try:
        return _json.loads(s)
    except Exception:
        pass
    depth, start = 0, None
    for i, ch in enumerate(s):
        if ch == '[':
            if depth == 0:
                start = i
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return _json.loads(s[start:i + 1])
                except Exception:
                    return None
    return None


def _parse_hch_trajectory(text):
    # Parse full HCH v2 response: atomic prediction, subtasks, sub execs, answer.
    am = _ATOMIC_RE.search(text)
    atomic = _parse_json_object_loose(am.group(1)) if am else None

    subtasks = None
    sm = _SUBTASKS_RE.search(text)
    if sm:
        subtasks = _parse_json_array_loose(sm.group(1))

    starts = {int(m.group(1)): m.end() for m in _SUB_START_RE.finditer(text)}
    ends = {}
    for m in _SUB_END_RE.finditer(text):
        ends[int(m.group(1))] = (m.start(), m.group(2))
    sub_execs = []
    for sid in sorted(starts):
        if sid not in ends:
            sub_execs.append({'id': sid, 'missing_end': True})
            continue
        work_end, status_blob = ends[sid]
        actual_words = len(text[starts[sid]:work_end].split())
        correctly_solved, conf = None, None
        if status_blob:
            try:
                blob = _json.loads(status_blob)
                correctly_solved = blob.get('correctly_solved')
                conf = blob.get('confidence')
            except Exception:
                pass
        sub_execs.append({
            'id': sid,
            'correctly_solved': correctly_solved,
            'confidence': conf,
            'actual_words': actual_words,
        })

    answers = _ANSWER_RE.findall(text)
    pcs = _PC_RE.findall(text)
    answer = answers[-1].strip() if answers else None
    try:
        p_correct = float(pcs[-1]) if pcs else None
    except ValueError:
        p_correct = None

    return {
        'atomic': atomic,
        'subtasks': subtasks,
        'sub_executions': sub_execs,
        'answer': answer,
        'p_correct': p_correct,
    }


def _parse_vanilla(text):
    # Parse vanilla one-shot response: answer, p_correct, word_count.
    answers = _ANSWER_RE.findall(text)
    pcs = _PC_RE.findall(text)
    answer = answers[-1].strip() if answers else None
    try:
        p_correct = float(pcs[-1]) if pcs else None
    except ValueError:
        p_correct = None
    return {'answer': answer, 'p_correct': p_correct, 'word_count': len(text.split())}


def _compare_answer(got, gold, qnum):
    # Gold comparison with per-question tolerance rules.
    if got is None:
        return False
    got = got.strip().strip('.').strip()
    # Float ±0.01 (Q41)
    try:
        if abs(float(got) - float(gold)) <= 0.01:
            return True
    except Exception:
        pass
    # TC\u2070 variants (Q55): accept TC^0, TC0, TC\u2070
    def _tc_norm(s):
        return s.replace('\u2070', '0').replace('^0', '0').upper()
    if _tc_norm(got) == _tc_norm(gold):
        return True
    # Dodecagon (Q99): accept with or without "A " prefix
    if 'dodecagon' in gold.lower() and 'dodecagon' in got.lower():
        return True
    # Default: case-insensitive strip
    return got.strip().lower() == gold.strip().lower()


def _judge_answer(llm, gold, full_response):
    # LLM-as-judge: determine if the model's full response correctly states the gold answer.
    # Returns (judge_pass: bool, judge_raw: str).
    # Uses the same llm object as the task (same proxy, same model).
    judge_prompt = (
        f'Gold answer: "{gold}"\n'
        f'Model response: "{full_response}"\n'
        'Did the model correctly state the gold answer? Reply YES or NO only.'
    )
    try:
        judge_raw = llm.prompt(judge_prompt, max_output_tokens=16)
        judge_pass = judge_raw.strip().upper().startswith("YES")
    except Exception as _e:
        judge_raw = f"JUDGE_ERROR: {_e}"
        judge_pass = False
    return judge_pass, judge_raw
"""


def load_hle_questions(qnums):
    """Load 12 target HLE questions from the user-supplied dataset."""
    if not HLE_USER_PATH.exists():
        raise FileNotFoundError(f"HLE dataset not found: {HLE_USER_PATH}")
    with open(HLE_USER_PATH) as f:
        data = json.load(f)
    items = data.get("data") or data.get("eval_data") or []
    text_only = [q for q in items if not q.get("has_image")]
    print(f"[gen] HLE loaded: {len(text_only)} text-only questions", file=sys.stderr)
    return {n: text_only[n - 1] for n in qnums}


def make_hch_task(qnum, gold, answer_type, raw_subject, question):
    """Build source for one HCH v2 task file."""
    task_name = f"hch_hle12_q{qnum}_hch"
    fn_name = f"hch_hle12_q{qnum}_hch"
    prompt_header = (
        f"Question type: {answer_type}\n"
        f"Subject: {raw_subject}\n\n"
        f"QUESTION:\n{question}\n\n"
    )
    full_prompt = prompt_header + HCH_PROMPT_BODY

    # Escape curly braces in gold repr so it embeds safely into generated f-strings.
    gold_esc = repr(gold).replace('{', '{{').replace('}', '}}')

    src = (
        f'"""HCH HLE-12 spike \u2014 Q{qnum} \u2014 HCH v2 arm.\n\n'
        f'Subject: {raw_subject}\n'
        f'Answer type: {answer_type}\n'
        f'Gold: {gold!r}\n'
        f'"""\n\n'
        f'import kaggle_benchmarks as kbench\n\n'
        f'QNUM = {qnum}\n'
        f'GOLD_ANSWER = {gold!r}\n'
        f'PROMPT = {full_prompt!r}\n'
        + SHARED_CODE +
        f'\n\n@kbench.task(\n'
        f'    name={task_name!r},\n'
        f'    description=(\n'
        f'        "HCH HLE-12 Q{qnum} ({raw_subject}): HCH v2 arm. "\n'
        f'        "Scores A1,A2,A3,B,C,D metacog axes. "\n'
        f'        "Gold={gold!r}."\n'
        f'    ),\n'
        f')\n'
        f'def {fn_name}(llm) -> bool:\n'
        f'    raw = llm.prompt(PROMPT, max_output_tokens=32768)\n'
        f'    traj = _parse_hch_trajectory(raw)\n'
        f'    official_pass = _compare_answer(traj["answer"], GOLD_ANSWER, QNUM)\n'
        f'    judge_pass, judge_raw = _judge_answer(llm, GOLD_ANSWER, raw)\n'
        f'    correct = judge_pass  # primary correctness signal is the judge\n'
        f'\n'
        f'    # Judge vs regex diagnostic\n'
        f'    kbench.assertions.assert_true(\n'
        f'        True,\n'
        f'        expectation=(\n'
        f'            f"JUDGE Q{qnum} HCH: official={{official_pass}}, judge={{judge_pass}}, "\n'
        f'            f"judge_raw={{judge_raw!r}}"\n'
        f'        ),\n'
        f'    )\n'
        f'\n'
        f'    # Axis A0: atomic baseline metadata\n'
        f'    kbench.assertions.assert_true(\n'
        f'        True,\n'
        f'        expectation=(\n'
        f'            f"ATOMIC: words_if_atomic={{traj[\'atomic\'] and traj[\'atomic\'].get(\'words_if_atomic\')}}, "\n'
        f'            f"p_correct_if_atomic={{traj[\'atomic\'] and traj[\'atomic\'].get(\'p_correct_if_atomic\')}}"\n'
        f'        ),\n'
        f'    )\n'
        f'\n'
        f'    # Axis A3: decompose decision\n'
        f'    n_subtasks = len(traj["subtasks"]) if traj["subtasks"] else 0\n'
        f'    kbench.assertions.assert_true(\n'
        f'        True,\n'
        f'        expectation=f"DECOMP: n_subtasks={{n_subtasks}}, chose_decomp={{n_subtasks > 1}}",\n'
        f'    )\n'
        f'\n'
        f'    # Axis B + C: per-subtask plan vs execution\n'
        f'    for sub_plan in (traj["subtasks"] or []):\n'
        f'        sid = sub_plan.get("id")\n'
        f'        exec_info = next(\n'
        f'            (s for s in traj["sub_executions"] if s.get("id") == sid), {{}}\n'
        f'        )\n'
        f'        kbench.assertions.assert_true(\n'
        f'            True,\n'
        f'            expectation=(\n'
        f'                f"SUB_{{sid}}: p_solve={{sub_plan.get(\'p_solve\')}}, "\n'
        f'                f"words_to_produce={{sub_plan.get(\'words_to_produce_solution\')}}, "\n'
        f'                f"correctly_solved={{exec_info.get(\'correctly_solved\')}}, "\n'
        f'                f"confidence={{exec_info.get(\'confidence\')}}, "\n'
        f'                f"actual_words={{exec_info.get(\'actual_words\')}}"\n'
        f'            ),\n'
        f'        )\n'
        f'\n'
        f'    # Axis D: final answer calibration\n'
        f'    kbench.assertions.assert_true(\n'
        f'        correct,\n'
        f'        expectation=(\n'
        f'            f"Axis D Q{qnum} HCH: answer={{traj[\'answer\']!r}}, "\n'
        f'            f"p_correct={{traj[\'p_correct\']}}, "\n'
        f'            f"correct={{correct}}, gold={gold_esc}"\n'
        f'        ),\n'
        f'    )\n'
        f'    return correct\n'
    )
    return src


def make_vanilla_task(qnum, gold, answer_type, raw_subject, question):
    """Build source for one vanilla one-shot task file."""
    task_name = f"hch_hle12_q{qnum}_vanilla"
    fn_name = f"hch_hle12_q{qnum}_vanilla"
    prompt_header = (
        f"Question type: {answer_type}\n"
        f"Subject: {raw_subject}\n\n"
        f"QUESTION:\n{question}\n\n"
    )
    full_prompt = prompt_header + VANILLA_PROMPT_BODY

    # Escape curly braces in gold repr so it embeds safely into generated f-strings.
    gold_esc = repr(gold).replace('{', '{{').replace('}', '}}')

    src = (
        f'"""HCH HLE-12 spike \u2014 Q{qnum} \u2014 Vanilla one-shot arm.\n\n'
        f'Subject: {raw_subject}\n'
        f'Answer type: {answer_type}\n'
        f'Gold: {gold!r}\n'
        f'"""\n\n'
        f'import kaggle_benchmarks as kbench\n\n'
        f'QNUM = {qnum}\n'
        f'GOLD_ANSWER = {gold!r}\n'
        f'PROMPT = {full_prompt!r}\n'
        + SHARED_CODE +
        f'\n\n@kbench.task(\n'
        f'    name={task_name!r},\n'
        f'    description=(\n'
        f'        "HCH HLE-12 Q{qnum} ({raw_subject}): Vanilla one-shot arm. "\n'
        f'        "Gold={gold!r}."\n'
        f'    ),\n'
        f')\n'
        f'def {fn_name}(llm) -> bool:\n'
        f'    raw = llm.prompt(PROMPT, max_output_tokens=32768)\n'
        f'    result = _parse_vanilla(raw)\n'
        f'    official_pass = _compare_answer(result["answer"], GOLD_ANSWER, QNUM)\n'
        f'    judge_pass, judge_raw = _judge_answer(llm, GOLD_ANSWER, raw)\n'
        f'    correct = judge_pass  # primary correctness signal is the judge\n'
        f'    kbench.assertions.assert_true(\n'
        f'        correct,\n'
        f'        expectation=(\n'
        f'            f"Vanilla Q{qnum}: official={{official_pass}}, judge={{judge_pass}}, "\n'
        f'            f"answer={{result[\'answer\']!r}}, p_correct={{result[\'p_correct\']}}, "\n'
        f'            f"gold={gold_esc}, word_count={{result[\'word_count\']}}"\n'
        f'        ),\n'
        f'    )\n'
        f'    return correct\n'
    )
    return src


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    qnums = [q[0] for q in QUESTIONS]
    hle = load_hle_questions(qnums)

    for qnum, gold in QUESTIONS:
        q = hle[qnum]
        answer_type = q.get("answer_type", "exactMatch")
        raw_subject = q.get("raw_subject", "Unknown")
        question = q.get("question", "")

        hch_path = OUTPUT_DIR / f"q{qnum}_hch.py"
        hch_src = make_hch_task(qnum, gold, answer_type, raw_subject, question)
        hch_path.write_text(hch_src, encoding="utf-8")
        print(f"[gen] wrote {hch_path.name}", file=sys.stderr)

        van_path = OUTPUT_DIR / f"q{qnum}_vanilla.py"
        van_src = make_vanilla_task(qnum, gold, answer_type, raw_subject, question)
        van_path.write_text(van_src, encoding="utf-8")
        print(f"[gen] wrote {van_path.name}", file=sys.stderr)

    print(f"[gen] done — {len(QUESTIONS) * 2} files in {OUTPUT_DIR}", file=sys.stderr)


if __name__ == "__main__":
    main()
