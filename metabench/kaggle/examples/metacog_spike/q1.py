"""
MetaCoach pilot Q1 — Borderline computation task (3×3 grid independent sets).

QUESTION (originally authored):
A 3×3 grid has each cell independently and uniformly coloured red or blue
with probability 1/2. What is the probability that no two cells sharing an
edge are both red?

  A) 63/512
  B) 1/8
  C) 7/64
  D) 9/64

GOLD DERIVATION (verified by hand):
Count independent sets in the 3×3 grid graph via row-by-row dynamic programming.

Step 1 — valid single-row patterns (no two horizontally adjacent cells both red).
3 cells per row, encode as 3-bit integer (bit 0 = leftmost):
  000=0, 001=1, 010=2, 100=4, 101=5  →  5 valid patterns (011,110,111 excluded)

Step 2 — row-transition rule: two consecutive rows are compatible iff their
bitwise AND is 0 (no column is red in both rows simultaneously).
Successor sets:
  0 → {0,1,2,4,5}   (5)
  1 → {0,2,4}        (3)   [101 conflicts: 1&5=1]
  2 → {0,1,4,5}      (4)   [010 conflicts: 2&2=2]
  4 → {0,1,2}        (3)   [101 conflicts: 4&5=4]
  5 → {0,2}          (2)   [001,100,101 all conflict]

Step 3 — f(s) = |successors(s)| (row-3 choices given row-2 = s):
  f(0)=5, f(1)=3, f(2)=4, f(4)=3, f(5)=2

Step 4 — g(r1) = Σ f(s) for s in successors(r1) (total valid (row2,row3) pairs per row1):
  g(0) = 5+3+4+3+2 = 17
  g(1) = 5+4+3     = 12
  g(2) = 5+3+3+2   = 13
  g(4) = 5+3+4     = 12
  g(5) = 5+4       = 9

Step 5 — total independent sets = Σ g(r1) = 17+12+13+12+9 = 63
Step 6 — total colorings = 2^9 = 512
Step 7 — P = 63/512

ANSWER: A (63/512)

Borderline check: 63/512 ≈ 12.3%.  A vanilla model that recognises the
independent-set structure will likely answer correctly; one that guesses
combinatorially will not.  Expected vanilla accuracy: 30–60%.

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
    "A 3×3 grid has each cell independently and uniformly coloured red or blue "
    "with probability 1/2. What is the probability that no two cells sharing an "
    "edge are both red?\n\n"
    "A) 63/512\n"
    "B) 1/8\n"
    "C) 7/64\n"
    "D) 9/64"
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
    "Subject: Combinatorics / Probability\n\n"
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
    "Subject: Combinatorics / Probability\n\n"
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


GOLD_ANSWER = "A"  # 63/512


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@kbench.task(
    name="metacoach_pilot_q1_grid_independence",
    description=(
        "MetaCoach pilot Q1: probability no two edge-adjacent cells in a 3×3 grid are "
        "both red (gold: A = 63/512, verified by DP). Runs vanilla + metacoach arms in "
        "one shared kernel session (spike; isolation-contract violation noted)."
    ),
)
def metacoach_pilot_q1_grid_independence(llm) -> bool:
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
        f"GOLD={GOLD_ANSWER} (63/512) | "
        f"vanilla_answer={vanilla_answer!r} vanilla_correct={vanilla_correct} vanilla_p={vanilla_p} | "
        f"metacoach_answer={metacoach_answer!r} metacoach_correct={metacoach_correct} metacoach_p={metacoach_p} | "
        f"redirected={redirected} | "
        "ISOLATION NOTE: two arms share one kernel session (Option A spike — "
        "per-arm fresh-session isolation violated; acceptable for toolchain validation only)."
    )

    kbench.assertions.assert_true(
        metacoach_correct,
        expectation=expectation,
    )
    return metacoach_correct
