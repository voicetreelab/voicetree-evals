from __future__ import annotations

import json
from typing import Any

from gemini_client import GeminiChatSession
from portfolio_problem import PreparedProblem

DEFAULT_EXTRACTOR_MODEL = "gemini-2.5-flash"
EXTRACTOR_TIMEOUT_S = 180
EXTRACTOR_SYSTEM_PROMPT = (
    "You extract structured JSON from transcripts. "
    "Return only valid JSON and no markdown."
)


def extract_problem_answers(
    problems: list[PreparedProblem],
    transcript_text: str,
    *,
    model_name: str = DEFAULT_EXTRACTOR_MODEL,
) -> dict[str, dict[str, Any]]:
    return {
        problem.problem_id: _extract_problem_answer(
            problem,
            transcript_text,
            model_name=model_name,
        )
        for problem in problems
    }


def extract_session_metrics(
    transcript_text: str,
    *,
    model_name: str = DEFAULT_EXTRACTOR_MODEL,
) -> dict[str, Any]:
    prompt = f"""Transcript below. Extract:
- turn_count: number of distinct assistant turns with non-empty content
- subtasks_executed: distinct subtasks the model actually worked on, not just planned
- problems_attempted: subset of ["P1", "P2", "P3", "P4"] for which the model produced any candidate answer
- plan_evolution_summary: one sentence on whether the plan changed across turns
- declared_stop_reason: did the model ever say it wanted to stop, or did it just run to budget / turn cap?
- declared_one_more_turn_value_estimate: numeric estimate of additional net value from one more turn if the model explicitly gave one, else null
- declared_one_more_turn_notes: one short sentence describing that forecast evidence, else ""

Output ONLY valid JSON with exactly these keys.

Transcript:
<<<
{transcript_text}
>>>
"""
    response = _run_extractor(prompt, model_name=model_name)
    parsed, parse_error = _strict_json_loads(response["text"])
    if not isinstance(parsed, dict):
        return {
            **response,
            "json_valid": False,
            "parse_error": parse_error or "extractor did not return a JSON object",
            "turn_count": None,
            "subtasks_executed": None,
            "problems_attempted": [],
            "plan_evolution_summary": None,
            "declared_stop_reason": None,
            "declared_one_more_turn_value_estimate": None,
            "declared_one_more_turn_notes": None,
        }

    problems_attempted = parsed.get("problems_attempted")
    if not isinstance(problems_attempted, list):
        problems_attempted = []

    return {
        **response,
        "json_valid": True,
        "parse_error": None,
        "turn_count": _as_int(parsed.get("turn_count")),
        "subtasks_executed": _as_int(parsed.get("subtasks_executed")),
        "problems_attempted": [
            str(problem_id).strip().upper()
            for problem_id in problems_attempted
            if str(problem_id).strip().upper() in {"P1", "P2", "P3", "P4"}
        ],
        "plan_evolution_summary": _as_text(parsed.get("plan_evolution_summary")),
        "declared_stop_reason": _as_text(parsed.get("declared_stop_reason")),
        "declared_one_more_turn_value_estimate": _as_float(
            parsed.get("declared_one_more_turn_value_estimate")
        ),
        "declared_one_more_turn_notes": _as_text(
            parsed.get("declared_one_more_turn_notes")
        ),
    }


def _extract_problem_answer(
    problem: PreparedProblem,
    transcript_text: str,
    *,
    model_name: str,
) -> dict[str, Any]:
    prompt = f"""Below is a transcript of an AI attempting problem {problem.problem_id} ({problem.short_label}).
Extract the AI's FINAL candidate answer for this problem: the latest best attempt.
If no candidate answer is present, return {{"missing": true, "notes": "..."}}.
Expected schema hint for {problem.problem_id}: {problem.answer_contract}
Output ONLY valid JSON of one of these forms:
- {{"answer": <extracted>, "notes": "<1-line summary of what was extracted>"}}
- {{"missing": true, "notes": "<1-line summary of why no answer was found>"}}

Transcript:
<<<
{transcript_text}
>>>
"""
    response = _run_extractor(prompt, model_name=model_name)
    parsed, parse_error = _strict_json_loads(response["text"])
    if not isinstance(parsed, dict):
        return {
            **response,
            "json_valid": False,
            "parse_error": parse_error or "extractor did not return a JSON object",
            "missing": True,
            "answer": None,
            "notes": None,
        }

    missing = bool(parsed.get("missing"))
    return {
        **response,
        "json_valid": True,
        "parse_error": None,
        "missing": missing,
        "answer": None if missing else parsed.get("answer"),
        "notes": _as_text(parsed.get("notes")),
    }


def _run_extractor(prompt: str, *, model_name: str) -> dict[str, Any]:
    session = GeminiChatSession(model_name, EXTRACTOR_SYSTEM_PROMPT, temperature=0.0)
    response = session.send(prompt, EXTRACTOR_TIMEOUT_S)
    return {
        "model": model_name,
        "raw_text": response["text"],
        "wall_seconds": response["wall_seconds"],
        "input_tokens": response["input_tokens"],
        "output_tokens": response["output_tokens"],
        "total_tokens": response["total_tokens"],
        "thinking_tokens": response["thinking_tokens"],
        "text": response["text"],
    }


def _strict_json_loads(raw_text: str) -> tuple[Any | None, str | None]:
    text = raw_text.strip()
    if not text:
        return None, "empty response"
    try:
        return json.loads(text), None
    except json.JSONDecodeError as exc:
        return (
            None,
            f"invalid JSON at line {exc.lineno} column {exc.colno}: {exc.msg}",
        )


def _as_int(value: Any) -> int | None:
    try:
        return int(value)
    except Exception:
        return None


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
