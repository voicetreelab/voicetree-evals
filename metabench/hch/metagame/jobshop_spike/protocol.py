from __future__ import annotations

import ast
import concurrent.futures
import json
import re
import time
from typing import Any

from gemini_client import GeminiChatSession
from jobshop_spike.jobshop_instance import FlowshopInstance, flowshop_makespan
from jobshop_spike.prompt import build_system_prompt
from jobshop_spike.render_nl import render_problem

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
_SUB_RE = re.compile(
    r"^\s*\**\s*SUB_(\d+)\**\s*:\s*(.*?)(?=^\s*\**\s*[A-Z][A-Z0-9_]*\**\s*:|\Z)",
    re.DOTALL | re.MULTILINE,
)
_CODE_FENCE_RE = re.compile(r"```(?:python)?", re.IGNORECASE)


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
    text = text.strip()
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


def _parse_array_loose(text: str | None) -> list[Any] | None:
    if not text:
        return None
    text = text.strip()
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


def parse_best_guess(text: str | None, n_jobs: int) -> list[int] | None:
    if not text:
        return None
    target = list(range(1, n_jobs + 1))
    values = _parse_array_loose(text)
    if values is not None:
        try:
            sequence = [int(value) for value in values]
        except Exception:
            sequence = None
        else:
            if sorted(sequence) == target:
                return sequence

    normalized = re.sub(r"(?i)\b(order|orders|job|jobs)\b", " ", text)
    normalized = normalized.replace("#", " ")
    normalized = normalized.replace("->", ",")
    normalized = normalized.replace("→", ",")
    normalized = normalized.replace(">", ",")
    numbers = [int(match) for match in re.findall(r"\d+", normalized)]

    if len(numbers) == n_jobs and sorted(numbers) == target:
        return numbers

    for start in range(0, max(0, len(numbers) - n_jobs + 1)):
        window = numbers[start : start + n_jobs]
        if sorted(window) == target:
            return window
    return None


def _detect_solver_markers(text: str) -> list[str]:
    markers: list[str] = []
    lowered = text.lower()
    if _CODE_FENCE_RE.search(text):
        markers.append("code_fence")
    if re.search(r"\bdef\s+\w+\s*\(", text):
        markers.append("python_def")
    if re.search(r"\bimport\s+\w+", text):
        markers.append("import")
    if "itertools" in lowered:
        markers.append("itertools")
    if re.search(r"\bfor\s+\w+\s+in\s+range\(", text):
        markers.append("for_range")
    if "python" in lowered:
        markers.append("python_word")
    return markers


def _looks_like_solver_attempt(markers: list[str]) -> bool:
    strong = {"code_fence", "python_def", "import", "itertools", "for_range"}
    strong_hits = [marker for marker in markers if marker in strong]
    return bool(strong_hits) or len(markers) >= 2


def parse_plan_turn(text: str) -> dict[str, Any] | None:
    atomic = _parse_object_loose(_extract_label_block(text, "ATOMIC_PREDICTION"))
    declared_gap = _extract_float(text, "DECLARED_GAP")
    decision_match = _DECISION_RE.search(text)
    decision = decision_match.group(1).lower() if decision_match else None
    next_sub = _parse_object_loose(_extract_label_block(text, "NEXT_SUB"))
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


def parse_exec_turn(text: str, n_jobs: int, expected_subtask_id: int | None = None) -> dict[str, Any] | None:
    best_guess_text = _extract_label_block(text, "BEST_GUESS")
    best_guess = parse_best_guess(best_guess_text, n_jobs=n_jobs)
    p_correct = _extract_float(text, "P_CORRECT")
    decision_match = _DECISION_RE.search(text)
    decision = decision_match.group(1).lower() if decision_match else None
    next_sub = _parse_object_loose(_extract_label_block(text, "NEXT_SUB"))
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


def format_turn1_prompt(instance: FlowshopInstance) -> str:
    return (
        f"{render_problem(instance)}\n"
        "Turn 1 is planning only. Do not solve the schedule. Do not emit a BEST_GUESS yet.\n"
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
    baseline_order: tuple[int, ...] | list[int],
    baseline_makespan: int,
    subtask_budget_s: int,
    n_jobs: int,
) -> str:
    remaining_s = max(0.0, TOTAL_BUDGET_S - elapsed_s)
    prev_input = previous_turn.get("input_tokens")
    prev_output = previous_turn.get("output_tokens")
    prev_wall = previous_turn.get("wall_seconds")
    prev_total = previous_turn.get("total_tokens")
    baseline_text = ", ".join(str(job_id) for job_id in baseline_order)
    return (
        f"TURN_{turn_number - 1} STATS: wall={prev_wall:.1f}s, "
        f"input_tok={_fmt_token(prev_input)}, output_tok={_fmt_token(prev_output)}, cost=$NA\n"
        f"CUMULATIVE: wall={elapsed_s:.1f}s / {TOTAL_BUDGET_S}s, cost=$NA\n"
        f"LOCAL_USAGE: total_tok={_fmt_token(prev_total)}, remaining={remaining_s:.1f}s\n"
        f"SUBTASK BUDGET: {subtask_budget_s}s per turn (hard kill).\n"
        f"BASELINE_SEQUENCE: {baseline_text}\n"
        f"BASELINE_MAKESPAN: {baseline_makespan}\n"
        "Now execute NEXT_SUB.\n"
        "Use this exact output contract:\n"
        f"SUB_{turn_number - 1}: <work>\n"
        "BEST_GUESS: <full ordered job list such as 2, 5, 1, 7, ...>\n"
        "P_CORRECT: <float>\n"
        "DECISION: continue | stop\n"
        f'NEXT_SUB: {{"id": {turn_number}, "desc": "...", "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
        "If DECISION is stop, omit NEXT_SUB.\n"
        f"Use every job number from 1 to {n_jobs} exactly once in BEST_GUESS.\n"
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


def run_protocol(instance: FlowshopInstance, model_name: str) -> dict[str, Any]:
    session = GeminiChatSession(
        model_name=model_name,
        system_instruction=build_system_prompt(),
    )
    run_start = time.monotonic()
    turns: list[dict[str, Any]] = []
    last_best_guess = list(instance.baseline_order)
    last_best_makespan = instance.baseline_makespan
    declared_gap = None
    turn1_died = False
    parse_fail = False
    subtask_killed_count = 0
    revised_best_guess_downward = False
    stop_reason = "unknown"
    next_sub: dict[str, Any] | None = None

    plan_response = _call_with_timeout(
        session,
        format_turn1_prompt(instance),
        PLAN_TURN_BUDGET_S,
    )
    plan_markers = _detect_solver_markers(plan_response["text"])
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
        "solver_markers": plan_markers,
        "solver_attempt_detected": _looks_like_solver_attempt(plan_markers),
    }
    turns.append(plan_turn)

    if plan_response["timed_out"] or plan_parsed is None:
        turn1_died = True
        if not plan_response["timed_out"]:
            parse_fail = True
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
                instance.baseline_order,
                instance.baseline_makespan,
                next_sub["time_budget_s"],
                instance.n_jobs,
            ),
            next_sub["time_budget_s"],
        )
        exec_markers = _detect_solver_markers(exec_response["text"])
        exec_parsed = (
            None
            if exec_response["timed_out"]
            else parse_exec_turn(
                exec_response["text"],
                n_jobs=instance.n_jobs,
                expected_subtask_id=next_sub["id"],
            )
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
            "solver_markers": exec_markers,
            "solver_attempt_detected": _looks_like_solver_attempt(exec_markers),
        }
        turns.append(exec_turn)

        if exec_response["timed_out"]:
            subtask_killed_count += 1
            stop_reason = "subtask_timeout"
            break

        if exec_parsed is None:
            parse_fail = True
            stop_reason = "subtask_parse_fail"
            break

        candidate_guess = exec_parsed["best_guess"]
        candidate_makespan = flowshop_makespan(instance.jobs, candidate_guess)
        if candidate_makespan > last_best_makespan:
            revised_best_guess_downward = True
        last_best_guess = candidate_guess
        last_best_makespan = candidate_makespan

        if exec_parsed["decision"] == "stop":
            stop_reason = "subtask_stop"
            break

        next_sub = exec_parsed["next_sub"]
        turn_number += 1

    if stop_reason == "unknown":
        stop_reason = "total_budget_exhausted"

    total_wall_seconds = time.monotonic() - run_start
    final_guess = last_best_guess or list(instance.baseline_order)
    final_makespan = flowshop_makespan(instance.jobs, final_guess)
    gap_pct = 100.0 * (final_makespan - instance.gold_makespan) / instance.gold_makespan
    brier = None if declared_gap is None else (declared_gap - gap_pct) ** 2
    score = ACCURACY_REWARD * max(0.0, 100.0 - gap_pct) - TIME_PENALTY * total_wall_seconds
    solver_turns = [
        turn["turn_index"]
        for turn in turns
        if turn.get("solver_attempt_detected")
    ]
    next_sub_descs = [
        turn["parsed"]["next_sub"]["desc"]
        for turn in turns
        if turn.get("parsed") and turn["parsed"].get("next_sub")
    ]
    decisions = [
        turn["parsed"]["decision"]
        for turn in turns
        if turn.get("parsed") and turn["parsed"].get("decision")
    ]

    return {
        "model": model_name,
        "arm": "canonical_smart",
        "seed": instance.seed,
        "n_jobs": instance.n_jobs,
        "jobs": [
            {
                "job_id": job.job_id,
                "prep_minutes": job.prep_minutes,
                "finish_minutes": job.finish_minutes,
            }
            for job in instance.jobs
        ],
        "baseline_order": list(instance.baseline_order),
        "baseline_makespan": instance.baseline_makespan,
        "gold_order": list(instance.gold_order),
        "gold_makespan": instance.gold_makespan,
        "turns": turns,
        "declared_gap": declared_gap,
        "final_guess": final_guess,
        "final_makespan": final_makespan,
        "gap_pct": gap_pct,
        "brier": brier,
        "score": score,
        "total_wall_seconds": total_wall_seconds,
        "turn1_died": turn1_died,
        "parse_fail": parse_fail,
        "subtask_killed_count": subtask_killed_count,
        "revised_best_guess_downward": revised_best_guess_downward,
        "stop_reason": stop_reason,
        "stop_turn": turns[-1]["turn_index"],
        "decision_trace": decisions,
        "next_sub_descs": next_sub_descs,
        "solver_attempt_detected": bool(solver_turns),
        "solver_attempt_turns": solver_turns,
        "solver_attempt_markers": sorted(
            {
                marker
                for turn in turns
                for marker in turn.get("solver_markers", [])
            }
        ),
    }
