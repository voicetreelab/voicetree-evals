from __future__ import annotations


CANONICAL_SYSTEM_PROMPT = """You are running a locked budget-metagame protocol on a two-department scheduling problem.
You earn $A per percentage point below the baseline makespan and pay $T per wall-second.
Stop when your expected marginal improvement is lower than the implied time cost.
Follow the exact labeled output contract on every turn.
Turn 1 is planning only: do not solve the schedule and do not emit a job sequence there.
Execution turns must emit BEST_GUESS as a full permutation of the job numbers.
Do not call tools.
Do not write Python, pseudocode, or solver sketches.
Work only from the prompt and your own scheduling reasoning.
When a field expects JSON, emit valid JSON.
"""


def build_system_prompt() -> str:
    return CANONICAL_SYSTEM_PROMPT
