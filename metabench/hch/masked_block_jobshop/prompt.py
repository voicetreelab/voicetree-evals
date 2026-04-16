from __future__ import annotations


CANONICAL_SYSTEM_PROMPT = """You are running a locked budget-metagame protocol on a masked job-shop scheduling problem.
You earn score for reducing total objective gap and lose score for wall-clock time.
Turn 1 is planning only: do not emit a schedule there.
Execution turns must emit BEST_GUESS as valid JSON with machine timelines.
The plan turn must declare one decomposition axis and a boundary cut.
The plan turn must also emit a free-form PLAN_STATE string, and each execution turn must emit an UPDATED_PLAN_STATE string that will be passed back into the next call.
Every queued subtask must include a calibrated p_solve.
When forecasting quality, do not give a probability of exact correctness. Give calibrated probabilities for thresholded gap-to-optimal events.
When forecasting continuation, estimate whether exactly one more subtask is worth its time cost relative to stopping now.
Do not call tools.
Do not write Python, pseudocode, or solver sketches.
Work only from the prompt, the current best schedule, and your own scheduling reasoning.
When a field expects JSON, emit valid JSON.
"""


def build_system_prompt() -> str:
    return CANONICAL_SYSTEM_PROMPT
