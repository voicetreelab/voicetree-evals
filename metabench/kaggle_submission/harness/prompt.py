from __future__ import annotations

import json
from typing import Any

from harness.protocol import CF_RESERVE_S, PLAN_TURN_BUDGET_S, SUBTASK_BUDGET_S, TOTAL_BUDGET_S

CLASS_DISPLAY_NAMES = {
    "cjs": "Coupled Job-Shop",
    "graphcol": "Graph Coloring",
    "mwis": "Maximum Weighted Independent Set",
    "steiner": "Steiner x Coloring",
    "tsp": "Traveling Salesperson",
    "ve": "Bayesian Variable Elimination",
}


def build_system_prompt() -> str:
    return (
        "You are solving an optimization problem.\n\n"
        "Value. Each problem is worth up to 100 points of value. Your gap to the optimum "
        "reduces value linearly, at 1 point per percentage point of gap, floored at 0.\n\n"
        "Time cost. Wall time costs 0.01 points per second.\n\n"
        f"Budgets. Total wall budget is {TOTAL_BUDGET_S}s. Turn 1 planning budget is "
        f"{PLAN_TURN_BUDGET_S}s. Each execution subtask may budget up to {SUBTASK_BUDGET_S}s. "
        f"The harness reserves {CF_RESERVE_S}s for a forced one-more-turn counterfactual branch "
        "after a clean stop.\n\n"
        "Protocol. You may decompose the problem into subtasks, revise your plan each turn, "
        "and stop when you judge no more work is worth its time cost. The harness extracts "
        "structured fields from your raw text, so when a field expects JSON, emit valid JSON.\n\n"
        "Do not call tools. Do not write code, pseudocode, or solver sketches. Work only from "
        "the prompt, the running transcript, the current best artifact, and your own reasoning."
    )


def build_turn1_prompt(instance_nl: str, *, cls: str) -> str:
    return (
        f"{instance_nl}\n\n"
        f"Turn 1 for {CLASS_DISPLAY_NAMES.get(cls, cls)} is planning only. Do not emit "
        "BEST_GUESS yet.\n\n"
        "Emit, in order:\n"
        "- `PLAN_STATE`: free-form plan. We will quote this back to you verbatim on every later turn.\n"
        "- `NEXT_SUB`: `{id: 1, desc, p_solve, time_budget_s}`. `p_solve` is your probability "
        "that the final answer lands within the target gap after this subtask. `time_budget_s` "
        f"must be <= {SUBTASK_BUDGET_S}.\n\n"
        f"Planning budget: {PLAN_TURN_BUDGET_S}s."
    )


def build_exec_prompt(
    *,
    instance_nl: str,
    cls: str,
    turn_index: int,
    transcript: str,
    elapsed_s: float,
    current_best: dict[str, Any] | None,
    last_subtask: dict[str, Any] | None,
    subtask_history: list[dict[str, Any]],
) -> str:
    remaining_s = max(0.0, TOTAL_BUDGET_S - elapsed_s)
    current_best_block = "CURRENT_BEST_JSON:\nnone yet"
    if current_best is not None:
        current_best_block = "CURRENT_BEST_JSON:\n" + json.dumps(current_best, indent=2, sort_keys=True)

    schema_block = _best_guess_schema_block(cls)
    timing_block = _timing_block(
        elapsed_s=elapsed_s,
        remaining_s=remaining_s,
        last_subtask=last_subtask,
        subtask_history=subtask_history,
    )

    return (
        f"{instance_nl}\n\n"
        "FULL PRIOR TRANSCRIPT:\n"
        f"{transcript.strip()}\n\n"
        f"{timing_block}\n\n"
        f"{current_best_block}\n\n"
        f"Exec turn {turn_index}. Emit, in order:\n"
        f"- `SUB_{turn_index - 1}`: reasoning/work for this subtask\n"
        f"- `BEST_GUESS`: class-specific JSON for `{cls}`\n"
        f"{schema_block}\n"
        "- `UPDATED_PLAN_STATE`: revised plan, or keep the prior plan verbatim\n"
        "- `QUALITY_FORECAST`: `{p_gap_le_2, p_gap_le_5, p_gap_le_10}` for solo classes, "
        "or the VE-specific thresholds if this is `ve`\n"
        "- `CONTINUE_FORECAST`: `{p_improve, expected_delta_score}` and optionally "
        "`expected_gap_reduction`\n"
        "- `DECISION`: `continue` or `stop`\n"
        f"- `NEXT_SUB`: `{{id: {turn_index}, desc, p_solve, time_budget_s}}` only if you continue\n"
    )


def build_force_continue_prompt(
    *,
    instance_nl: str,
    cls: str,
    turn_index: int,
    transcript: str,
    elapsed_s: float,
    current_best: dict[str, Any] | None,
    last_subtask: dict[str, Any] | None,
    subtask_history: list[dict[str, Any]],
) -> str:
    base = build_exec_prompt(
        instance_nl=instance_nl,
        cls=cls,
        turn_index=turn_index,
        transcript=transcript,
        elapsed_s=elapsed_s,
        current_best=current_best,
        last_subtask=last_subtask,
        subtask_history=subtask_history,
    )
    return (
        f"{base}\n"
        "Counterfactual branch: take exactly one more execution turn from the same transcript state. "
        "Do not emit `DECISION` or `NEXT_SUB` on this branch."
    )


def _timing_block(
    *,
    elapsed_s: float,
    remaining_s: float,
    last_subtask: dict[str, Any] | None,
    subtask_history: list[dict[str, Any]],
) -> str:
    if last_subtask is None:
        last_summary = "none yet"
    else:
        budgeted_s = last_subtask.get("budgeted_s", "?")
        actual_s = last_subtask.get("actual_s", "?")
        desc = last_subtask.get("desc", "")
        last_summary = f"budgeted {budgeted_s}s, actual {actual_s}s, desc={desc}"

    history_bits = []
    for item in subtask_history:
        sub_id = item.get("id", "?")
        budgeted_s = item.get("budgeted_s", "?")
        actual_s = item.get("actual_s", "?")
        history_bits.append(f"s{sub_id} {actual_s}/{budgeted_s}s")
    history_text = ", ".join(history_bits) if history_bits else "none yet"

    return (
        f"TIMING: global elapsed {elapsed_s:.1f}s / {TOTAL_BUDGET_S}s "
        f"(remaining {remaining_s:.1f}s).\n"
        f"LAST_SUBTASK: {last_summary}\n"
        f"SUBTASK_HISTORY: [{history_text}]"
    )


def _best_guess_schema_block(cls: str) -> str:
    try:
        from verifiers import CLASS_TO_BEST_GUESS_SCHEMA
    except Exception:
        return "- BEST_GUESS schema example unavailable until verifier registries are in place."

    schema = CLASS_TO_BEST_GUESS_SCHEMA.get(cls)
    if not schema:
        return f"- BEST_GUESS schema example unavailable for `{cls}`."
    return f"- BEST_GUESS schema example for `{cls}`:\n```json\n{schema}\n```"
