from __future__ import annotations

import ast
import concurrent.futures
import json
import re
import time
from typing import Any

from gemini_client import GeminiChatSession
from prompt import build_system_prompt
from steiner_coloring_instance import SteinerColoringInstance, solution_summary
from verify import verify_answer

TOTAL_BUDGET_S = 1800
SUBTASK_BUDGET_S = 600
PLAN_TURN_BUDGET_S = 300
MAX_EXEC_TURNS = 4
TIME_PENALTY = 0.01

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
    return None


def _lookup_key(mapping: dict[str, Any], *names: str) -> Any:
    upper_map = {str(key).strip().upper(): value for key, value in mapping.items()}
    for name in names:
        if name.upper() in upper_map:
            return upper_map[name.upper()]
    return None


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def normalize_next_sub(next_sub: dict[str, Any] | None) -> dict[str, Any] | None:
    if not next_sub:
        return None
    try:
        sub_id = int(next_sub["id"])
        time_budget_s = int(next_sub.get("time_budget_s", SUBTASK_BUDGET_S))
    except Exception:
        return None
    desc = str(next_sub.get("desc", "")).strip()
    if not desc:
        return None
    return {
        "id": sub_id,
        "desc": desc,
        "time_budget_s": max(1, min(time_budget_s, SUBTASK_BUDGET_S)),
    }


def parse_plan_turn(text: str) -> dict[str, Any] | None:
    next_sub = _parse_object_loose(_extract_label_block(text, "NEXT_SUB"))
    if next_sub is None:
        top_level = _parse_object_loose(text)
        if top_level is not None:
            next_sub = next_sub or _lookup_key(top_level, "NEXT_SUB")
    next_sub = normalize_next_sub(next_sub) if next_sub else None
    if next_sub is None:
        return None
    return {"next_sub": next_sub}


def parse_exec_turn(text: str, expected_subtask_id: int | None = None) -> dict[str, Any] | None:
    edges = _parse_list_loose(_extract_label_block(text, "EDGES"))
    frequencies = _parse_object_loose(_extract_label_block(text, "FREQUENCIES"))
    p_correct = _safe_float(_extract_label_block(text, "P_CORRECT"))
    decision_match = _DECISION_RE.search(text)
    next_sub = _parse_object_loose(_extract_label_block(text, "NEXT_SUB"))
    sub_match = _SUB_RE.search(text)
    subtask_id = int(sub_match.group(1)) if sub_match else None
    if edges is None or frequencies is None or p_correct is None or decision_match is None or sub_match is None:
        top_level = _parse_object_loose(text)
        if top_level is not None:
            answer_obj = _lookup_key(top_level, "ANSWER")
            if isinstance(answer_obj, dict):
                edges = edges or _lookup_key(answer_obj, "EDGES", "edges")
                frequencies = frequencies or _lookup_key(answer_obj, "FREQUENCIES", "frequencies")
            edges = edges or _lookup_key(top_level, "EDGES", "edges")
            frequencies = frequencies or _lookup_key(top_level, "FREQUENCIES", "frequencies")
            if p_correct is None:
                p_correct = _safe_float(_lookup_key(top_level, "P_CORRECT"))
            if decision_match is None:
                decision_candidate = _lookup_key(top_level, "DECISION")
                decision_text = str(decision_candidate).strip().lower() if decision_candidate is not None else None
                decision_match = re.match(r"^(continue|stop)$", decision_text or "")
            next_sub = next_sub or _lookup_key(top_level, "NEXT_SUB")
            if subtask_id is None:
                for key, value in top_level.items():
                    match = re.match(r"^SUB_(\d+)$", str(key).strip(), re.IGNORECASE)
                    if match:
                        subtask_id = int(match.group(1))
                        break
            if subtask_id is None and expected_subtask_id is not None:
                subtask_id = expected_subtask_id
    if edges is None or frequencies is None or p_correct is None or decision_match is None or subtask_id is None:
        return None
    if not 0.0 <= p_correct <= 1.0:
        return None
    if expected_subtask_id is not None and subtask_id != expected_subtask_id:
        return None
    decision = decision_match.group(1).lower()
    if decision == "continue" and next_sub is None:
        return None
    return {
        "subtask_id": subtask_id,
        "best_guess": {"edges": edges, "frequencies": frequencies},
        "p_correct": p_correct,
        "decision": decision,
        "next_sub": normalize_next_sub(next_sub) if next_sub else None,
    }


def format_turn1_prompt(instance: SteinerColoringInstance) -> str:
    return (
        f"{instance.problem_statement}\n"
        "Turn 1 is planning only. Do not emit EDGES or FREQUENCIES yet.\n"
        "Choose only the first execution subtask to run next.\n"
        "Keep it minimal.\n"
        "Do not restate the full problem setup in the subtask description.\n"
        "Use this exact output contract:\n"
        f'NEXT_SUB: {{"id": 1, "desc": "...", "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
        "The description should name the first concrete reasoning step only.\n"
        "Example style: compare a few promising terminal-connecting trees and account for frequency conflicts.\n"
    )


def format_exec_prompt(
    *,
    turn_number: int,
    previous_turn: dict[str, Any],
    elapsed_s: float,
    current_best_answer: dict[str, Any],
    current_best_source: str,
    current_best_cost: int,
    subtask_budget_s: int,
    instance: SteinerColoringInstance,
) -> str:
    remaining_s = max(0.0, TOTAL_BUDGET_S - elapsed_s)
    answer_json = json.dumps(current_best_answer, indent=2, sort_keys=True)
    prev_wall = previous_turn.get("wall_seconds")
    prev_input = previous_turn.get("input_tokens")
    prev_output = previous_turn.get("output_tokens")
    prev_total = previous_turn.get("total_tokens")
    return (
        f"TURN_{turn_number - 1} STATS: wall={prev_wall:.1f}s, input_tok={_fmt_token(prev_input)}, "
        f"output_tok={_fmt_token(prev_output)}, total_tok={_fmt_token(prev_total)}\n"
        f"CUMULATIVE: wall={elapsed_s:.1f}s / {TOTAL_BUDGET_S}s, remaining={remaining_s:.1f}s\n"
        f"SUBTASK BUDGET: {subtask_budget_s}s per turn (hard kill)\n"
        f"CURRENT_BEST_SOURCE: {current_best_source}\n"
        f"CURRENT_BEST_COST: {current_best_cost}\n"
        f"CURRENT_BEST_SUMMARY:\n{solution_summary(instance, current_best_answer, current_best_cost)}\n"
        f"CURRENT_BEST_JSON:\n{answer_json}\n"
        "Now execute NEXT_SUB.\n"
        "Use this exact output contract:\n"
        f"SUB_{turn_number - 1}: <work>\n"
        "ANSWER:\n"
        '  EDGES: [["Port", "Bay"], ["Bay", "Cliff"]]\n'
        '  FREQUENCIES: {"Port": 1, "Bay": 2, "Cliff": 1}\n'
        "P_CORRECT: <float>\n"
        "DECISION: continue | stop\n"
        f'NEXT_SUB: {{"id": {turn_number}, "desc": "...", "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
        "P_CORRECT means the probability that this answer is within 10 percent of optimum total cost.\n"
        "If DECISION is stop, omit NEXT_SUB.\n"
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


def run_protocol(instance: SteinerColoringInstance, model_name: str) -> dict[str, Any]:
    session = GeminiChatSession(
        model_name=model_name,
        system_instruction=build_system_prompt(),
    )
    run_start = time.monotonic()
    turns: list[dict[str, Any]] = []
    current_best_answer = instance.baseline_answer
    current_best_cost = instance.baseline_cost
    current_best_source = "baseline"
    final_answer_source = "baseline"
    final_p_correct: float | None = None
    turn1_died = False
    parse_fail = False
    subtask_killed_count = 0
    revised_best_guess_downward = False
    stop_reason = "unknown"
    next_sub: dict[str, Any] | None = None
    max_exec_turns_reached = False
    feasibility_failures = 0
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
                current_best_answer=current_best_answer,
                current_best_source=current_best_source,
                current_best_cost=current_best_cost,
                subtask_budget_s=next_sub["time_budget_s"],
                instance=instance,
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

        verification = verify_answer(instance, exec_parsed["best_guess"])
        exec_turn["verification"] = {
            "feasible": verification.feasible,
            "computed_cost": verification.computed_cost,
            "edge_cost": verification.edge_cost,
            "num_frequencies_used": verification.num_frequencies_used,
            "failure_reason": verification.failure_reason,
        }
        turns.append(exec_turn)

        if verification.feasible and verification.computed_cost is not None and verification.normalized_answer is not None:
            valid_model_turns.append(turn_number)
            if verification.computed_cost <= current_best_cost:
                if verification.computed_cost > current_best_cost:
                    revised_best_guess_downward = True
                current_best_answer = verification.normalized_answer
                current_best_cost = verification.computed_cost
                final_p_correct = exec_parsed["p_correct"]
                final_answer_source = "model"
                current_best_source = "model"
            else:
                revised_best_guess_downward = True
        else:
            feasibility_failures += 1
            if valid_model_turns:
                final_answer_source = "last_good_turn"
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

    if not valid_model_turns:
        final_answer_source = "baseline"

    total_wall_seconds = time.monotonic() - run_start
    baseline_gap_pct = (
        100.0 * (instance.baseline_cost - instance.optimal_cost) / instance.optimal_cost
        if instance.optimal_cost is not None
        else None
    )
    cable_only_gap_pct = (
        100.0 * (instance.cable_only_cost - instance.optimal_cost) / instance.optimal_cost
        if instance.cable_only_cost is not None and instance.optimal_cost is not None
        else None
    )
    gap_pct = (
        100.0 * (current_best_cost - instance.optimal_cost) / instance.optimal_cost
        if instance.optimal_cost is not None
        else None
    )
    score = _score_for_gap(gap_pct, total_wall_seconds) if gap_pct is not None else None
    p_correct_event = (gap_pct <= 10.0) if gap_pct is not None else None
    p_correct_brier = (
        (final_p_correct - float(p_correct_event)) ** 2
        if final_p_correct is not None and p_correct_event is not None
        else None
    )
    baseline_improvement_pct = (
        100.0 * (instance.baseline_cost - current_best_cost) / instance.baseline_cost
        if instance.baseline_cost > 0
        else None
    )

    return {
        "model": model_name,
        "seed": instance.seed,
        "n": instance.n,
        "k": instance.k,
        "villages": list(instance.villages),
        "terminals": list(instance.terminals),
        "edges": [{"u": edge.u, "v": edge.v, "cost": edge.cost} for edge in instance.edges],
        "interference_pairs": [list(pair) for pair in instance.interference_pairs],
        "baseline_answer": instance.baseline_answer,
        "baseline_cost": instance.baseline_cost,
        "baseline_gap_pct": baseline_gap_pct,
        "cable_only_answer": instance.cable_only_answer,
        "cable_only_cost": instance.cable_only_cost,
        "cable_only_gap_pct": cable_only_gap_pct,
        "optimal_answer": instance.optimal_answer,
        "optimal_cost": instance.optimal_cost,
        "joint_reasoning_gain": (
            instance.cable_only_cost - instance.optimal_cost
            if instance.cable_only_cost is not None and instance.optimal_cost is not None
            else None
        ),
        "turns": turns,
        "atomic_prediction": None,
        "declared_gap": None,
        "declared_gap_error": None,
        "final_p_correct": final_p_correct,
        "p_correct_brier": p_correct_brier,
        "p_correct_target_gap_pct": 10.0,
        "final_answer": current_best_answer,
        "final_cost": current_best_cost,
        "baseline_improvement_pct": baseline_improvement_pct,
        "gap_pct": gap_pct,
        "score": score,
        "total_wall_seconds": total_wall_seconds,
        "turn_count": len(turns),
        "turn1_died": turn1_died,
        "subtask_killed_count": subtask_killed_count,
        "stop_reason": stop_reason,
        "parse_fail": parse_fail,
        "revised_best_guess_downward": revised_best_guess_downward,
        "final_answer_feasible": True,
        "final_answer_source": final_answer_source,
        "feasibility_failure_count": feasibility_failures,
        "max_exec_turns_reached": max_exec_turns_reached,
        "valid_model_turns": valid_model_turns,
    }


def _score_for_gap(gap_pct: float, wall_seconds: float) -> float:
    return max(0.0, 100.0 - gap_pct) - TIME_PENALTY * wall_seconds
