from __future__ import annotations

import ast
import concurrent.futures
import json
import re
import time
from typing import Any

from arms import build_system_prompt
from gemini_client import GeminiChatSession
from tsp_instance import TSPInstance, tour_length

TOTAL_BUDGET_S = 1800
SUBTASK_BUDGET_S = 600
PLAN_TURN_BUDGET_S = 300
ACCURACY_REWARD = 1.0
TIME_PENALTY = 0.01

_FLOAT_PATTERN = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
_DECISION_RE = re.compile(
    r"^\s*\**\s*DECISION\**\s*:\s*\**\s*(continue|stop)\s*\**\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_SUB_RE = re.compile(r"^\s*\**\s*SUB_(\d+)\**\s*:\s*(.*?)(?=^\s*\**\s*[A-Z][A-Z0-9_]*\**\s*:|\Z)", re.DOTALL | re.MULTILINE)


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


def _parse_json_object_loose(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    text = text.strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except Exception:
        pass

    depth = 0
    start = None
    for idx, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = idx
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    value = json.loads(text[start : idx + 1])
                except Exception:
                    return None
                return value if isinstance(value, dict) else None
    return None


def _parse_json_array_loose(text: str | None) -> list[Any] | None:
    if not text:
        return None
    text = text.strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, list) else None
    except Exception:
        pass

    depth = 0
    start = None
    for idx, ch in enumerate(text):
        if ch == "[":
            if depth == 0:
                start = idx
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0 and start is not None:
                chunk = text[start : idx + 1]
                for parser in (json.loads, ast.literal_eval):
                    try:
                        value = parser(chunk)
                    except Exception:
                        continue
                    return value if isinstance(value, list) else None
                return None
    return None


def parse_tour(text: str | None, n_cities: int = 25) -> list[int] | None:
    values = _parse_json_array_loose(text)
    if values is None:
        return None
    if len(values) != n_cities:
        return None
    try:
        tour = [int(v) for v in values]
    except Exception:
        return None
    if sorted(tour) != list(range(n_cities)):
        return None
    return tour


def parse_plan_turn(text: str) -> dict[str, Any] | None:
    atomic = _parse_json_object_loose(_extract_label_block(text, "ATOMIC_PREDICTION"))
    declared_gap = _extract_float(text, "DECLARED_GAP")
    decision_match = _DECISION_RE.search(text)
    decision = decision_match.group(1).lower() if decision_match else None
    next_sub = _parse_json_object_loose(_extract_label_block(text, "NEXT_SUB"))

    if atomic is None or declared_gap is None or decision is None:
        return None
    if decision == "continue" and next_sub is None:
        return None
    return {
        "atomic_prediction": atomic,
        "declared_gap": declared_gap,
        "decision": decision,
        "next_sub": normalize_next_sub(next_sub) if next_sub else None,
    }


def parse_exec_turn(text: str, expected_subtask_id: int | None = None) -> dict[str, Any] | None:
    best_guess_text = _extract_label_block(text, "BEST_GUESS")
    best_guess = parse_tour(best_guess_text)
    p_correct = _extract_float(text, "P_CORRECT")
    decision_match = _DECISION_RE.search(text)
    decision = decision_match.group(1).lower() if decision_match else None
    next_sub = _parse_json_object_loose(_extract_label_block(text, "NEXT_SUB"))
    sub_match = _SUB_RE.search(text)
    subtask_id = int(sub_match.group(1)) if sub_match else None

    if best_guess is None or p_correct is None or decision is None or subtask_id is None:
        return None
    if expected_subtask_id is not None and subtask_id != expected_subtask_id:
        return None
    if decision == "continue" and next_sub is None:
        return None
    return {
        "subtask_id": subtask_id,
        "best_guess": best_guess,
        "p_correct": p_correct,
        "decision": decision,
        "next_sub": normalize_next_sub(next_sub) if next_sub else None,
    }


def normalize_next_sub(next_sub: dict[str, Any] | None) -> dict[str, Any] | None:
    if not next_sub:
        return None
    try:
        sub_id = int(next_sub["id"])
    except Exception:
        sub_id = None
    desc = str(next_sub.get("desc", "")).strip()
    try:
        time_budget_s = int(next_sub.get("time_budget_s", SUBTASK_BUDGET_S))
    except Exception:
        time_budget_s = SUBTASK_BUDGET_S
    if sub_id is None or not desc:
        return None
    return {
        "id": sub_id,
        "desc": desc,
        "time_budget_s": max(1, min(time_budget_s, SUBTASK_BUDGET_S)),
    }


def format_turn1_prompt(instance: TSPInstance) -> str:
    return (
        f"{instance.problem_statement()}\n"
        "Turn 1 is planning only. Do not solve the TSP. Do not emit a tour.\n"
        "Estimate what would happen if you answered atomically, then decide whether to continue.\n"
        "Use this exact output contract:\n"
        'ATOMIC_PREDICTION: {"words_if_atomic": int, "p_correct_if_atomic": float}\n'
        "DECLARED_GAP: <float>\n"
        "DECISION: continue | stop\n"
        f'NEXT_SUB: {{"id": 1, "desc": "...", "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
        "If DECISION is stop, omit NEXT_SUB.\n"
    )


def format_exec_prompt(
    turn_number: int,
    previous_turn: dict[str, Any],
    elapsed_s: float,
    baseline_tour: list[int],
    subtask_budget_s: int,
) -> str:
    remaining_s = max(0.0, TOTAL_BUDGET_S - elapsed_s)
    prev_input = previous_turn.get("input_tokens")
    prev_output = previous_turn.get("output_tokens")
    prev_wall = previous_turn.get("wall_seconds")
    prev_total = previous_turn.get("total_tokens")

    return (
        f"TURN_{turn_number - 1} STATS: wall={prev_wall:.1f}s, "
        f"input_tok={_fmt_token(prev_input)}, output_tok={_fmt_token(prev_output)}, "
        "cost=$NA\n"
        f"CUMULATIVE: wall={elapsed_s:.1f}s / {TOTAL_BUDGET_S}s, cost=$NA\n"
        f"LOCAL_USAGE: total_tok={_fmt_token(prev_total)}, remaining={remaining_s:.1f}s\n"
        f"SUBTASK BUDGET: {subtask_budget_s}s per turn (hard kill).\n"
        f"BASELINE_TOUR: {baseline_tour}\n"
        "Now execute NEXT_SUB.\n"
        "Use this exact output contract:\n"
        f"SUB_{turn_number - 1}: <work>\n"
        "BEST_GUESS: <full JSON array tour>\n"
        "P_CORRECT: <float>\n"
        "DECISION: continue | stop\n"
        f'NEXT_SUB: {{"id": {turn_number}, "desc": "...", "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
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


def run_protocol(instance: TSPInstance, model_name: str, arm: str) -> dict[str, Any]:
    session = GeminiChatSession(
        model_name=model_name,
        system_instruction=build_system_prompt(arm),
    )
    run_start = time.monotonic()
    baseline_tour = list(instance.baseline_tour)
    baseline_length = instance.baseline_length
    turns: list[dict[str, Any]] = []
    last_best_guess = baseline_tour
    last_best_length = baseline_length
    declared_gap = None
    turn1_died = False
    subtask_killed_count = 0
    revised_best_guess_downward = False
    stop_reason = "unknown"
    next_sub: dict[str, Any] | None = None

    plan_response = _call_with_timeout(
        session,
        format_turn1_prompt(instance),
        PLAN_TURN_BUDGET_S,
    )
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
        stop_reason = "turn1_died"
    else:
        declared_gap = plan_parsed["declared_gap"]
        if plan_parsed["decision"] == "stop":
            stop_reason = "turn1_stop"
        else:
            next_sub = plan_parsed["next_sub"]

    turn_number = 2
    while (
        next_sub is not None
        and stop_reason == "unknown"
        and (time.monotonic() - run_start) < TOTAL_BUDGET_S
    ):
        elapsed_s = time.monotonic() - run_start
        exec_response = _call_with_timeout(
            session,
            format_exec_prompt(
                turn_number,
                turns[-1],
                elapsed_s,
                baseline_tour,
                next_sub["time_budget_s"],
            ),
            next_sub["time_budget_s"],
        )
        exec_parsed = (
            None
            if exec_response["timed_out"]
            else parse_exec_turn(exec_response["text"], expected_subtask_id=next_sub["id"])
        )
        exec_turn = {
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
        turns.append(exec_turn)

        if exec_response["timed_out"]:
            subtask_killed_count += 1
            stop_reason = "subtask_timeout"
            break

        if exec_parsed is None:
            stop_reason = "subtask_parse_fail"
            break

        candidate_tour = exec_parsed["best_guess"]
        candidate_length = tour_length(instance.coords, candidate_tour)
        if candidate_length > last_best_length + 1e-9:
            revised_best_guess_downward = True
        last_best_guess = candidate_tour
        last_best_length = candidate_length

        if exec_parsed["decision"] == "stop":
            stop_reason = "subtask_stop"
            break

        next_sub = exec_parsed["next_sub"]
        turn_number += 1

    if stop_reason == "unknown":
        stop_reason = "total_budget_exhausted"

    total_wall_seconds = time.monotonic() - run_start
    final_tour = last_best_guess or baseline_tour
    final_length = tour_length(instance.coords, final_tour)
    gap_pct = 100.0 * (final_length - instance.gold_length) / instance.gold_length
    brier = None if declared_gap is None else (declared_gap - gap_pct) ** 2
    score = ACCURACY_REWARD * max(0.0, 100.0 - gap_pct) - TIME_PENALTY * total_wall_seconds

    return {
        "model": model_name,
        "arm": arm,
        "seed": instance.seed,
        "coords": [list(coord) for coord in instance.coords],
        "baseline_tour": list(instance.baseline_tour),
        "baseline_length": baseline_length,
        "gold_tour": list(instance.gold_tour),
        "gold_length": instance.gold_length,
        "turns": turns,
        "declared_gap": declared_gap,
        "final_tour": final_tour,
        "final_length": final_length,
        "gap_pct": gap_pct,
        "brier": brier,
        "score": score,
        "total_wall_seconds": total_wall_seconds,
        "turn1_died": turn1_died,
        "subtask_killed_count": subtask_killed_count,
        "revised_best_guess_downward": revised_best_guess_downward,
        "stop_reason": stop_reason,
    }
