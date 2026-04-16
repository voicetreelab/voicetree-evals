from __future__ import annotations

ARM_PROMPTS = {
    "greedy": (
        "You have a very small time budget. Commit after one execution subtask. "
        "Do not iterate beyond a single execution turn unless the protocol forces you to stop cleanly."
    ),
    "exhaustive": (
        "Maximize accuracy. Use the full available budget. Ignore the cost term and keep iterating "
        "until your confidence stops improving or the protocol terminates."
    ),
    "smart": (
        "You pay $T per wall-second and score $A per percent-optimal. "
        "Stop when marginal accuracy gain per second < $T/$A. "
        "The DECISION field is your stop rule."
    ),
}

COMMON_SYSTEM_PROMPT = """You are running a locked budget-metagame protocol on TSP-25.
Follow the exact labeled output contracts.
When a field expects JSON, emit valid JSON.
Turn 1 is planning only: do not solve and do not emit a tour there.
Execution turns must emit BEST_GUESS as a full JSON array tour, even if the baseline remains your best answer.
Do not call tools. Do not write code. Work only from the prompt and your own reasoning.
"""


def build_system_prompt(arm: str) -> str:
    try:
        arm_instruction = ARM_PROMPTS[arm]
    except KeyError as exc:
        raise ValueError(f"unknown arm: {arm}") from exc
    return f"{COMMON_SYSTEM_PROMPT}\nArm instruction: {arm_instruction}"
