from __future__ import annotations

import concurrent.futures
import copy
import math
import time
from typing import Any

from gemini_client import GeminiChatSession
from portfolio_problem import PreparedProblem
from prompt import build_system_prompt

MAX_TURNS = 10
WALL_BUDGET_S = 1800
COST_PER_SECOND = 0.05
TURN_TIMEOUT_CAP_S = 300
COUNTERFACTUAL_TIMEOUT_S = 300
TERMINATE_MARKER = "[[TERMINATE]]"


def run_main_loop(
    problems: list[PreparedProblem],
    model_name: str,
) -> tuple[GeminiChatSession, dict[str, Any]]:
    system_prompt = build_system_prompt(problems)
    session = GeminiChatSession(model_name, system_prompt, temperature=0.0)
    transcript_entries: list[dict[str, Any]] = [
        {
            "role": "system",
            "phase": "main",
            "text": system_prompt,
        }
    ]
    turn_records: list[dict[str, Any]] = []
    started_at = time.monotonic()
    stop_reason = "max_turns"
    error: dict[str, Any] | None = None

    for turn_number in range(1, MAX_TURNS + 1):
        elapsed_s = time.monotonic() - started_at
        remaining_s = WALL_BUDGET_S - elapsed_s
        if remaining_s <= 0:
            stop_reason = "wall_budget"
            break

        turn_prompt = _format_turn_prompt(turn_number, elapsed_s, remaining_s)
        transcript_entries.append(
            {
                "role": "user",
                "phase": "main",
                "turn": turn_number,
                "elapsed_before_s": elapsed_s,
                "remaining_before_s": remaining_s,
                "text": turn_prompt,
            }
        )
        timeout_s = _turn_timeout_s(remaining_s)

        try:
            response = _call_with_timeout(session, turn_prompt, timeout_s)
        except Exception as exc:
            stop_reason = "api_error"
            error = _error_payload("main", turn_number, exc)
            transcript_entries.append(
                {
                    "role": "error",
                    "phase": "main",
                    "turn": turn_number,
                    "text": error["message"],
                    "error": error,
                }
            )
            break

        assistant_entry = {
            "role": "assistant",
            "phase": "main",
            "turn": turn_number,
            "text": response["text"],
            "wall_seconds": response["wall_seconds"],
            "input_tokens": response["input_tokens"],
            "output_tokens": response["output_tokens"],
            "total_tokens": response["total_tokens"],
            "thinking_tokens": response["thinking_tokens"],
            "timed_out": response["timed_out"],
        }
        transcript_entries.append(assistant_entry)
        turn_records.append(
            {
                "turn": turn_number,
                "prompt": turn_prompt,
                **assistant_entry,
            }
        )

        if response["timed_out"]:
            stop_reason = "turn_timeout"
            error = {
                "phase": "main",
                "turn": turn_number,
                "type": "TimeoutError",
                "message": f"Turn {turn_number} timed out after {timeout_s}s",
            }
            transcript_entries.append(
                {
                    "role": "error",
                    "phase": "main",
                    "turn": turn_number,
                    "text": error["message"],
                    "error": error,
                }
            )
            break

        if TERMINATE_MARKER in response["text"]:
            stop_reason = "terminate_marker"
            break

    total_wall_seconds = time.monotonic() - started_at
    result = {
        "system_prompt": system_prompt,
        "transcript_entries": transcript_entries,
        "transcript_text": render_transcript(transcript_entries),
        "turns": turn_records,
        "turn_count": len(turn_records),
        "stop_reason": stop_reason,
        "error": error,
        "total_wall_seconds": total_wall_seconds,
        "total_input_tokens": _sum_numeric(turn_records, "input_tokens"),
        "total_output_tokens": _sum_numeric(turn_records, "output_tokens"),
        "total_tokens": _sum_numeric(turn_records, "total_tokens"),
        "total_thinking_tokens": _sum_numeric(turn_records, "thinking_tokens"),
    }
    return session, result


def run_counterfactual_turn(
    session: GeminiChatSession,
    base_result: dict[str, Any],
) -> dict[str, Any]:
    transcript_entries = copy.deepcopy(base_result["transcript_entries"])
    elapsed_s = float(base_result["total_wall_seconds"])
    turn_number = int(base_result["turn_count"]) + 1
    turn_prompt = _format_counterfactual_prompt(turn_number, elapsed_s)
    transcript_entries.append(
        {
            "role": "user",
            "phase": "counterfactual",
            "turn": turn_number,
            "elapsed_before_s": elapsed_s,
            "remaining_before_s": 0.0,
            "text": turn_prompt,
        }
    )

    error: dict[str, Any] | None = None
    try:
        response = _call_with_timeout(session, turn_prompt, COUNTERFACTUAL_TIMEOUT_S)
    except Exception as exc:
        error = _error_payload("counterfactual", turn_number, exc)
        transcript_entries.append(
            {
                "role": "error",
                "phase": "counterfactual",
                "turn": turn_number,
                "text": error["message"],
                "error": error,
            }
        )
        response = None

    branch_turn: dict[str, Any] | None = None
    if response is not None:
        branch_turn = {
            "role": "assistant",
            "phase": "counterfactual",
            "turn": turn_number,
            "text": response["text"],
            "wall_seconds": response["wall_seconds"],
            "input_tokens": response["input_tokens"],
            "output_tokens": response["output_tokens"],
            "total_tokens": response["total_tokens"],
            "thinking_tokens": response["thinking_tokens"],
            "timed_out": response["timed_out"],
        }
        transcript_entries.append(branch_turn)
        if response["timed_out"]:
            error = {
                "phase": "counterfactual",
                "turn": turn_number,
                "type": "TimeoutError",
                "message": f"Counterfactual turn timed out after {COUNTERFACTUAL_TIMEOUT_S}s",
            }
            transcript_entries.append(
                {
                    "role": "error",
                    "phase": "counterfactual",
                    "turn": turn_number,
                    "text": error["message"],
                    "error": error,
                }
            )

    return {
        "transcript_entries": transcript_entries,
        "transcript_text": render_transcript(transcript_entries),
        "turn": branch_turn,
        "error": error,
    }


def render_transcript(transcript_entries: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for entry in transcript_entries:
        role = str(entry["role"]).upper()
        phase = entry.get("phase")
        turn = entry.get("turn")
        header_parts = [role]
        if phase:
            header_parts.append(str(phase).upper())
        if turn is not None:
            header_parts.append(f"TURN {turn}")
        if entry.get("elapsed_before_s") is not None:
            header_parts.append(f"elapsed={float(entry['elapsed_before_s']):.2f}s")
        if entry.get("remaining_before_s") is not None:
            header_parts.append(f"remaining={float(entry['remaining_before_s']):.2f}s")
        if entry.get("wall_seconds") is not None:
            header_parts.append(f"wall={float(entry['wall_seconds']):.2f}s")
        for token_field in ("input_tokens", "output_tokens", "total_tokens", "thinking_tokens"):
            if entry.get(token_field) is not None:
                header_parts.append(f"{token_field}={entry[token_field]}")
        if entry.get("timed_out"):
            header_parts.append("timed_out=true")
        chunks.append(f"[{' | '.join(header_parts)}]\n{entry.get('text', '')}".rstrip())
    return "\n\n".join(chunks).strip() + "\n"


def _format_turn_prompt(turn_number: int, elapsed_s: float, remaining_s: float) -> str:
    return "\n".join(
        [
            f"Turn {turn_number} of {MAX_TURNS}.",
            f"Elapsed wall time: {elapsed_s:.1f}s.",
            f"Remaining wall budget: {remaining_s:.1f}s.",
            "Continue working across the four problems and revise your plan as needed.",
            "For any problem you update, emit your full current best candidate answer on its own line using exactly one of these prefixes:",
            'P1_ANSWER: {...}',
            'P2_ANSWER: {...}',
            'P3_ANSWER: [...]',
            'P4_ANSWER: {...}',
            "Reason freely elsewhere if useful.",
            "If helpful, add a brief estimate of how much net value one additional turn could still unlock. This is optional.",
        ]
    )


def _format_counterfactual_prompt(turn_number: int, elapsed_s: float) -> str:
    return "\n".join(
        [
            f"Forced continuation turn {turn_number}.",
            f"The main loop stopped after {elapsed_s:.1f}s of wall time.",
            "This is a counterfactual extra turn from the exact stop state.",
            "Produce your best candidate answers for any problem you can still improve.",
            "For any problem you update, emit your full current best candidate answer on its own line using the same P1_ANSWER / P2_ANSWER / P3_ANSWER / P4_ANSWER labels.",
            "This is your final turn.",
        ]
    )


def _turn_timeout_s(remaining_s: float) -> int:
    bounded = min(float(remaining_s), float(TURN_TIMEOUT_CAP_S))
    return max(10, int(math.ceil(bounded)))


def _call_with_timeout(
    session: GeminiChatSession,
    message: str,
    timeout_s: int,
) -> dict[str, Any]:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    start = time.monotonic()
    future = executor.submit(session.send, message, timeout_s)
    try:
        response = future.result(timeout=timeout_s + 5)
        response["timed_out"] = False
        return response
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


def _sum_numeric(items: list[dict[str, Any]], key: str) -> int | None:
    values = [item[key] for item in items if item.get(key) is not None]
    if not values:
        return None
    return int(sum(int(value) for value in values))


def _error_payload(phase: str, turn_number: int, exc: Exception) -> dict[str, Any]:
    return {
        "phase": phase,
        "turn": turn_number,
        "type": type(exc).__name__,
        "message": str(exc),
    }
