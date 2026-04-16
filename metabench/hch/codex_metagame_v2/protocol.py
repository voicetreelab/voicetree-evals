from __future__ import annotations

import ast
import concurrent.futures
import json
import re
import time
from typing import Any

from gemini_client import GeminiChatSession
from jobshop_instance import CoupledJobShopInstance, schedule_summary, verify_schedule
from prompt import build_system_prompt
from render_nl import render_problem

TOTAL_BUDGET_S = 1800
SUBTASK_BUDGET_S = 600
PLAN_TURN_BUDGET_S = 300
MAX_EXEC_TURNS = 4
TIME_PENALTY = 0.01
GAP_THRESHOLDS = (2.0, 5.0, 10.0)

_FLOAT_PATTERN = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
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


def _extract_float(text: str, label: str) -> float | None:
    block = _extract_label_block(text, label)
    if not block:
        return None
    match = re.search(_FLOAT_PATTERN, block)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


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


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return stripped


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
    if not desc:
        return None
    return {
        "id": sub_id,
        "desc": desc,
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
    if not 0.0 <= p_improve <= 1.0:
        return None
    if expected_gap_reduction < 0.0:
        return None
    return {
        "p_improve_if_one_more_subtask": p_improve,
        "expected_gap_reduction": expected_gap_reduction,
        "expected_delta_score": expected_delta_score,
    }


def parse_plan_turn(text: str) -> dict[str, Any] | None:
    atomic_forecast = _normalize_gap_forecast(_parse_object_loose(_extract_label_block(text, "ATOMIC_FORECAST")))
    continue_forecast = _normalize_continue_forecast(
        _parse_object_loose(_extract_label_block(text, "CONTINUE_FORECAST"))
    )
    decision_match = _DECISION_RE.search(text)
    decision = decision_match.group(1).lower() if decision_match else None
    next_sub = _parse_object_loose(_extract_label_block(text, "NEXT_SUB"))
    if atomic_forecast is None or continue_forecast is None or decision is None:
        return None
    if decision == "continue" and next_sub is None:
        return None
    return {
        "atomic_forecast": atomic_forecast,
        "continue_forecast": continue_forecast,
        "decision": decision,
        "next_sub": normalize_next_sub(next_sub) if next_sub else None,
    }


def parse_exec_turn(text: str, expected_subtask_id: int | None = None) -> dict[str, Any] | None:
    best_guess = _parse_object_loose(_extract_label_block(text, "BEST_GUESS"))
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
        "quality_forecast": quality_forecast,
        "continue_forecast": continue_forecast,
        "decision": decision,
        "next_sub": normalize_next_sub(next_sub) if next_sub else None,
    }


def format_turn1_prompt(instance: CoupledJobShopInstance) -> str:
    return (
        f"{render_problem(instance)}\n"
        "Turn 1 is planning only. Do not emit BEST_GUESS or a full schedule yet.\n"
        "Forecast the quality of an atomic answer and whether one more subtask is economically worth it.\n"
        "Use calibrated probabilities for distance-to-optimal thresholds, not a probability of exact correctness.\n"
        "Your CONTINUE_FORECAST should estimate the value of taking exactly one more subtask instead of stopping now.\n"
        "Use this exact output contract:\n"
        'ATOMIC_FORECAST: {"p_gap_le_2": <float>, "p_gap_le_5": <float>, "p_gap_le_10": <float>}\n'
        'CONTINUE_FORECAST: {"p_improve_if_one_more_subtask": <float>, "expected_gap_reduction": <float>, "expected_delta_score": <float>}\n'
        "DECISION: continue | stop\n"
        f'NEXT_SUB: {{"id": 1, "desc": "...", "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
        "If DECISION is stop, omit NEXT_SUB.\n"
        f"Probabilities must be between 0 and 1 and must be monotone: {_gap_key(2.0)} <= {_gap_key(5.0)} <= {_gap_key(10.0)}.\n"
    )


def format_exec_prompt(
    *,
    turn_number: int,
    previous_turn: dict[str, Any],
    elapsed_s: float,
    current_best_schedule: dict[str, Any],
    current_best_source: str,
    current_best_makespan: int,
    subtask_budget_s: int,
) -> str:
    remaining_s = max(0.0, TOTAL_BUDGET_S - elapsed_s)
    prev_input = previous_turn.get("input_tokens")
    prev_output = previous_turn.get("output_tokens")
    prev_wall = previous_turn.get("wall_seconds")
    prev_total = previous_turn.get("total_tokens")
    schedule_json = json.dumps(current_best_schedule, indent=2, sort_keys=True)
    return (
        f"TURN_{turn_number - 1} STATS: wall={prev_wall:.1f}s, input_tok={_fmt_token(prev_input)}, "
        f"output_tok={_fmt_token(prev_output)}, total_tok={_fmt_token(prev_total)}\n"
        f"CUMULATIVE: wall={elapsed_s:.1f}s / {TOTAL_BUDGET_S}s, remaining={remaining_s:.1f}s\n"
        f"SUBTASK BUDGET: {subtask_budget_s}s per turn (hard kill)\n"
        f"CURRENT_BEST_SOURCE: {current_best_source}\n"
        f"CURRENT_BEST_MAKESPAN: {current_best_makespan}\n"
        f"CURRENT_BEST_SUMMARY:\n{schedule_summary(current_best_schedule)}\n"
        f"CURRENT_BEST_JSON:\n{schedule_json}\n"
        "Now execute NEXT_SUB. You may keep the current schedule if you judge further edits are not worth it.\n"
        "QUALITY_FORECAST should describe the quality of the BEST_GUESS you emit this turn.\n"
        "CONTINUE_FORECAST should estimate the value of taking exactly one more subtask after this turn instead of stopping.\n"
        "Use this exact output contract:\n"
        f"SUB_{turn_number - 1}: <work>\n"
        "BEST_GUESS: {\n"
        '  "factory_a": {"MA1": [["J1", 0, 3]], "...": []},\n'
        '  "factory_b": {"MB1": [["J2", 8, 10]], "...": []},\n'
        '  "makespan": 24\n'
        "}\n"
        'QUALITY_FORECAST: {"p_gap_le_2": <float>, "p_gap_le_5": <float>, "p_gap_le_10": <float>}\n'
        'CONTINUE_FORECAST: {"p_improve_if_one_more_subtask": <float>, "expected_gap_reduction": <float>, "expected_delta_score": <float>}\n'
        "DECISION: continue | stop\n"
        f'NEXT_SUB: {{"id": {turn_number}, "desc": "...", "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
        "If DECISION is stop, omit NEXT_SUB.\n"
        f"Probabilities must be between 0 and 1 and must be monotone: {_gap_key(2.0)} <= {_gap_key(5.0)} <= {_gap_key(10.0)}.\n"
        "Every required operation must appear exactly once. Start/end times must be integers. Claimed makespan must match the schedule.\n"
    )


def _fmt_token(value: Any) -> str:
    return "NA" if value is None else str(value)


def _call_with_timeout(session: GeminiChatSession, message: str, timeout_s: int) -> dict[str, Any]:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    start = time.monotonic()
    future = executor.submit(session.send_message, message, timeout_s)
    try:
        result = future.result(timeout=timeout_s)
        result["timed_out"] = False
        return result
    except concurrent.futures.TimeoutError:
        future.cancel()
        return {
            "text": "",
            "wall_seconds": time.monotonic() - start,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "thinking_tokens": None,
            "timed_out": True,
        }
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def run_protocol(instance: CoupledJobShopInstance, model_name: str) -> dict[str, Any]:
    session = GeminiChatSession(
        model_name=model_name,
        system_instruction=build_system_prompt(),
    )
    run_start = time.monotonic()
    turns: list[dict[str, Any]] = []
    current_best_schedule = instance.baseline_schedule
    current_best_makespan = instance.baseline_makespan
    current_best_source = "baseline"
    final_schedule_source = "baseline"
    atomic_forecast: dict[str, float] | None = None
    plan_continue_forecast: dict[str, float] | None = None
    final_quality_forecast: dict[str, float] | None = None
    turn1_died = False
    parse_fail = False
    subtask_killed_count = 0
    revised_best_guess_downward = False
    stop_reason = "unknown"
    next_sub: dict[str, Any] | None = None
    max_exec_turns_reached = False
    feasible_failures = 0
    valid_model_turns: list[int] = []

    plan_response = _call_with_timeout(session, format_turn1_prompt(instance), PLAN_TURN_BUDGET_S)
    plan_parsed = None if plan_response["timed_out"] else parse_plan_turn(plan_response["text"])
    plan_turn = {
        "turn_index": 1,
        "phase": "plan",
        "raw_text": plan_response["text"],
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
        exec_response = _call_with_timeout(
            session,
            format_exec_prompt(
                turn_number=turn_number,
                previous_turn=turns[-1],
                elapsed_s=elapsed_s,
                current_best_schedule=current_best_schedule,
                current_best_source=current_best_source,
                current_best_makespan=current_best_makespan,
                subtask_budget_s=next_sub["time_budget_s"],
            ),
            next_sub["time_budget_s"],
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
            break

        if exec_parsed is None:
            turns.append(exec_turn)
            parse_fail = True
            stop_reason = "subtask_parse_fail"
            break

        verification = verify_schedule(
            jobs=instance.jobs,
            n_machines=instance.n_machines,
            schedule=exec_parsed["best_guess"],
        )
        exec_turn["verification"] = {
            "is_feasible": verification.is_feasible,
            "verified_makespan": verification.verified_makespan,
            "failure_reason": verification.failure_reason,
        }
        turns.append(exec_turn)

        if verification.is_feasible and verification.verified_makespan is not None:
            if verification.verified_makespan > current_best_makespan:
                revised_best_guess_downward = True
            current_best_schedule = exec_parsed["best_guess"]
            current_best_makespan = verification.verified_makespan
            final_quality_forecast = exec_parsed["quality_forecast"]
            final_schedule_source = "model"
            current_best_source = "model"
            valid_model_turns.append(turn_number)
        else:
            feasible_failures += 1
            if valid_model_turns:
                final_schedule_source = "last_good_turn"
                current_best_source = "last_good_turn"

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
    final_schedule_feasible = current_best_makespan is not None
    baseline_gap_pct = 100.0 * (instance.baseline_makespan - instance.optimal_makespan) / instance.optimal_makespan
    gap_pct = 100.0 * (current_best_makespan - instance.optimal_makespan) / instance.optimal_makespan
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
    if not valid_model_turns:
        final_schedule_source = "baseline"

    return {
        "model": model_name,
        "seed": instance.seed,
        "n_jobs": instance.n_jobs,
        "n_machines": instance.n_machines,
        "jobs": [
            {
                "job_id": job.job_id,
                "factory_a": [
                    {"machine_name": op.machine_name, "duration": op.duration}
                    for op in job.factory_a
                ],
                "factory_b": [
                    {"machine_name": op.machine_name, "duration": op.duration}
                    for op in job.factory_b
                ],
            }
            for job in instance.jobs
        ],
        "baseline_schedule": instance.baseline_schedule,
        "baseline_makespan": instance.baseline_makespan,
        "baseline_gap_pct": baseline_gap_pct,
        "optimal_schedule": instance.optimal_schedule,
        "optimal_makespan": instance.optimal_makespan,
        "turns": turns,
        "atomic_forecast": atomic_forecast,
        "plan_continue_forecast": plan_continue_forecast,
        "final_quality_forecast": final_quality_forecast,
        "declared_gap": None,
        "atomic_p_correct": None,
        "final_schedule": current_best_schedule,
        "final_makespan": current_best_makespan,
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
        "turn1_died": turn1_died,
        "subtask_killed_count": subtask_killed_count,
        "stop_reason": stop_reason,
        "revised_best_guess_downward": revised_best_guess_downward,
        "final_schedule_feasible": final_schedule_feasible,
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
