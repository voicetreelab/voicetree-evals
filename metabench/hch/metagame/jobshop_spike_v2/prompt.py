from __future__ import annotations


CANONICAL_SYSTEM_PROMPT = """You are running a locked budget-metagame protocol on a natural-language multi-machine job-shop scheduling problem.
You earn $A per percentage point below the baseline makespan and pay $T per wall-second.
Stop when your expected marginal improvement is lower than the implied time cost.
Follow the exact labeled output contract on every turn.
Turn 1 is planning only: do not solve the schedule and do not emit BEST_GUESS there.
Execution turns must emit BEST_GUESS as valid JSON with exactly the station keys named in the prompt.
Do not call tools.
Do not write Python, pseudocode, or solver templates.
Work only from the prompt and your own reasoning.
"""


def build_system_prompt() -> str:
    return CANONICAL_SYSTEM_PROMPT
