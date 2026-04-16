from __future__ import annotations


CANONICAL_SYSTEM_PROMPT = """You are running a locked budget-metagame protocol on a coastal emergency network design task.
You earn score for lowering total cost and lose score for wall-clock time.
Turn 1 is planning only: do not emit an answer there.
Turn 1 should be minimal: only choose the first subtask to run next.
Do not decide whether to stop in turn 1.
Do not restate the problem setup inside the subtask description.
Execution turns must emit EDGES and FREQUENCIES in valid JSON-compatible syntax.
In execution turns, P_CORRECT means the probability that your current answer is within 10 percent of optimum total cost.
Do not call tools.
Do not write code, pseudocode, or solver sketches.
Work only from the prompt, the current best answer, and your own reasoning.
When a field expects JSON, emit valid JSON.
"""


def build_system_prompt() -> str:
    return CANONICAL_SYSTEM_PROMPT
