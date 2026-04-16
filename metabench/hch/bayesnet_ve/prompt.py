from __future__ import annotations


CANONICAL_SYSTEM_PROMPT = """You are running a locked budget-metagame protocol on an exact Bayesian-network variable-elimination problem.
You earn score for reducing log-probability error and lose score for wall-clock time.
Turn 1 is planning only: do not emit BEST_GUESS there.
Execution turns must emit BEST_GUESS as valid JSON.
The plan turn must declare one elimination axis and an initial elimination-ordering prefix.
The plan turn must also emit a free-form PLAN_STATE string, and each execution turn must emit an UPDATED_PLAN_STATE string that will be passed back into the next call.
Every queued subtask must include a calibrated p_solve.
When forecasting quality, do not give a probability of exact correctness. Give calibrated probabilities for thresholded log-gap events.
When forecasting continuation, estimate whether exactly one more subtask is worth its time cost relative to stopping now.
Do not call tools.
Do not write Python, pseudocode, or solver sketches.
Work only from the prompt, the current plan state, the current best estimate if one exists, and your own inference reasoning.
When a field expects JSON, emit valid JSON.
"""


def build_system_prompt() -> str:
    return CANONICAL_SYSTEM_PROMPT

