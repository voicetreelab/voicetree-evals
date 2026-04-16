from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path
from typing import Any

from gemini_client import load_local_env
from jobshop_instance import build_instance, schedule_summary, verify_schedule
from prompt import build_system_prompt
from protocol import (
    SUBTASK_BUDGET_S,
    TOTAL_BUDGET_S,
    _call_with_timeout,
    _extract_label_block,
    _normalize_continue_forecast,
    _normalize_gap_forecast,
    _parse_object_loose,
    _safe_float,
    _score_for_gap,
)


_DECISION_RE = re.compile(
    r"^\s*\**\s*DECISION\**\s*:\s*\**\s*(continue|stop)\s*\**\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Force exactly one more masked-block exec turn from a saved stop state.")
    parser.add_argument(
        "--input-row",
        type=Path,
        required=True,
        help="JSONL file containing the saved masked-block run row.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output JSON path for the forced-continuation result.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Optional model override. Defaults to the original row model.",
    )
    return parser.parse_args()


def _normalize_forced_subtask(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not value:
        return None
    desc = str(value.get("desc", "")).strip()
    p_solve = _safe_float(value.get("p_solve"))
    if not desc or p_solve is None or not 0.0 <= p_solve <= 1.0:
        return None
    try:
        time_budget_s = int(value.get("time_budget_s", SUBTASK_BUDGET_S))
    except Exception:
        time_budget_s = SUBTASK_BUDGET_S
    return {
        "desc": desc,
        "p_solve": p_solve,
        "time_budget_s": max(1, min(time_budget_s, SUBTASK_BUDGET_S)),
    }


def parse_forced_turn(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2:
            stripped = "\n".join(lines[1:-1]).strip()
    for parser in (json.loads, ast.literal_eval):
        try:
            wrapper = parser(stripped)
        except Exception:
            continue
        if isinstance(wrapper, dict) and "CHOSEN_SUBTASK" in wrapper and "BEST_GUESS" in wrapper:
            chosen_subtask = _normalize_forced_subtask(wrapper.get("CHOSEN_SUBTASK"))
            updated_plan_state = str(wrapper.get("UPDATED_PLAN_STATE", "")).strip()
            quality_forecast = _normalize_gap_forecast(wrapper.get("QUALITY_FORECAST"))
            continue_forecast = _normalize_continue_forecast(wrapper.get("CONTINUE_FORECAST"))
            decision = str(wrapper.get("DECISION", "")).strip().lower()
            next_sub = _normalize_forced_subtask(wrapper.get("NEXT_SUB"))
            if (
                chosen_subtask is None
                or not updated_plan_state
                or not isinstance(wrapper.get("BEST_GUESS"), dict)
                or quality_forecast is None
                or continue_forecast is None
                or decision not in {"continue", "stop"}
            ):
                return None
            if decision == "continue" and next_sub is None:
                return None
            return {
                "chosen_subtask": chosen_subtask,
                "updated_plan_state": updated_plan_state,
                "best_guess": wrapper["BEST_GUESS"],
                "quality_forecast": quality_forecast,
                "continue_forecast": continue_forecast,
                "decision": decision,
                "next_sub": next_sub,
            }

    chosen_subtask = _normalize_forced_subtask(_parse_object_loose(_extract_label_block(text, "CHOSEN_SUBTASK")))
    updated_plan_state = _extract_label_block(text, "UPDATED_PLAN_STATE")
    best_guess = _parse_object_loose(_extract_label_block(text, "BEST_GUESS"))
    quality_forecast = _normalize_gap_forecast(_parse_object_loose(_extract_label_block(text, "QUALITY_FORECAST")))
    continue_forecast = _normalize_continue_forecast(
        _parse_object_loose(_extract_label_block(text, "CONTINUE_FORECAST"))
    )
    decision_match = _DECISION_RE.search(text)
    decision = decision_match.group(1).lower() if decision_match else None
    next_sub = _normalize_forced_subtask(_parse_object_loose(_extract_label_block(text, "NEXT_SUB")))
    if (
        chosen_subtask is None
        or updated_plan_state is None
        or best_guess is None
        or quality_forecast is None
        or continue_forecast is None
        or decision is None
    ):
        return None
    if decision == "continue" and next_sub is None:
        return None
    return {
        "chosen_subtask": chosen_subtask,
        "updated_plan_state": updated_plan_state.strip(),
        "best_guess": best_guess,
        "quality_forecast": quality_forecast,
        "continue_forecast": continue_forecast,
        "decision": decision,
        "next_sub": next_sub,
    }


def format_forced_exec_prompt(*, instance: Any, row: dict[str, Any]) -> str:
    previous_turn = row["turns"][-1]
    current_best_schedule = row["final_schedule"]
    schedule_json = json.dumps(current_best_schedule, indent=2, sort_keys=True)
    return (
        f"{instance.problem_statement}\n"
        "Counterfactual evaluation: in the original run, you chose STOP after the previous turn.\n"
        "You must now take exactly one additional execution turn from that saved stop state.\n"
        "Choose the single most valuable next subtask, execute it now, update the plan state, and emit a revised BEST_GUESS.\n"
        "Do not refuse on the grounds that you previously stopped; this call is the forced one-more-subtask branch.\n"
        f"PREVIOUS TURN STATS: wall={previous_turn['wall_seconds']:.1f}s, "
        f"input_tok={previous_turn.get('input_tokens')}, output_tok={previous_turn.get('output_tokens')}, "
        f"total_tok={previous_turn.get('total_tokens')}\n"
        f"CUMULATIVE: wall={row['total_wall_seconds']:.1f}s / {TOTAL_BUDGET_S}s, "
        f"remaining={max(0.0, TOTAL_BUDGET_S - row['total_wall_seconds']):.1f}s\n"
        f"FORCED SUBTASK BUDGET: {SUBTASK_BUDGET_S}s (hard kill)\n"
        f"CURRENT_PLAN_STATE:\n{row['final_plan_state']}\n"
        f"CURRENT_BEST_SOURCE: {row['final_schedule_source']}\n"
        f"CURRENT_BEST_OBJECTIVE: {row['final_objective']}\n"
        f"CURRENT_BEST_MAKESPAN: {row['final_makespan']}\n"
        f"CURRENT_BEST_WEIGHTED_TARDINESS: {row['final_weighted_tardiness']}\n"
        f"CURRENT_BEST_SUMMARY:\n{schedule_summary(current_best_schedule)}\n"
        f"CURRENT_BEST_JSON:\n{schedule_json}\n"
        "Use this exact output contract:\n"
        'CHOSEN_SUBTASK: {"desc": "...", "p_solve": <float>, "time_budget_s": 600}\n'
        "SUB_FORCED: <work>\n"
        "UPDATED_PLAN_STATE: <free text revised plan state string>\n"
        "BEST_GUESS: {\n"
        '  "machines": {"M1": [["J1", 0, 3]], "...": []},\n'
        '  "makespan": 24,\n'
        '  "weighted_tardiness": 19,\n'
        '  "objective": 43\n'
        "}\n"
        'QUALITY_FORECAST: {"p_gap_le_2": <float>, "p_gap_le_5": <float>, "p_gap_le_10": <float>}\n'
        'CONTINUE_FORECAST: {"p_improve_if_one_more_subtask": <float>, "expected_gap_reduction": <float>, "expected_delta_score": <float>}\n'
        "DECISION: continue | stop\n"
        f'NEXT_SUB: {{"desc": "...", "p_solve": <float>, "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
        "If DECISION is stop, omit NEXT_SUB.\n"
        "Probabilities must be between 0 and 1 and monotone.\n"
        "Every required operation must appear exactly once. Start/end times must be integers. Claimed objective fields must match the schedule.\n"
    )


def load_row(path: Path) -> dict[str, Any]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"no rows found in {path}")
    return json.loads(lines[-1])


def main() -> None:
    args = parse_args()
    load_local_env()

    row = load_row(args.input_row)
    model_name = args.model or row["model"]
    instance = build_instance(
        seed=row["seed"],
        n_jobs=row["requested_n_jobs"],
        n_machines=row["requested_n_machines"],
    )
    if instance.optimal_objective != row["optimal_objective"] or instance.baseline_objective != row["baseline_objective"]:
        raise RuntimeError("reconstructed instance does not match saved row")

    prompt = format_forced_exec_prompt(instance=instance, row=row)
    response = _call_with_timeout(
        model_name=model_name,
        system_instruction=build_system_prompt(),
        message=prompt,
        timeout_s=SUBTASK_BUDGET_S,
    )
    parsed = None if response["timed_out"] else parse_forced_turn(response["text"])
    verification = None
    final_schedule = row["final_schedule"]
    final_objective = row["final_objective"]
    final_makespan = row["final_makespan"]
    final_weighted_tardiness = row["final_weighted_tardiness"]
    final_plan_state = row["final_plan_state"]
    kept_as_best = False

    if parsed is not None:
        verification = verify_schedule(
            jobs=instance.jobs,
            n_machines=instance.n_machines,
            schedule=parsed["best_guess"],
        )
        final_plan_state = parsed["updated_plan_state"]
        if verification.is_feasible and verification.verified_objective is not None:
            if verification.verified_objective <= final_objective:
                kept_as_best = True
                final_schedule = dict(parsed["best_guess"])
                final_schedule["makespan"] = verification.verified_makespan
                final_schedule["weighted_tardiness"] = verification.verified_weighted_tardiness
                final_schedule["objective"] = verification.verified_objective
                final_objective = verification.verified_objective
                final_makespan = verification.verified_makespan
                final_weighted_tardiness = verification.verified_weighted_tardiness

    total_wall_seconds = row["total_wall_seconds"] + response["wall_seconds"]
    gap_pct = 100.0 * (final_objective - row["optimal_objective"]) / row["optimal_objective"]
    forced_score = _score_for_gap(gap_pct, total_wall_seconds)
    score_delta = forced_score - row["score"]

    result = {
        "source_row_path": str(args.input_row),
        "model": model_name,
        "seed": row["seed"],
        "n_jobs": row["n_jobs"],
        "n_machines": row["n_machines"],
        "original_stop_score": row["score"],
        "original_stop_objective": row["final_objective"],
        "original_stop_gap_pct": row["gap_pct"],
        "forced_prompt": prompt,
        "forced_response": response,
        "forced_parsed": parsed,
        "verification": None
        if verification is None
        else {
            "is_feasible": verification.is_feasible,
            "verified_makespan": verification.verified_makespan,
            "verified_weighted_tardiness": verification.verified_weighted_tardiness,
            "verified_objective": verification.verified_objective,
            "failure_reason": verification.failure_reason,
        },
        "kept_as_best": kept_as_best,
        "counterfactual_final_schedule": final_schedule,
        "counterfactual_final_objective": final_objective,
        "counterfactual_final_makespan": final_makespan,
        "counterfactual_final_weighted_tardiness": final_weighted_tardiness,
        "counterfactual_final_plan_state": final_plan_state,
        "counterfactual_total_wall_seconds": total_wall_seconds,
        "counterfactual_gap_pct": gap_pct,
        "counterfactual_score": forced_score,
        "score_delta_vs_stop": score_delta,
        "forced_step_helped": score_delta > 0.0,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
