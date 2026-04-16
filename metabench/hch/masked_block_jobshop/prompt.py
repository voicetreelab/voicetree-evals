from __future__ import annotations


CANONICAL_SYSTEM_PROMPT = """You are running a locked budget-metagame protocol on a coupled two-factory job-shop scheduling problem.
You earn score for reducing makespan gap and lose score for wall-clock time.
Turn 1 is planning only: do not emit a schedule there.
Execution turns must emit BEST_GUESS as valid JSON with machine timelines for both factories.
When forecasting quality, do not give a probability of exact correctness. Give calibrated probabilities for thresholded gap-to-optimal events.
When forecasting continuation, estimate whether exactly one more subtask is worth its time cost relative to stopping now.
Do not call tools.
Do not write Python, pseudocode, or solver sketches.
Work only from the prompt, the current best schedule, and your own scheduling reasoning.
When a field expects JSON, emit valid JSON.
"""


def build_system_prompt() -> str:
    return CANONICAL_SYSTEM_PROMPT
