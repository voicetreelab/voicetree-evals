from __future__ import annotations

import ast
import json
import re
from typing import Any

TOTAL_BUDGET_S = 1800
PLAN_TURN_BUDGET_S = 300
SUBTASK_BUDGET_S = 600
CF_RESERVE_S = 300
MAX_EXEC_TURNS = 10
TIME_PENALTY = 0.01
SOLO_GAP_THRESHOLDS = (2.0, 5.0, 10.0)
VE_GAP_THRESHOLDS = (0.01, 0.1, 0.5)

_DECISION_RE = re.compile(
    r"^\s*\**\s*DECISION\**\s*:\s*\**\s*(continue|stop)\s*\**\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_SUB_RE = re.compile(
    r"^\s*\**\s*SUB_(\d+)\**\s*:\s*(.*?)(?=^\s*\**\s*[A-Z][A-Z0-9_]*\**\s*:|\Z)",
    re.DOTALL | re.MULTILINE,
)


def gap_thresholds_for_class(cls: str | None) -> tuple[float, ...]:
    if cls == "ve":
        return VE_GAP_THRESHOLDS
    return SOLO_GAP_THRESHOLDS


def _gap_key(threshold: float) -> str:
    return f"p_gap_le_{format(threshold, 'g').replace('.', '_')}"


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _extract_label_block(text: str, label: str) -> str | None:
    pattern = re.compile(
        rf"^\s*\**\s*{re.escape(label)}\**\s*:\s*(.*?)(?=^\s*\**\s*[A-Z][A-Z0-9_]*\**\s*:|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip()
    return value or None


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _parse_json_like(text: str | None) -> Any:
    if not text:
        return None

    stripped = _strip_code_fences(text)
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(stripped)
        except Exception:
            continue

    for opening, closing in (("{", "}"), ("[", "]")):
        depth = 0
        start = None
        for index, char in enumerate(stripped):
            if char == opening:
                if depth == 0:
                    start = index
                depth += 1
            elif char == closing:
                depth -= 1
                if depth == 0 and start is not None:
                    chunk = stripped[start : index + 1]
                    for parser in (json.loads, ast.literal_eval):
                        try:
                            return parser(chunk)
                        except Exception:
                            continue
                    return None
    return None


def _parse_object_loose(text: str | None) -> dict[str, Any] | None:
    parsed = _parse_json_like(text)
    return parsed if isinstance(parsed, dict) else None


def normalize_next_sub(next_sub: dict[str, Any] | None) -> dict[str, Any] | None:
    if not next_sub:
        return None

    try:
        sub_id = int(next_sub["id"])
    except Exception:
        return None

    desc = str(next_sub.get("desc", "")).strip()
    p_solve = _safe_float(next_sub.get("p_solve"))
    try:
        time_budget_s = int(next_sub.get("time_budget_s", SUBTASK_BUDGET_S))
    except Exception:
        time_budget_s = SUBTASK_BUDGET_S

    if not desc or p_solve is None or not 0.0 <= p_solve <= 1.0:
        return None

    return {
        "id": sub_id,
        "desc": desc,
        "p_solve": p_solve,
        "time_budget_s": max(1, min(time_budget_s, SUBTASK_BUDGET_S)),
    }


def _normalize_forecast(
    forecast: dict[str, Any] | None,
    *,
    thresholds: tuple[float, ...],
) -> dict[str, float] | None:
    if not forecast:
        return None

    normalized: dict[str, float] = {}
    for threshold in thresholds:
        key = _gap_key(threshold)
        value = _safe_float(forecast.get(key))
        if value is None or not 0.0 <= value <= 1.0:
            return None
        normalized[key] = value

    ordered = [normalized[_gap_key(threshold)] for threshold in thresholds]
    if ordered != sorted(ordered):
        return None

    return normalized


def parse_plan_state(text: str) -> str | None:
    return _extract_label_block(text, "PLAN_STATE")


def parse_updated_plan_state(text: str) -> str | None:
    return _extract_label_block(text, "UPDATED_PLAN_STATE")


def parse_best_guess(text: str) -> dict[str, Any] | None:
    return _parse_object_loose(_extract_label_block(text, "BEST_GUESS"))


def parse_decision(text: str) -> str | None:
    match = _DECISION_RE.search(text)
    if not match:
        return None
    return match.group(1).lower()


def parse_quality_forecast(
    text: str,
    *,
    cls: str | None = None,
    label: str = "QUALITY_FORECAST",
) -> dict[str, float] | None:
    return _normalize_forecast(
        _parse_object_loose(_extract_label_block(text, label)),
        thresholds=gap_thresholds_for_class(cls),
    )


def parse_continue_forecast(text: str) -> dict[str, float] | None:
    payload = _parse_object_loose(_extract_label_block(text, "CONTINUE_FORECAST"))
    if not payload:
        return None

    p_improve = _safe_float(
        payload.get("p_improve_if_one_more_subtask", payload.get("p_improve"))
    )
    expected_delta_score = _safe_float(payload.get("expected_delta_score"))
    expected_gap_reduction = _safe_float(payload.get("expected_gap_reduction"))

    if p_improve is None or expected_delta_score is None:
        return None
    if not 0.0 <= p_improve <= 1.0:
        return None

    result = {
        "p_improve": p_improve,
        "expected_delta_score": expected_delta_score,
    }
    if expected_gap_reduction is not None and expected_gap_reduction >= 0.0:
        result["expected_gap_reduction"] = expected_gap_reduction
    return result


def parse_next_sub(text: str) -> dict[str, Any] | None:
    return normalize_next_sub(_parse_object_loose(_extract_label_block(text, "NEXT_SUB")))


def parse_subtask_block(
    text: str,
    *,
    expected_subtask_id: int | None = None,
) -> tuple[int, str] | None:
    match = _SUB_RE.search(text)
    if not match:
        return None

    subtask_id = int(match.group(1))
    if expected_subtask_id is not None and subtask_id != expected_subtask_id:
        return None
    return subtask_id, match.group(2).strip()


def parse_plan_turn(text: str, *, cls: str | None = None) -> dict[str, Any] | None:
    plan_state = parse_plan_state(text)
    if plan_state is None:
        return None

    result: dict[str, Any] = {
        "plan_state": plan_state,
        "next_sub": parse_next_sub(text),
    }

    atomic_forecast = parse_quality_forecast(text, cls=cls, label="ATOMIC_FORECAST")
    if atomic_forecast is not None:
        result["atomic_forecast"] = atomic_forecast

    continue_forecast = parse_continue_forecast(text)
    if continue_forecast is not None:
        result["continue_forecast"] = continue_forecast

    decision = parse_decision(text)
    if decision is not None:
        result["decision"] = decision

    return result


def parse_exec_turn(
    text: str,
    *,
    cls: str | None = None,
    expected_subtask_id: int | None = None,
    require_decision: bool = True,
) -> dict[str, Any] | None:
    subtask = parse_subtask_block(text, expected_subtask_id=expected_subtask_id)
    best_guess = parse_best_guess(text)
    updated_plan_state = parse_updated_plan_state(text)
    quality_forecast = parse_quality_forecast(text, cls=cls)
    continue_forecast = parse_continue_forecast(text)
    decision = parse_decision(text)

    if (
        subtask is None
        or best_guess is None
        or updated_plan_state is None
        or quality_forecast is None
        or continue_forecast is None
        or (require_decision and decision is None)
    ):
        return None

    next_sub = parse_next_sub(text)
    if decision == "continue" and next_sub is None:
        return None

    subtask_id, subtask_body = subtask
    return {
        "subtask_id": subtask_id,
        "subtask_body": subtask_body,
        "best_guess": best_guess,
        "updated_plan_state": updated_plan_state,
        "quality_forecast": quality_forecast,
        "continue_forecast": continue_forecast,
        "decision": decision,
        "next_sub": next_sub,
    }


def parse_exec_turn_partial(
    text: str,
    *,
    cls: str | None = None,
    expected_subtask_id: int | None = None,
    require_decision: bool = True,
) -> dict[str, Any]:
    result: dict[str, Any] = {}

    subtask = parse_subtask_block(text, expected_subtask_id=expected_subtask_id)
    if subtask is not None:
        subtask_id, subtask_body = subtask
        result["subtask_id"] = subtask_id
        result["subtask_body"] = subtask_body

    best_guess = parse_best_guess(text)
    if best_guess is not None:
        result["best_guess"] = best_guess

    updated_plan_state = parse_updated_plan_state(text)
    if updated_plan_state is not None:
        result["updated_plan_state"] = updated_plan_state

    quality_forecast = parse_quality_forecast(text, cls=cls)
    if quality_forecast is not None:
        result["quality_forecast"] = quality_forecast

    continue_forecast = parse_continue_forecast(text)
    if continue_forecast is not None:
        result["continue_forecast"] = continue_forecast

    decision = parse_decision(text)
    if decision is not None:
        result["decision"] = decision

    next_sub = parse_next_sub(text)
    if next_sub is not None:
        result["next_sub"] = next_sub

    missing_or_invalid: list[str] = []
    if "subtask_id" not in result or "subtask_body" not in result:
        missing_or_invalid.append("subtask")
    for field in ("best_guess", "updated_plan_state", "quality_forecast", "continue_forecast"):
        if field not in result:
            missing_or_invalid.append(field)
    if require_decision and "decision" not in result:
        missing_or_invalid.append("decision")
    if decision == "continue" and "next_sub" not in result:
        missing_or_invalid.append("next_sub")

    result["missing_or_invalid"] = missing_or_invalid
    return result
