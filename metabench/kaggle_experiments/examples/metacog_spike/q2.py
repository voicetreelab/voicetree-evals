"""
MetaCoach pilot Q2 — Axis-3 ambiguity task (last digit of filtered sum).

QUESTION (originally authored):
What is the last digit of the sum of all integers from 1 to 100 that are
not divisible by either 3 or 7?

  A) 0
  B) 2
  C) 4
  D) 8

GOLD DERIVATION (verified by hand):
"not divisible by either 3 or 7" = not divisible by 3 AND not divisible by 7.

  Sum(1..100) = 100 × 101 / 2 = 5050

  Multiples of 3 up to 100: 3, 6, …, 99 → 33 terms
    Sum = 3 × (33 × 34 / 2) = 3 × 561 = 1683

  Multiples of 7 up to 100: 7, 14, …, 98 → 14 terms
    Sum = 7 × (14 × 15 / 2) = 7 × 105 = 735

  Multiples of 21 up to 100: 21, 42, 63, 84 → 4 terms
    Sum = 21 + 42 + 63 + 84 = 210

  Inclusion-exclusion — sum divisible by 3 or 7:
    1683 + 735 − 210 = 2208

  Target sum (not divisible by 3 or 7):
    5050 − 2208 = 2842  →  last digit = 2

ANSWER: B (last digit = 2)

AXIS-3 AMBIGUITY SOURCE:
A plausible alternative reading of "not divisible by either 3 or 7" is
"not divisible by both simultaneously", i.e. not divisible by lcm(3,7)=21.
  Sum not divisible by 21: 5050 − 210 = 4840  →  last digit = 0  →  Answer A.
A metacoach arm that catches this ambiguity and resolves it correctly is
demonstrating Axis-3 (answer-redirection driven by ambiguity resolution),
not merely confidence modulation.

ISOLATION CONTRACT NOTE:
Both arms run in one shared kernel session (Option A spike).  Fresh-session
isolation (one session per arm per question) is violated.  Flagged here and
in the pilot note — acceptable for toolchain validation, not for production runs.
"""

import re

import kaggle_benchmarks as kbench

# ---------------------------------------------------------------------------
# Question text
# ---------------------------------------------------------------------------

QUESTION_TEXT = (
    "What is the last digit of the sum of all integers from 1 to 100 that are "
    "not divisible by either 3 or 7?\n\n"
    "A) 0\n"
    "B) 2\n"
    "C) 4\n"
    "D) 8"
)

FORMAT_BLOCK = (
    "OUTPUT FORMAT — strict. Your response must END with exactly two lines:\n"
    "ANSWER: <your answer>\n"
    "P_CORRECT: <float in [0,1]>\n\n"
    "If the question is multipleChoice, ANSWER is a single capital letter."
)

# ---------------------------------------------------------------------------
# Vanilla arm prompt
# ---------------------------------------------------------------------------

VANILLA_PROMPT = (
    "Solve the following question directly. Show whatever reasoning you need, "
    "then emit your final answer.\n\n"
    "Question type: multipleChoice\n"
    "Subject: Number Theory / Arithmetic\n\n"
    "QUESTION:\n"
    f"{QUESTION_TEXT}\n\n"
    f"{FORMAT_BLOCK}"
)

# ---------------------------------------------------------------------------
# MetaCoach arm prompt  — coaching prefix is VERBATIM from spec.md §Arm 2
# ---------------------------------------------------------------------------

METACOACH_INSTRUCTION = """\
Address the following metacognitive reflection prompt at BOTH the start
and the end of this task:

"Go through at least 2-3 levels on your reasoning towards the task/prompt
you are assigned. At each level, reflect on the cognitive patterns of the
level below — not the content, the thinking, the cognitive patterns. For
example in level 1, identify what cognitive pattern you are using to solve
this problem. In level 2, identify what meta-pattern you used to notice &
identify that, biases/uncertainties, etc. Finally, after going to 2-3
meta-levels recursively, circle back to the task — has this reflection
actually improved my confidence in how to solve this problem & whether
it is correct? Provide a prediction probability claim for that question."

Do this reflection BEFORE attempting the question, then solve the question,
then do the reflection AGAIN after your candidate answer, and let your final
P_CORRECT incorporate both passes."""

METACOACH_PROMPT = (
    "You are solving the following question.\n\n"
    f"{METACOACH_INSTRUCTION}\n\n"
    "Question type: multipleChoice\n"
    "Subject: Number Theory / Arithmetic\n\n"
    "QUESTION:\n"
    f"{QUESTION_TEXT}\n\n"
    f"{FORMAT_BLOCK}"
)

# ---------------------------------------------------------------------------
# Parsing helpers (reused from hle_per_question.py pattern)
# ---------------------------------------------------------------------------

ANSWER_RE = re.compile(r"^\s*ANSWER:\s*(.+?)\s*$", re.MULTILINE)
PC_RE = re.compile(r"^\s*P_CORRECT:\s*([0-9]*\.?[0-9]+)\s*$", re.MULTILINE)


def _parse(text: str):
    answers = ANSWER_RE.findall(text)
    pcs = PC_RE.findall(text)
    answer = answers[-1].strip().upper() if answers else None
    try:
        p_correct = float(pcs[-1]) if pcs else None
    except ValueError:
        p_correct = None
    return answer, p_correct


GOLD_ANSWER = "B"  # last digit = 2


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@kbench.task(
    name="metacoach_pilot_q2_last_digit_sum",
    description=(
        "MetaCoach pilot Q2: last digit of sum of 1..100 not divisible by 3 or 7 "
        "(gold: B=2, verified by inclusion-exclusion). Axis-3 ambiguity source: "
        "'not divisible by either' vs 'not divisible by both' gives B=2 vs A=0. "
        "Runs vanilla + metacoach arms in one shared kernel session (spike)."
    ),
)
def metacoach_pilot_q2_last_digit_sum(llm) -> bool:
    # Arm 1 — Vanilla
    vanilla_raw = llm.prompt(VANILLA_PROMPT)
    vanilla_answer, vanilla_p = _parse(vanilla_raw)

    # Arm 2 — MetaCoach
    metacoach_raw = llm.prompt(METACOACH_PROMPT)
    metacoach_answer, metacoach_p = _parse(metacoach_raw)

    vanilla_correct = vanilla_answer == GOLD_ANSWER
    metacoach_correct = metacoach_answer == GOLD_ANSWER
    redirected = vanilla_answer != metacoach_answer

    expectation = (
        f"GOLD={GOLD_ANSWER} (last digit=2, sum=2842) | "
        f"vanilla_answer={vanilla_answer!r} vanilla_correct={vanilla_correct} vanilla_p={vanilla_p} | "
        f"metacoach_answer={metacoach_answer!r} metacoach_correct={metacoach_correct} metacoach_p={metacoach_p} | "
        f"redirected={redirected} | "
        "AMBIGUITY: 'not divisible by either 3 or 7' → correct reading: not-by-3 AND not-by-7 → "
        "sum=2842 → last digit 2=B; misreading: not-by-21 → sum=4840 → last digit 0=A | "
        "ISOLATION NOTE: two arms share one kernel session (Option A spike — "
        "per-arm fresh-session isolation violated; acceptable for toolchain validation only)."
    )

    kbench.assertions.assert_true(
        metacoach_correct,
        expectation=expectation,
    )
    return metacoach_correct
