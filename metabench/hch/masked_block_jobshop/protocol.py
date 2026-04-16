from __future__ import annotations

import ast
import json
import multiprocessing as mp
import re
import time
from typing import Any

from gemini_client import GeminiChatSession
from jobshop_instance import MaskedBlockJobShopInstance, schedule_summary, verify_schedule
from prompt import build_system_prompt

TOTAL_BUDGET_S = 1800
SUBTASK_BUDGET_S = 600
PLAN_TURN_BUDGET_S = 300
MAX_EXEC_TURNS = 4
TIME_PENALTY = 0.01
GAP_THRESHOLDS = (2.0, 5.0, 10.0)
DECLARED_AXES = {
    "bottleneck_first",
    "family_first",
    "outlier_first",
    "due_date_first",
    "composite",
    "other",
}

_DECISION_RE = re.compile(
    r"^\s*\**\s*DECISION\**\s*:\s*\**\s*(continue|stop)\s*\**\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_SUB_RE = re.compile(
    r"^\s*\**\s*SUB_(\d+)\**\s*:\s*(.*?)(?=^\s*\**\s*[A-Z][A-Z0-9_]*\**\s*:|\Z)",
    re.DOTALL | re.MULTILINE,
)


def _extract_label_block(text: str, label: str) -> str | None:
    pattern = re.compile(
        rf"^\s*\**\s*{re.escape(label)}\**\s*:\s*(.*?)(?=^\s*\**\s*[A-Z][A-Z0-9_]*\**\s*:|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        return None
    return match.group(1).strip()


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _parse_object_loose(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    text = _strip_code_fences(text.strip())
    for parser in (json.loads, ast.literal_eval):
        try:
            value = parser(text)
        except Exception:
            continue
        return value if isinstance(value, dict) else None

    depth = 0
    start = None
    for index, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start is not None:
                chunk = text[start : index + 1]
                for parser in (json.loads, ast.literal_eval):
                    try:
                        value = parser(chunk)
                    except Exception:
                        continue
                    return value if isinstance(value, dict) else None
                return None
    return None


def normalize_next_sub(next_sub: dict[str, Any] | None) -> dict[str, Any] | None:
    if not next_sub:
        return None
    try:
        sub_id = int(next_sub["id"])
    except Exception:
        return None
    desc = str(next_sub.get("desc", "")).strip()
    try:
        time_budget_s = int(next_sub.get("time_budget_s", SUBTASK_BUDGET_S))
    except Exception:
        time_budget_s = SUBTASK_BUDGET_S
    p_solve = _safe_float(next_sub.get("p_solve"))
    if not desc or p_solve is None or not 0.0 <= p_solve <= 1.0:
        return None
    return {
        "id": sub_id,
        "desc": desc,
        "p_solve": p_solve,
        "time_budget_s": max(1, min(time_budget_s, SUBTASK_BUDGET_S)),
    }


def _normalize_gap_forecast(gap_forecast: dict[str, Any] | None) -> dict[str, float] | None:
    if not gap_forecast:
        return None
    canonical: dict[str, float] = {}
    for threshold in GAP_THRESHOLDS:
        key = _gap_key(threshold)
        value = _safe_float(gap_forecast.get(key))
        if value is None or not 0.0 <= value <= 1.0:
            return None
        canonical[key] = value
    ordered = [canonical[_gap_key(threshold)] for threshold in GAP_THRESHOLDS]
    if ordered != sorted(ordered):
        return None
    return canonical


def _normalize_continue_forecast(continue_forecast: dict[str, Any] | None) -> dict[str, float] | None:
    if not continue_forecast:
        return None
    p_improve = _safe_float(continue_forecast.get("p_improve_if_one_more_subtask"))
    expected_gap_reduction = _safe_float(continue_forecast.get("expected_gap_reduction"))
    expected_delta_score = _safe_float(continue_forecast.get("expected_delta_score"))
    if p_improve is None or expected_gap_reduction is None or expected_delta_score is None:
        return None
    if not 0.0 <= p_improve <= 1.0 or expected_gap_reduction < 0.0:
        return None
    return {
        "p_improve_if_one_more_subtask": p_improve,
        "expected_gap_reduction": expected_gap_reduction,
        "expected_delta_score": expected_delta_score,
    }


def _normalize_axis(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    return normalized if normalized in DECLARED_AXES else None


def _normalize_plan_state(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip()
    return normalized or None


def parse_plan_turn(text: str) -> dict[str, Any] | None:
    declared_axis = _normalize_axis(_extract_label_block(text, "DECLARED_DECOMPOSITION_AXIS"))
    declared_axis_rationale = _extract_label_block(text, "DECLARED_AXIS_RATIONALE")
    declared_boundary_cut = _extract_label_block(text, "DECLARED_BOUNDARY_CUT")
    plan_state = _normalize_plan_state(_extract_label_block(text, "PLAN_STATE"))
    atomic_forecast = _normalize_gap_forecast(_parse_object_loose(_extract_label_block(text, "ATOMIC_FORECAST")))
    continue_forecast = _normalize_continue_forecast(
        _parse_object_loose(_extract_label_block(text, "CONTINUE_FORECAST"))
    )
    decision_match = _DECISION_RE.search(text)
    decision = decision_match.group(1).lower() if decision_match else None
    next_sub = _parse_object_loose(_extract_label_block(text, "NEXT_SUB"))
    if (
        declared_axis is None
        or not declared_axis_rationale
        or not declared_boundary_cut
        or plan_state is None
        or atomic_forecast is None
        or continue_forecast is None
        or decision is None
    ):
        return None
    if decision == "continue" and next_sub is None:
        return None
    return {
        "declared_decomposition_axis": declared_axis,
        "declared_axis_rationale": declared_axis_rationale,
        "declared_boundary_cut": declared_boundary_cut,
        "plan_state": plan_state,
        "atomic_forecast": atomic_forecast,
        "continue_forecast": continue_forecast,
        "decision": decision,
        "next_sub": normalize_next_sub(next_sub) if next_sub else None,
    }


def parse_exec_turn(text: str, expected_subtask_id: int | None = None) -> dict[str, Any] | None:
    best_guess = _parse_object_loose(_extract_label_block(text, "BEST_GUESS"))
    updated_plan_state = _normalize_plan_state(_extract_label_block(text, "UPDATED_PLAN_STATE"))
    quality_forecast = _normalize_gap_forecast(
        _parse_object_loose(_extract_label_block(text, "QUALITY_FORECAST"))
    )
    continue_forecast = _normalize_continue_forecast(
        _parse_object_loose(_extract_label_block(text, "CONTINUE_FORECAST"))
    )
    decision_match = _DECISION_RE.search(text)
    decision = decision_match.group(1).lower() if decision_match else None
    next_sub = _parse_object_loose(_extract_label_block(text, "NEXT_SUB"))
    sub_match = _SUB_RE.search(text)
    subtask_id = int(sub_match.group(1)) if sub_match else None
    if (
        best_guess is None
        or updated_plan_state is None
        or quality_forecast is None
        or continue_forecast is None
        or decision is None
        or subtask_id is None
    ):
        return None
    if expected_subtask_id is not None and subtask_id != expected_subtask_id:
        return None
    if decision == "continue" and next_sub is None:
        return None
    return {
        "subtask_id": subtask_id,
        "best_guess": best_guess,
        "updated_plan_state": updated_plan_state,
        "quality_forecast": quality_forecast,
        "continue_forecast": continue_forecast,
        "decision": decision,
        "next_sub": normalize_next_sub(next_sub) if next_sub else None,
    }


def format_turn1_prompt(instance: MaskedBlockJobShopInstance) -> str:
    return (
        f"{instance.problem_statement}\n"
        "Turn 1 is planning only. Do not emit BEST_GUESS or a full schedule yet.\n"
        "Choose a decomposition axis, describe the cut you intend to use, and forecast whether one more subtask is worth it.\n"
        "Use calibrated probabilities for distance-to-optimal thresholds on total objective gap, not a probability of exact correctness.\n"
        "Your CONTINUE_FORECAST should estimate the value of taking exactly one more subtask instead of stopping now.\n"
        "Use this exact output contract:\n"
        "DECLARED_DECOMPOSITION_AXIS: bottleneck_first | family_first | outlier_first | due_date_first | composite | other\n"
        "DECLARED_AXIS_RATIONALE: <free text>\n"
        "DECLARED_BOUNDARY_CUT: <free text>\n"
        "PLAN_STATE: <free text plan state string; choose your own structure and include the current multi-step plan>\n"
        'ATOMIC_FORECAST: {"p_gap_le_2": <float>, "p_gap_le_5": <float>, "p_gap_le_10": <float>}\n'
        'CONTINUE_FORECAST: {"p_improve_if_one_more_subtask": <float>, "expected_gap_reduction": <float>, "expected_delta_score": <float>}\n'
        "DECISION: continue | stop\n"
        f'NEXT_SUB: {{"id": 1, "desc": "...", "p_solve": <float>, "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
        "If DECISION is stop, omit NEXT_SUB.\n"
        f"Probabilities must be between 0 and 1 and monotone: {_gap_key(2.0)} <= {_gap_key(5.0)} <= {_gap_key(10.0)}.\n"
    )


def format_exec_prompt(
    *,
    instance: MaskedBlockJobShopInstance,
    turn_number: int,
    previous_turn: dict[str, Any],
    next_sub: dict[str, Any],
    current_plan_state: str,
    elapsed_s: float,
    current_best_schedule: dict[str, Any],
    current_best_source: str,
    current_best_objective: int,
    current_best_makespan: int,
    current_best_weighted_tardiness: int,
    subtask_budget_s: int,
) -> str:
    remaining_s = max(0.0, TOTAL_BUDGET_S - elapsed_s)
    prev_input = previous_turn.get("input_tokens")
    prev_output = previous_turn.get("output_tokens")
    prev_wall = previous_turn.get("wall_seconds")
    prev_total = previous_turn.get("total_tokens")
    schedule_json = json.dumps(current_best_schedule, indent=2, sort_keys=True)
    return (
        f"{instance.problem_statement}\n"
        f"TURN_{turn_number - 1} STATS: wall={prev_wall:.1f}s, input_tok={_fmt_token(prev_input)}, "
        f"output_tok={_fmt_token(prev_output)}, total_tok={_fmt_token(prev_total)}\n"
        f"CUMULATIVE: wall={elapsed_s:.1f}s / {TOTAL_BUDGET_S}s, remaining={remaining_s:.1f}s\n"
        f"SUBTASK BUDGET: {subtask_budget_s}s per turn (hard kill)\n"
        f"NEXT_SUB_TO_EXECUTE: id={next_sub['id']}, p_solve={next_sub['p_solve']:.2f}, desc={next_sub['desc']}\n"
        f"CURRENT_PLAN_STATE:\n{current_plan_state}\n"
        f"CURRENT_BEST_SOURCE: {current_best_source}\n"
        f"CURRENT_BEST_OBJECTIVE: {current_best_objective}\n"
        f"CURRENT_BEST_MAKESPAN: {current_best_makespan}\n"
        f"CURRENT_BEST_WEIGHTED_TARDINESS: {current_best_weighted_tardiness}\n"
        f"CURRENT_BEST_SUMMARY:\n{schedule_summary(current_best_schedule)}\n"
        f"CURRENT_BEST_JSON:\n{schedule_json}\n"
        "Now execute NEXT_SUB. You may keep the current schedule if you judge further edits are not worth it.\n"
        "QUALITY_FORECAST should describe the quality of the BEST_GUESS you emit this turn.\n"
        "CONTINUE_FORECAST should estimate the value of taking exactly one more subtask after this turn instead of stopping.\n"
        "Use this exact output contract:\n"
        f"SUB_{turn_number - 1}: <work>\n"
        "UPDATED_PLAN_STATE: <free text revised plan state string; you may keep or rewrite the structure entirely>\n"
        "BEST_GUESS: {\n"
        '  "machines": {"M1": [["J1", 0, 3]], "...": []},\n'
        '  "makespan": 24,\n'
        '  "weighted_tardiness": 19,\n'
        '  "objective": 43\n'
        "}\n"
        'QUALITY_FORECAST: {"p_gap_le_2": <float>, "p_gap_le_5": <float>, "p_gap_le_10": <float>}\n'
        'CONTINUE_FORECAST: {"p_improve_if_one_more_subtask": <float>, "expected_gap_reduction": <float>, "expected_delta_score": <float>}\n'
        "DECISION: continue | stop\n"
        f'NEXT_SUB: {{"id": {turn_number}, "desc": "...", "p_solve": <float>, "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
        "If DECISION is stop, omit NEXT_SUB.\n"
        f"Probabilities must be between 0 and 1 and monotone: {_gap_key(2.0)} <= {_gap_key(5.0)} <= {_gap_key(10.0)}.\n"
        "Every required operation must appear exactly once. Start/end times must be integers. Claimed objective fields must match the schedule.\n"
    )


def _fmt_token(value: Any) -> str:
    return "NA" if value is None else str(value)


def _model_call_worker(
    queue: Any,
    model_name: str,
    system_instruction: str,
    message: str,
    timeout_s: int,
) -> None:
    try:
        session = GeminiChatSession(
            model_name=model_name,
            system_instruction=system_instruction,
        )
        queue.put({"ok": True, "result": session.send_message(message, timeout_s)})
    except Exception as exc:  # pragma: no cover - exercised in live API failures
        queue.put({"ok": False, "error": str(exc)})


def _call_with_timeout(
    *,
    model_name: str,
    system_instruction: str,
    message: str,
    timeout_s: int,
) -> dict[str, Any]:
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    process = ctx.Process(
        target=_model_call_worker,
        args=(queue, model_name, system_instruction, message, timeout_s),
    )
    start = time.monotonic()
    process.start()
    process.join(timeout_s)
    if process.is_alive():
        process.kill()
        process.join()
        return {
            "text": "",
            "wall_seconds": time.monotonic() - start,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "thinking_tokens": None,
            "timed_out": True,
        }

    wall_seconds = time.monotonic() - start
    try:
        payload = queue.get_nowait()
    except Exception:
        payload = None
    if payload is not None:
        if payload.get("ok"):
            result = payload["result"]
            result["timed_out"] = False
            return result
        return {
            "text": "",
            "wall_seconds": wall_seconds,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "thinking_tokens": None,
            "timed_out": False,
            "worker_error": payload.get("error"),
        }
    return {
        "text": "",
        "wall_seconds": wall_seconds,
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "thinking_tokens": None,
        "timed_out": False,
        "worker_error": f"worker exited with code {process.exitcode}",
    }


def run_protocol(instance: MaskedBlockJobShopInstance, model_name: str) -> dict[str, Any]:
    system_instruction = build_system_prompt()
    run_start = time.monotonic()
    turns: list[dict[str, Any]] = []
    subtask_summaries: list[dict[str, Any]] = []
    current_best_schedule = dict(instance.baseline_schedule)
    current_best_objective = instance.baseline_objective
    current_best_makespan = instance.baseline_makespan
    current_best_weighted_tardiness = instance.baseline_weighted_tardiness
    current_best_source = "baseline"
    final_schedule_source = "baseline"
    atomic_forecast: dict[str, float] | None = None
    plan_continue_forecast: dict[str, float] | None = None
    final_quality_forecast: dict[str, float] | None = None
    declared_axis: str | None = None
    declared_axis_rationale: str | None = None
    declared_boundary_cut: str | None = None
    current_plan_state: str | None = None
    turn1_died = False
    parse_fail = False
    subtask_killed_count = 0
    revised_best_guess_downward = False
    stop_reason = "unknown"
    next_sub: dict[str, Any] | None = None
    max_exec_turns_reached = False
    feasible_failures = 0
    valid_model_turns: list[int] = []

    plan_response = _call_with_timeout(
        model_name=model_name,
        system_instruction=system_instruction,
        message=format_turn1_prompt(instance),
        timeout_s=PLAN_TURN_BUDGET_S,
    )
    plan_parsed = None if plan_response["timed_out"] else parse_plan_turn(plan_response["text"])
    plan_turn = {
        "turn_index": 1,
        "phase": "plan",
        "raw_text": plan_response["text"],
        "worker_error": plan_response.get("worker_error"),
        "wall_seconds": plan_response["wall_seconds"],
        "input_tokens": plan_response["input_tokens"],
        "output_tokens": plan_response["output_tokens"],
        "total_tokens": plan_response["total_tokens"],
        "thinking_tokens": plan_response["thinking_tokens"],
        "timed_out": plan_response["timed_out"],
        "parse_ok": plan_parsed is not None,
        "parsed": plan_parsed,
    }
    turns.append(plan_turn)

    if plan_response["timed_out"] or plan_parsed is None:
        turn1_died = True
        if not plan_response["timed_out"]:
            parse_fail = True
        stop_reason = "turn1_died"
    else:
        declared_axis = plan_parsed["declared_decomposition_axis"]
        declared_axis_rationale = plan_parsed["declared_axis_rationale"]
        declared_boundary_cut = plan_parsed["declared_boundary_cut"]
        current_plan_state = plan_parsed["plan_state"]
        atomic_forecast = plan_parsed["atomic_forecast"]
        plan_continue_forecast = plan_parsed["continue_forecast"]
        if plan_parsed["decision"] == "stop":
            stop_reason = "turn1_stop"
        else:
            next_sub = plan_parsed["next_sub"]

    turn_number = 2
    while (
        next_sub is not None
        and stop_reason == "unknown"
        and (time.monotonic() - run_start) < TOTAL_BUDGET_S
        and turn_number <= MAX_EXEC_TURNS + 1
    ):
        elapsed_s = time.monotonic() - run_start
        prior_best_objective = current_best_objective
        exec_response = _call_with_timeout(
            model_name=model_name,
            system_instruction=system_instruction,
            message=format_exec_prompt(
                instance=instance,
                turn_number=turn_number,
                previous_turn=turns[-1],
                next_sub=next_sub,
                current_plan_state=current_plan_state or "",
                elapsed_s=elapsed_s,
                current_best_schedule=current_best_schedule,
                current_best_source=current_best_source,
                current_best_objective=current_best_objective,
                current_best_makespan=current_best_makespan,
                current_best_weighted_tardiness=current_best_weighted_tardiness,
                subtask_budget_s=next_sub["time_budget_s"],
            ),
            timeout_s=next_sub["time_budget_s"],
        )
        exec_parsed = None if exec_response["timed_out"] else parse_exec_turn(
            exec_response["text"],
            expected_subtask_id=next_sub["id"],
        )
        exec_turn: dict[str, Any] = {
            "turn_index": turn_number,
            "phase": "exec",
            "next_sub_in": next_sub,
            "raw_text": exec_response["text"],
            "worker_error": exec_response.get("worker_error"),
            "wall_seconds": exec_response["wall_seconds"],
            "input_tokens": exec_response["input_tokens"],
            "output_tokens": exec_response["output_tokens"],
            "total_tokens": exec_response["total_tokens"],
            "thinking_tokens": exec_response["thinking_tokens"],
            "timed_out": exec_response["timed_out"],
            "parse_ok": exec_parsed is not None,
            "parsed": exec_parsed,
        }

        if exec_response["timed_out"]:
            turns.append(exec_turn)
            subtask_killed_count += 1
            stop_reason = "subtask_timeout"
            subtask_summaries.append(
                {
                    "turn_index": turn_number,
                    "subtask_id": next_sub["id"],
                    "desc": next_sub["desc"],
                    "p_solve": next_sub["p_solve"],
                    "timed_out": True,
                    "kept_as_best": False,
                }
            )
            break

        if exec_parsed is None:
            turns.append(exec_turn)
            parse_fail = True
            stop_reason = "subtask_parse_fail"
            subtask_summaries.append(
                {
                    "turn_index": turn_number,
                    "subtask_id": next_sub["id"],
                    "desc": next_sub["desc"],
                    "p_solve": next_sub["p_solve"],
                    "parse_ok": False,
                    "kept_as_best": False,
                }
            )
            break

        verification = verify_schedule(
            jobs=instance.jobs,
            n_machines=instance.n_machines,
            schedule=exec_parsed["best_guess"],
        )
        exec_turn["verification"] = {
            "is_feasible": verification.is_feasible,
            "verified_makespan": verification.verified_makespan,
            "verified_weighted_tardiness": verification.verified_weighted_tardiness,
            "verified_objective": verification.verified_objective,
            "failure_reason": verification.failure_reason,
        }
        turns.append(exec_turn)

        kept_as_best = False
        delta_objective = None
        verified_gap_pct = None
        current_plan_state = exec_parsed["updated_plan_state"]
        if verification.is_feasible and verification.verified_objective is not None:
            verified_schedule = dict(exec_parsed["best_guess"])
            verified_schedule["makespan"] = verification.verified_makespan
            verified_schedule["weighted_tardiness"] = verification.verified_weighted_tardiness
            verified_schedule["objective"] = verification.verified_objective
            delta_objective = verification.verified_objective - prior_best_objective
            verified_gap_pct = (
                100.0 * (verification.verified_objective - instance.optimal_objective) / instance.optimal_objective
            )
            if verification.verified_objective <= current_best_objective:
                kept_as_best = True
                current_best_schedule = verified_schedule
                current_best_objective = verification.verified_objective
                current_best_makespan = verification.verified_makespan or current_best_makespan
                current_best_weighted_tardiness = (
                    verification.verified_weighted_tardiness or current_best_weighted_tardiness
                )
                final_quality_forecast = exec_parsed["quality_forecast"]
                final_schedule_source = "model"
                current_best_source = "model"
                valid_model_turns.append(turn_number)
            else:
                revised_best_guess_downward = True
        else:
            feasible_failures += 1

        subtask_summaries.append(
            {
                "turn_index": turn_number,
                "subtask_id": exec_parsed["subtask_id"],
                "desc": next_sub["desc"],
                "p_solve": next_sub["p_solve"],
                "updated_plan_state": exec_parsed["updated_plan_state"],
                "decision": exec_parsed["decision"],
                "verified_feasible": verification.is_feasible,
                "verified_objective": verification.verified_objective,
                "verified_gap_pct": verified_gap_pct,
                "delta_objective_from_prev_best": delta_objective,
                "kept_as_best": kept_as_best,
            }
        )

        if exec_parsed["decision"] == "stop":
            stop_reason = "subtask_stop"
            break

        next_sub = exec_parsed["next_sub"]
        turn_number += 1

    if stop_reason == "unknown":
        if turn_number > MAX_EXEC_TURNS + 1 and next_sub is not None:
            max_exec_turns_reached = True
            stop_reason = "max_exec_turns"
        else:
            stop_reason = "total_budget_exhausted"

    total_wall_seconds = time.monotonic() - run_start
    baseline_gap_pct = (
        100.0 * (instance.baseline_objective - instance.optimal_objective) / instance.optimal_objective
    )
    gap_pct = 100.0 * (current_best_objective - instance.optimal_objective) / instance.optimal_objective
    brier = _gap_forecast_brier(atomic_forecast, gap_pct)
    final_quality_brier = _gap_forecast_brier(final_quality_forecast, gap_pct)
    score = _score_for_gap(gap_pct, total_wall_seconds)
    plan_stop_now_score = _score_for_gap(baseline_gap_pct, plan_response["wall_seconds"])
    plan_realized_delta_score = score - plan_stop_now_score
    plan_continue_was_worth_it = plan_realized_delta_score > 0.0 if plan_continue_forecast is not None else None
    plan_continue_brier = (
        (plan_continue_forecast["p_improve_if_one_more_subtask"] - float(plan_continue_was_worth_it)) ** 2
        if plan_continue_forecast is not None and plan_continue_was_worth_it is not None
        else None
    )
    plan_expected_delta_score_error = (
        abs(plan_continue_forecast["expected_delta_score"] - plan_realized_delta_score)
        if plan_continue_forecast is not None
        else None
    )
    if final_schedule_source != "model":
        final_schedule_source = "baseline"

    return {
        "model": model_name,
        "seed": instance.seed,
        "requested_n_jobs": instance.requested_n_jobs,
        "requested_n_machines": instance.requested_n_machines,
        "n_jobs": instance.n_jobs,
        "n_machines": instance.n_machines,
        "used_fallback_size": (instance.n_jobs, instance.n_machines)
        != (instance.requested_n_jobs, instance.requested_n_machines),
        "fallback_note": instance.fallback_note,
        "optimal_proven": instance.optimal_proven,
        "solver_status": instance.solver_status,
        "solver_wall_seconds": instance.solver_wall_seconds,
        "jobs": [
            {
                "job_id": job.job_id,
                "due_date": job.due_date,
                "tardiness_weight": job.tardiness_weight,
                "operations": [
                    {"machine_name": op.machine_name, "duration": op.duration}
                    for op in job.operations
                ],
            }
            for job in instance.jobs
        ],
        "preflight_heuristics": [
            {
                "name": result.name,
                "objective": result.objective,
                "makespan": result.makespan,
                "weighted_tardiness": result.weighted_tardiness,
                "gap_pct": result.gap_pct,
                "notes": result.notes,
            }
            for result in instance.heuristic_results
        ],
        "heuristic_spread_pct": instance.heuristic_spread_pct,
        "baseline_schedule": instance.baseline_schedule,
        "baseline_makespan": instance.baseline_makespan,
        "baseline_weighted_tardiness": instance.baseline_weighted_tardiness,
        "baseline_objective": instance.baseline_objective,
        "baseline_gap_pct": baseline_gap_pct,
        "optimal_schedule": instance.optimal_schedule,
        "optimal_makespan": instance.optimal_makespan,
        "optimal_weighted_tardiness": instance.optimal_weighted_tardiness,
        "optimal_objective": instance.optimal_objective,
        "turns": turns,
        "subtask_summaries": subtask_summaries,
        "declared_decomposition_axis": declared_axis,
        "declared_axis_rationale": declared_axis_rationale,
        "declared_boundary_cut": declared_boundary_cut,
        "initial_plan_state": plan_parsed["plan_state"] if plan_parsed is not None else None,
        "final_plan_state": current_plan_state,
        "atomic_forecast": atomic_forecast,
        "plan_continue_forecast": plan_continue_forecast,
        "final_quality_forecast": final_quality_forecast,
        "final_schedule": current_best_schedule,
        "final_makespan": current_best_makespan,
        "final_weighted_tardiness": current_best_weighted_tardiness,
        "final_objective": current_best_objective,
        "gap_pct": gap_pct,
        "score": score,
        "brier": brier,
        "final_quality_brier": final_quality_brier,
        "plan_stop_now_score": plan_stop_now_score,
        "plan_realized_delta_score": plan_realized_delta_score,
        "plan_continue_was_worth_it": plan_continue_was_worth_it,
        "plan_continue_brier": plan_continue_brier,
        "plan_expected_delta_score_error": plan_expected_delta_score_error,
        "total_wall_seconds": total_wall_seconds,
        "turn_count": len(turns),
        "exec_turn_count": sum(1 for turn in turns if turn["phase"] == "exec"),
        "turn1_died": turn1_died,
        "parse_fail": parse_fail,
        "subtask_killed_count": subtask_killed_count,
        "stop_reason": stop_reason,
        "revised_best_guess_downward": revised_best_guess_downward,
        "final_schedule_feasible": True,
        "final_schedule_source": final_schedule_source,
        "feasibility_failure_count": feasible_failures,
        "max_exec_turns_reached": max_exec_turns_reached,
        "valid_model_turns": valid_model_turns,
    }


def _gap_key(threshold: float) -> str:
    return f"p_gap_le_{int(threshold)}"


def _gap_forecast_brier(gap_forecast: dict[str, float] | None, actual_gap_pct: float) -> float | None:
    if gap_forecast is None:
        return None
    terms = []
    for threshold in GAP_THRESHOLDS:
        predicted = gap_forecast[_gap_key(threshold)]
        actual = float(actual_gap_pct <= threshold)
        terms.append((predicted - actual) ** 2)
    return sum(terms) / len(terms)


def _score_for_gap(gap_pct: float, wall_seconds: float) -> float:
    return max(0.0, 100.0 - gap_pct) - TIME_PENALTY * wall_seconds


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None
