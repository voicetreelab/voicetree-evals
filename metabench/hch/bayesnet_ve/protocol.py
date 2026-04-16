from __future__ import annotations

import ast
import json
import math
import multiprocessing as mp
import re
import time
from typing import Any

from bayesnet_instance import BayesianVEInstance, verify_best_guess
from gemini_client import GeminiChatSession
from prompt import build_system_prompt

TOTAL_BUDGET_S = 1800
SUBTASK_BUDGET_S = 600
PLAN_TURN_BUDGET_S = 300
MAX_EXEC_TURNS = 4
TIME_PENALTY = 0.01
GAP_THRESHOLDS = (0.01, 0.1, 0.5)
DECLARED_AXES = {
    "min_neighbors",
    "min_weight",
    "min_fill",
    "cluster_first",
    "query_centered",
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


def _parse_list_loose(text: str | None) -> list[Any] | None:
    if not text:
        return None
    text = _strip_code_fences(text.strip())
    for parser in (json.loads, ast.literal_eval):
        try:
            value = parser(text)
        except Exception:
            continue
        return value if isinstance(value, list) else None

    depth = 0
    start = None
    for index, char in enumerate(text):
        if char == "[":
            if depth == 0:
                start = index
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0 and start is not None:
                chunk = text[start : index + 1]
                for parser in (json.loads, ast.literal_eval):
                    try:
                        value = parser(chunk)
                    except Exception:
                        continue
                    return value if isinstance(value, list) else None
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


def _normalize_declared_ordering(ordering: list[Any] | None) -> list[str] | None:
    if not ordering:
        return None
    normalized = [str(value).strip() for value in ordering]
    if not all(normalized):
        return None
    if len(set(normalized)) != len(normalized):
        return None
    return normalized


def parse_plan_turn(text: str) -> dict[str, Any] | None:
    declared_axis = _normalize_axis(_extract_label_block(text, "DECLARED_ELIMINATION_AXIS"))
    declared_axis_rationale = _extract_label_block(text, "DECLARED_AXIS_RATIONALE")
    declared_ordering = _normalize_declared_ordering(_parse_list_loose(_extract_label_block(text, "DECLARED_ORDERING")))
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
        or declared_ordering is None
        or plan_state is None
        or atomic_forecast is None
        or continue_forecast is None
        or decision is None
    ):
        return None
    if decision == "continue" and next_sub is None:
        return None
    return {
        "declared_elimination_axis": declared_axis,
        "declared_axis_rationale": declared_axis_rationale,
        "declared_ordering": declared_ordering,
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


def format_turn1_prompt(instance: BayesianVEInstance) -> str:
    return (
        f"{instance.problem_statement}\n"
        "Turn 1 is planning only. Do not emit BEST_GUESS yet.\n"
        "Choose an elimination axis, write the first 5-7 eliminable variables of the elimination order you currently intend to use, and explain why.\n"
        "Use calibrated probabilities for thresholded log-gap events, not a probability of exact correctness.\n"
        "Your CONTINUE_FORECAST should estimate the value of taking exactly one more subtask after your first execution turn instead of stopping after that turn.\n"
        "Use this exact output contract:\n"
        "DECLARED_ELIMINATION_AXIS: min_neighbors | min_weight | min_fill | cluster_first | query_centered | composite | other\n"
        "DECLARED_AXIS_RATIONALE: <free text>\n"
        'DECLARED_ORDERING: ["X1", "X2", "X3", "X4", "X5"]\n'
        "PLAN_STATE: <free text plan state string; choose your own structure and include the current multi-step plan>\n"
        f'ATOMIC_FORECAST: {{"{_gap_key(0.01)}": <float>, "{_gap_key(0.1)}": <float>, "{_gap_key(0.5)}": <float>}}\n'
        'CONTINUE_FORECAST: {"p_improve_if_one_more_subtask": <float>, "expected_gap_reduction": <float>, "expected_delta_score": <float>}\n'
        "DECISION: continue | stop\n"
        f'NEXT_SUB: {{"id": 1, "desc": "...", "p_solve": <float>, "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
        "If DECISION is stop, omit NEXT_SUB.\n"
        f"Probabilities must be between 0 and 1 and monotone: {_gap_key(0.01)} <= {_gap_key(0.1)} <= {_gap_key(0.5)}.\n"
    )


def format_exec_prompt(
    *,
    instance: BayesianVEInstance,
    turn_number: int,
    previous_turn: dict[str, Any],
    next_sub: dict[str, Any],
    current_plan_state: str,
    elapsed_s: float,
    current_best_guess: dict[str, Any] | None,
    subtask_budget_s: int,
) -> str:
    remaining_s = max(0.0, TOTAL_BUDGET_S - elapsed_s)
    prev_input = previous_turn.get("input_tokens")
    prev_output = previous_turn.get("output_tokens")
    prev_wall = previous_turn.get("wall_seconds")
    prev_total = previous_turn.get("total_tokens")
    if current_best_guess is None:
        current_best_block = "CURRENT_BEST_GUESS: none yet\n"
    else:
        current_best_block = (
            "CURRENT_BEST_GUESS_JSON:\n"
            f"{json.dumps(current_best_guess, indent=2, sort_keys=True)}\n"
        )
    return (
        f"{instance.problem_statement}\n"
        f"TURN_{turn_number - 1} STATS: wall={prev_wall:.1f}s, input_tok={_fmt_token(prev_input)}, "
        f"output_tok={_fmt_token(prev_output)}, total_tok={_fmt_token(prev_total)}\n"
        f"CUMULATIVE: wall={elapsed_s:.1f}s / {TOTAL_BUDGET_S}s, remaining={remaining_s:.1f}s\n"
        f"SUBTASK BUDGET: {subtask_budget_s}s per turn (hard kill)\n"
        f"NEXT_SUB_TO_EXECUTE: id={next_sub['id']}, p_solve={next_sub['p_solve']:.2f}, desc={next_sub['desc']}\n"
        f"CURRENT_PLAN_STATE:\n{current_plan_state}\n"
        f"{current_best_block}"
        "Now execute NEXT_SUB. If you want to keep the current best estimate, repeat it exactly in BEST_GUESS.\n"
        "BEST_GUESS must contain a strictly between-0-and-1 posterior estimate, a full elimination order over all eliminable variables, and your self-reported peak factor size.\n"
        "QUALITY_FORECAST should describe the quality of the BEST_GUESS you emit this turn.\n"
        "CONTINUE_FORECAST should estimate the value of taking exactly one more subtask after this turn instead of stopping.\n"
        "Use this exact output contract:\n"
        f"SUB_{turn_number - 1}: <work>\n"
        "UPDATED_PLAN_STATE: <free text revised plan state string; you may keep or rewrite the structure entirely>\n"
        "BEST_GUESS: {\n"
        '  "p_query_given_evidence": 0.417,\n'
        '  "ordering_used": ["X1", "X2", "X3"],\n'
        '  "peak_factor_size_self_report": 6\n'
        "}\n"
        f'QUALITY_FORECAST: {{"{_gap_key(0.01)}": <float>, "{_gap_key(0.1)}": <float>, "{_gap_key(0.5)}": <float>}}\n'
        'CONTINUE_FORECAST: {"p_improve_if_one_more_subtask": <float>, "expected_gap_reduction": <float>, "expected_delta_score": <float>}\n'
        "DECISION: continue | stop\n"
        f'NEXT_SUB: {{"id": {turn_number}, "desc": "...", "p_solve": <float>, "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
        "If DECISION is stop, omit NEXT_SUB.\n"
        f"Probabilities must be between 0 and 1 and monotone: {_gap_key(0.01)} <= {_gap_key(0.1)} <= {_gap_key(0.5)}.\n"
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


def run_protocol(instance: BayesianVEInstance, model_name: str) -> dict[str, Any]:
    system_instruction = build_system_prompt()
    run_start = time.monotonic()
    turns: list[dict[str, Any]] = []
    subtask_summaries: list[dict[str, Any]] = []
    current_best_guess: dict[str, Any] | None = None
    current_best_gap_nats: float | None = None
    atomic_forecast: dict[str, float] | None = None
    plan_continue_forecast: dict[str, float] | None = None
    final_quality_forecast: dict[str, float] | None = None
    declared_axis: str | None = None
    declared_axis_rationale: str | None = None
    declared_ordering: list[str] | None = None
    current_plan_state: str | None = None
    turn1_died = False
    parse_fail = False
    subtask_killed_count = 0
    revised_best_guess_downward = False
    stop_reason = "unknown"
    next_sub: dict[str, Any] | None = None
    max_exec_turns_reached = False
    validity_failures = 0
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
        declared_axis = plan_parsed["declared_elimination_axis"]
        declared_axis_rationale = plan_parsed["declared_axis_rationale"]
        declared_ordering = plan_parsed["declared_ordering"]
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
        prior_best_gap_nats = current_best_gap_nats
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
                current_best_guess=current_best_guess,
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

        verification = verify_best_guess(instance, exec_parsed["best_guess"])
        exec_turn["verification"] = {
            "is_valid": verification.is_valid,
            "failure_reason": verification.failure_reason,
            "p_query_given_evidence": verification.p_query_given_evidence,
            "ordering_used": list(verification.ordering_used) if verification.ordering_used is not None else None,
            "peak_factor_size_self_report": verification.peak_factor_size_self_report,
            "true_peak_factor_size": verification.true_peak_factor_size,
            "gap_nats": verification.gap_nats,
        }
        turns.append(exec_turn)

        kept_as_best = False
        delta_gap_nats = None
        current_plan_state = exec_parsed["updated_plan_state"]
        if verification.is_valid and verification.gap_nats is not None:
            candidate_best_guess = {
                "p_query_given_evidence": verification.p_query_given_evidence,
                "ordering_used": list(verification.ordering_used or ()),
                "peak_factor_size_self_report": verification.peak_factor_size_self_report,
                "true_peak_factor_size": verification.true_peak_factor_size,
            }
            delta_gap_nats = (
                None if prior_best_gap_nats is None else prior_best_gap_nats - verification.gap_nats
            )
            if current_best_gap_nats is None or verification.gap_nats <= current_best_gap_nats:
                kept_as_best = True
                current_best_gap_nats = verification.gap_nats
                current_best_guess = candidate_best_guess
                final_quality_forecast = exec_parsed["quality_forecast"]
                valid_model_turns.append(turn_number)
            else:
                revised_best_guess_downward = True
        else:
            validity_failures += 1

        subtask_summaries.append(
            {
                "turn_index": turn_number,
                "subtask_id": exec_parsed["subtask_id"],
                "desc": next_sub["desc"],
                "p_solve": next_sub["p_solve"],
                "updated_plan_state": exec_parsed["updated_plan_state"],
                "decision": exec_parsed["decision"],
                "is_valid": verification.is_valid,
                "failure_reason": verification.failure_reason,
                "gap_nats": verification.gap_nats,
                "delta_gap_nats_from_prev_best": delta_gap_nats,
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
    brier = _gap_forecast_brier(atomic_forecast, current_best_gap_nats)
    final_quality_brier = _gap_forecast_brier(final_quality_forecast, current_best_gap_nats)
    score = _score_for_gap(current_best_gap_nats, total_wall_seconds)
    plan_stop_now_score = 0.0
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

    return {
        "model": model_name,
        "seed": instance.seed,
        "requested_total_variables": instance.requested_total_variables,
        "total_variables": instance.total_variables,
        "size_escalated": instance.size_escalated,
        "scale_note": instance.scale_note,
        "attempt_index": instance.attempt_index,
        "variables": [
            {
                "name": variable.name,
                "parents": list(variable.parents),
                "cpt_true_probs": list(variable.cpt_true_probs),
            }
            for variable in instance.variables
        ],
        "query_variable": instance.query_variable,
        "evidence": instance.evidence,
        "eliminable_variables": list(instance.eliminable_variables),
        "hidden_clusters": {name: list(values) for name, values in instance.hidden_clusters.items()},
        "bridge_variables": list(instance.bridge_variables),
        "decoy_variable": instance.decoy_variable,
        "heuristic_orderings": [
            {
                "name": "baseline",
                "ordering": list(instance.baseline_ordering),
                "peak_factor_size": instance.baseline_peak_factor_size,
            },
            *[
                {
                    "name": summary.name,
                    "ordering": list(summary.ordering),
                    "peak_factor_size": summary.peak_factor_size,
                }
                for summary in instance.heuristic_results
            ],
            {
                "name": instance.random_search_best.name,
                "ordering": list(instance.random_search_best.ordering),
                "peak_factor_size": instance.random_search_best.peak_factor_size,
            },
        ],
        "baseline_ordering": list(instance.baseline_ordering),
        "baseline_peak_factor_size": instance.baseline_peak_factor_size,
        "gold_ordering": list(instance.gold_ordering),
        "gold_peak_factor_size": instance.gold_peak_factor_size,
        "gold_source": instance.gold_source,
        "exact_posterior": instance.exact_posterior,
        "turns": turns,
        "subtask_summaries": subtask_summaries,
        "declared_elimination_axis": declared_axis,
        "declared_axis_rationale": declared_axis_rationale,
        "declared_ordering": declared_ordering,
        "initial_plan_state": plan_parsed["plan_state"] if plan_parsed is not None else None,
        "final_plan_state": current_plan_state,
        "atomic_forecast": atomic_forecast,
        "plan_continue_forecast": plan_continue_forecast,
        "final_quality_forecast": final_quality_forecast,
        "final_best_guess": current_best_guess,
        "final_p_query_given_evidence": None if current_best_guess is None else current_best_guess["p_query_given_evidence"],
        "final_ordering_used": None if current_best_guess is None else current_best_guess["ordering_used"],
        "final_peak_factor_size_self_report": None
        if current_best_guess is None
        else current_best_guess["peak_factor_size_self_report"],
        "final_true_peak_factor_size": None if current_best_guess is None else current_best_guess["true_peak_factor_size"],
        "gap_nats": current_best_gap_nats,
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
        "final_guess_valid": current_best_guess is not None,
        "validity_failure_count": validity_failures,
        "max_exec_turns_reached": max_exec_turns_reached,
        "valid_model_turns": valid_model_turns,
    }


def _gap_key(threshold: float) -> str:
    return f"p_gap_le_{str(threshold).replace('.', '_')}"


def _gap_forecast_brier(gap_forecast: dict[str, float] | None, actual_gap_nats: float | None) -> float | None:
    if gap_forecast is None:
        return None
    terms = []
    for threshold in GAP_THRESHOLDS:
        predicted = gap_forecast[_gap_key(threshold)]
        actual = float(actual_gap_nats is not None and actual_gap_nats <= threshold)
        terms.append((predicted - actual) ** 2)
    return sum(terms) / len(terms)


def _score_for_gap(gap_nats: float | None, wall_seconds: float) -> float:
    if gap_nats is None:
        return 0.0
    return max(0.0, 100.0 - 100.0 * gap_nats) - TIME_PENALTY * wall_seconds


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None
