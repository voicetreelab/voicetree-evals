from __future__ import annotations

import concurrent.futures
import json
import time
from typing import Any

from gemini_client import GeminiChatSession
from portfolio_problem import PreparedProblem, forecast_event_map
from prompt import build_system_prompt

TOTAL_BUDGET_S = 1800
PLAN_TURN_BUDGET_S = 300
MAX_SUBTASK_BUDGET_S = 600
MAX_EXEC_TURNS = 8
COST_PER_SECOND = 0.05
FORECAST_KEYS = ("p_within_5pct", "p_within_10pct", "p_within_20pct", "p_within_50pct")
STOP_TOKENS = {"stop_economic", "stop_budget"}
REALIZED_BUCKETS = {"within_5pct", "within_10pct", "within_20pct", "within_50pct", "miss"}
PROBLEM_IDS = ("P1", "P2", "P3", "P4")


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _normalize_forecast(raw: dict[str, Any]) -> dict[str, float] | None:
    upper_map = {str(key).strip().lower(): value for key, value in raw.items()}
    normalized: dict[str, float] = {}
    for key in FORECAST_KEYS:
        value = _safe_float(upper_map.get(key.lower()))
        if value is None or not 0.0 <= value <= 1.0:
            return None
        normalized[key] = value
    ordered = [normalized[key] for key in FORECAST_KEYS]
    if ordered != sorted(ordered):
        return None
    return normalized


def _parse_candidate_answer_json(raw: Any) -> dict[str, Any] | list[Any] | None:
    if not isinstance(raw, str):
        return None
    stripped = raw.strip()
    if not stripped:
        return None
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, (dict, list)):
        return None
    return parsed


def _normalize_next_sub_id(raw: Any) -> int | str | None:
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str):
        stripped = raw.strip()
        if stripped in STOP_TOKENS:
            return stripped
        if stripped.isdigit():
            return int(stripped)
    return None


def _normalize_plan_item(
    raw: dict[str, Any],
    *,
    prior: dict[str, Any] | None,
    require_status: bool,
    allowed_problem_ids: set[str],
) -> dict[str, Any] | None:
    try:
        item_id = int(raw.get("id"))
    except Exception:
        return None

    raw_status = raw.get("status", prior.get("status") if prior else None)
    if raw_status is None and not require_status:
        status = "pending"
    else:
        status_text = str(raw_status).strip().lower() if raw_status is not None else ""
        status_map = {
            "pending": "pending",
            "done": "done",
            "skip": "skipped",
            "skipped": "skipped",
        }
        status = status_map.get(status_text)
        if status is None:
            return None

    problem_id = raw.get("problem", prior.get("problem") if prior else None)
    if problem_id is None:
        return None
    problem_id = str(problem_id).strip().upper()
    if problem_id not in allowed_problem_ids:
        return None

    desc = raw.get("desc", prior.get("desc") if prior else "")
    desc = str(desc).strip()
    if not desc:
        return None

    raw_budget = raw.get("budget_s", prior.get("budget_s") if prior else None)
    if raw_budget is None:
        return None
    try:
        budget_s = int(raw_budget)
    except Exception:
        return None
    if budget_s <= 0:
        return None
    budget_s = min(budget_s, MAX_SUBTASK_BUDGET_S)

    realized_bucket = raw.get("realized_bucket", prior.get("realized_bucket") if prior else None)
    if realized_bucket is not None:
        realized_bucket = str(realized_bucket).strip().lower()
        if realized_bucket not in REALIZED_BUCKETS:
            realized_bucket = None

    item = {
        "id": item_id,
        "problem": problem_id,
        "desc": desc,
        "budget_s": budget_s,
        "status": status,
    }
    if realized_bucket is not None:
        item["realized_bucket"] = realized_bucket
    return item


def _normalize_plan(
    raw_plan: Any,
    *,
    prior_plan: list[dict[str, Any]] | None,
    require_status: bool,
    allowed_problem_ids: set[str],
) -> list[dict[str, Any]] | None:
    if not isinstance(raw_plan, list):
        return None
    prior_by_id = {item["id"]: item for item in prior_plan or []}
    normalized: list[dict[str, Any]] = []
    seen: set[int] = set()
    for raw_item in raw_plan:
        if not isinstance(raw_item, dict):
            return None
        raw_item_id = raw_item.get("id")
        try:
            prior_key = int(raw_item_id)
        except Exception:
            prior_key = -1
        item = _normalize_plan_item(
            raw_item,
            prior=prior_by_id.get(prior_key),
            require_status=require_status,
            allowed_problem_ids=allowed_problem_ids,
        )
        if item is None or item["id"] in seen:
            return None
        normalized.append(item)
        seen.add(item["id"])
    return normalized


def _plan_turn_json_schema(problem_ids: set[str]) -> dict[str, Any]:
    problem_enum = sorted(problem_ids)
    return {
        "type": "object",
        "properties": {
            "PLAN": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "problem": {"type": "string", "enum": problem_enum},
                        "desc": {"type": "string"},
                        "budget_s": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": MAX_SUBTASK_BUDGET_S,
                        },
                    },
                    "required": ["id", "problem", "desc", "budget_s"],
                },
            },
            "NEXT_SUB_ID": {"type": "integer"},
        },
        "required": ["PLAN", "NEXT_SUB_ID"],
    }


def _exec_turn_json_schema(problem_ids: set[str]) -> dict[str, Any]:
    problem_enum = sorted(problem_ids)
    return {
        "type": "object",
        "properties": {
            "SUB_N_RESULT": {"type": "string"},
            "candidate_answer_json": {"type": "string"},
            "FORECAST": {
                "type": "object",
                "properties": {
                    "p_within_5pct": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "p_within_10pct": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "p_within_20pct": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "p_within_50pct": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                },
                "required": list(FORECAST_KEYS),
            },
            "REVISED_PLAN": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "problem": {"type": "string", "enum": problem_enum},
                        "desc": {"type": "string"},
                        "budget_s": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": MAX_SUBTASK_BUDGET_S,
                        },
                        "status": {
                            "type": "string",
                            "enum": ["pending", "done", "skipped"],
                        },
                        "realized_bucket": {
                            "type": "string",
                            "enum": sorted(REALIZED_BUCKETS),
                        },
                    },
                    "required": ["id", "problem", "desc", "budget_s", "status"],
                },
            },
            "NEXT_SUB_ID": {
                "anyOf": [
                    {"type": "integer"},
                    {"type": "string", "enum": sorted(STOP_TOKENS)},
                ]
            },
        },
        "required": [
            "SUB_N_RESULT",
            "candidate_answer_json",
            "FORECAST",
            "REVISED_PLAN",
            "NEXT_SUB_ID",
        ],
    }


def _parse_plan_turn(payload: Any, problem_ids: set[str]) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    plan = _normalize_plan(
        payload.get("PLAN"),
        prior_plan=None,
        require_status=False,
        allowed_problem_ids=problem_ids,
    )
    next_sub_id = _normalize_next_sub_id(payload.get("NEXT_SUB_ID"))
    if plan is None or not isinstance(next_sub_id, int):
        return None
    if next_sub_id not in {item["id"] for item in plan}:
        return None
    return {"plan": plan, "next_sub_id": next_sub_id}


def _parse_exec_turn(
    payload: Any,
    *,
    prior_plan: list[dict[str, Any]],
    problem_ids: set[str],
    executed_subtask_id: int,
) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    revised_plan = _normalize_plan(
        payload.get("REVISED_PLAN"),
        prior_plan=prior_plan,
        require_status=True,
        allowed_problem_ids=problem_ids,
    )
    next_sub_id = _normalize_next_sub_id(payload.get("NEXT_SUB_ID"))
    forecast = payload.get("FORECAST")
    forecast = _normalize_forecast(forecast) if isinstance(forecast, dict) else None
    subtask_result = payload.get("SUB_N_RESULT")
    candidate_answer = _parse_candidate_answer_json(payload.get("candidate_answer_json"))
    if (
        not isinstance(subtask_result, str)
        or not subtask_result.strip()
        or candidate_answer is None
        or revised_plan is None
        or next_sub_id is None
        or forecast is None
    ):
        return None
    return {
        "subtask_id": executed_subtask_id,
        "subtask_result": subtask_result.strip(),
        "candidate_answer": candidate_answer,
        "forecast": forecast,
        "revised_plan": revised_plan,
        "next_sub_id": next_sub_id,
    }


def _merge_revised_plan(
    proposed_plan: list[dict[str, Any]],
    *,
    prior_plan: list[dict[str, Any]],
    executed_item: dict[str, Any],
    realized_bucket: str,
) -> list[dict[str, Any]]:
    by_id = {item["id"]: dict(item) for item in proposed_plan}
    if executed_item["id"] not in by_id:
        by_id[executed_item["id"]] = dict(executed_item)
    executed = by_id[executed_item["id"]]
    executed["status"] = "done"
    executed["problem"] = executed_item["problem"]
    executed["desc"] = executed_item["desc"]
    executed["budget_s"] = executed_item["budget_s"]
    executed["realized_bucket"] = realized_bucket

    # Keep prior done items if the model omitted them from the revised state.
    for item in prior_plan:
        if item["id"] not in by_id and item.get("status") == "done":
            by_id[item["id"]] = dict(item)

    return [by_id[item_id] for item_id in sorted(by_id)]


def _plan_delta(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> dict[str, Any]:
    previous_by_id = {item["id"]: item for item in previous}
    current_by_id = {item["id"]: item for item in current}
    additions = sorted(item_id for item_id in current_by_id if item_id not in previous_by_id)
    revisions = sorted(
        item_id
        for item_id in current_by_id
        if item_id in previous_by_id
        and any(
            current_by_id[item_id].get(field) != previous_by_id[item_id].get(field)
            for field in ("problem", "desc", "budget_s")
        )
    )
    status_flips = sorted(
        item_id
        for item_id in current_by_id
        if item_id in previous_by_id
        and current_by_id[item_id].get("status") != previous_by_id[item_id].get("status")
    )
    return {
        "plan_size": len(current),
        "additions": additions,
        "revisions": revisions,
        "status_flips": status_flips,
    }


def _fmt_token(value: Any) -> str:
    return "NA" if value is None else str(value)


def _call_with_timeout(
    session: GeminiChatSession,
    message: str,
    timeout_s: int,
    **send_kwargs: Any,
) -> dict[str, Any]:
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    start = time.monotonic()
    future = executor.submit(session.send_message, message, timeout_s, **send_kwargs)
    try:
        result = future.result(timeout=timeout_s)
        result["timed_out"] = False
        return result
    except concurrent.futures.TimeoutError:
        future.cancel()
        return {
            "text": "",
            "parsed": None,
            "wall_seconds": time.monotonic() - start,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "thinking_tokens": None,
            "timed_out": True,
        }
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _snapshot_attempt(response: dict[str, Any], attempt_index: int) -> dict[str, Any]:
    return {
        "attempt_index": attempt_index,
        "text": response.get("text"),
        "parsed": _clone_jsonish(response.get("parsed")),
        "wall_seconds": response.get("wall_seconds"),
        "input_tokens": response.get("input_tokens"),
        "output_tokens": response.get("output_tokens"),
        "total_tokens": response.get("total_tokens"),
        "thinking_tokens": response.get("thinking_tokens"),
        "timed_out": response.get("timed_out"),
    }


def _sum_attempt_field(attempts: list[dict[str, Any]], field: str) -> int | float | None:
    values = [attempt[field] for attempt in attempts if attempt.get(field) is not None]
    if not values:
        return None
    return sum(values)


def _call_structured_with_retry(
    session: GeminiChatSession,
    message: str,
    timeout_s: int,
    *,
    response_json_schema: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    attempts: list[dict[str, Any]] = []
    final_response: dict[str, Any] | None = None
    for attempt_index in range(1, 3):
        response = _call_with_timeout(
            session,
            message,
            timeout_s,
            response_json_schema=response_json_schema,
        )
        attempts.append(_snapshot_attempt(response, attempt_index))
        final_response = response
        if response["timed_out"] or response.get("parsed") is not None or attempt_index == 2:
            break

    if final_response is None:
        raise RuntimeError("structured call failed to produce a response object")

    aggregated = dict(final_response)
    aggregated["wall_seconds"] = float(_sum_attempt_field(attempts, "wall_seconds") or 0.0)
    for field in ("input_tokens", "output_tokens", "total_tokens", "thinking_tokens"):
        aggregated[field] = _sum_attempt_field(attempts, field)
    aggregated["retry_count"] = len(attempts) - 1
    aggregated["attempts"] = attempts

    parsed_payload = aggregated.get("parsed")
    normalized = _clone_jsonish(parsed_payload) if isinstance(parsed_payload, dict) else None
    return aggregated, normalized


def format_turn1_prompt(problems: list[PreparedProblem]) -> str:
    lines = [
        f"TOTAL_WALL_BUDGET_S: {TOTAL_BUDGET_S}",
        f"COST_PER_SECOND: {COST_PER_SECOND:.2f}",
        f"SUBTASK_BUDGET_CAP_S: {MAX_SUBTASK_BUDGET_S}",
        "Session score = sum(value captured per problem) - COST_PER_SECOND * total_wall_seconds.",
        "Value captured per problem is clipped to [0, value_cap].",
        "Turn 1 is planning only: do not emit any candidate artifact yet.",
        "Build a short portfolio allocation plan over these four problems.",
        "Return one JSON object only, matching the response schema exactly.",
        "No markdown, no code fences, and no prose outside JSON.",
        "",
        "Portfolio baseline state:",
    ]
    for problem in problems:
        lines.append(
            f"- {problem.problem_id} | {problem.label} | value_cap={problem.value_cap} | "
            f"baseline_{problem.metric_name}={_fmt_metric(problem.baseline_score)}"
        )
    lines.append("")
    for problem in problems:
        lines.extend(
            [
                f"=== {problem.problem_id}: {problem.label} ===",
                problem.problem_statement,
                f"When you later touch {problem.problem_id}, candidate_answer_json must decode to this shape:",
                problem.answer_contract,
                "",
            ]
        )
    lines.extend(
        [
            "Requirements:",
            "- PLAN can include any subset of P1..P4 and may contain multiple subtasks for the same problem.",
            "- PLAN is explicit state: use stable ids for surviving items and short free-text desc values.",
            "- desc should be short and should not restate the problem text.",
            f"- budget_s must be a positive integer no larger than {MAX_SUBTASK_BUDGET_S}.",
            "- Keep the plan multi-step and revisable; do not collapse it into one blob of prose.",
            "- NEXT_SUB_ID must point to one plan item in PLAN.",
        ]
    )
    return "\n".join(lines)


def format_exec_prompt(
    *,
    turn_number: int,
    previous_turn: dict[str, Any],
    elapsed_s: float,
    problems_by_id: dict[str, PreparedProblem],
    current_answers: dict[str, Any],
    current_scores: dict[str, float],
    plan_state: list[dict[str, Any]],
    next_sub: dict[str, Any],
) -> str:
    remaining_s = max(0.0, TOTAL_BUDGET_S - elapsed_s)
    prev_wall = previous_turn.get("wall_seconds")
    prev_input = previous_turn.get("input_tokens")
    prev_output = previous_turn.get("output_tokens")
    prev_total = previous_turn.get("total_tokens")

    status_lines = []
    for problem_id in sorted(problems_by_id):
        problem = problems_by_id[problem_id]
        current_score = current_scores[problem_id]
        gap_pct = problem.gap_pct_for_score(current_score)
        value = problem.value_captured(current_score)
        status_lines.append(
            f"- {problem_id} {problem.short_label}: current_{problem.metric_name}={_fmt_metric(current_score)}, "
            f"baseline={_fmt_metric(problem.baseline_score)}, gap_pct={gap_pct:.2f}, "
            f"value={value:.2f}/{problem.value_cap}"
        )

    target_problem = problems_by_id[next_sub["problem"]]
    target_answer = current_answers[next_sub["problem"]]
    target_score = current_scores[next_sub["problem"]]
    target_answer_json = json.dumps(target_answer, indent=2, sort_keys=True)
    plan_json = json.dumps(plan_state, indent=2, sort_keys=True)

    return (
        f"TURN_{turn_number - 1} STATS: wall={prev_wall:.1f}s, input_tok={_fmt_token(prev_input)}, "
        f"output_tok={_fmt_token(prev_output)}, total_tok={_fmt_token(prev_total)}\n"
        f"CUMULATIVE: wall={elapsed_s:.1f}s / {TOTAL_BUDGET_S}s, remaining={remaining_s:.1f}s\n"
        f"CURRENT_SUBTASK: id={next_sub['id']} problem={next_sub['problem']} budget_s={next_sub['budget_s']}\n"
        f"SUBTASK_DESC: {next_sub['desc']}\n"
        "PORTFOLIO_STATUS:\n"
        f"{chr(10).join(status_lines)}\n"
        "CURRENT_PLAN_JSON:\n"
        f"{plan_json}\n"
        f"TARGET_PROBLEM_SPEC ({target_problem.problem_id}):\n"
        f"{target_problem.problem_statement}\n"
        f"CURRENT_BEST_{target_problem.metric_name.upper()}: {_fmt_metric(target_score)}\n"
        "CURRENT_BEST_SUMMARY:\n"
        f"{target_problem.summarize_answer(target_answer, target_score)}\n"
        "CURRENT_BEST_JSON:\n"
        f"{target_answer_json}\n"
        "CANDIDATE_ANSWER_SHAPE:\n"
        f"{target_problem.answer_contract}\n"
        "Now execute the current subtask, then revise the plan state.\n"
        "Return one JSON object only, matching the response schema exactly.\n"
        "No markdown, no code fences, and no prose outside JSON.\n"
        "REVISED_PLAN must be the full revised plan state, not just the delta.\n"
        "Keep surviving subtask ids stable. Add new follow-up work with fresh ids rather than renumbering.\n"
        "FORECAST for the touched problem means the probability that the current best answer for that problem "
        "is within the stated gap threshold relative to that problem's offline gold.\n"
        "Rules:\n"
        "- SUB_N_RESULT is free-form text summarizing your work on this subtask.\n"
        f"- candidate_answer_json must be a JSON string whose decoded value is the full valid answer for {target_problem.problem_id}.\n"
        '- Example object payload: "{\\"assignment\\":{\\"N01\\":1,\\"N02\\":2}}". Example array payload: "[0,1,2,...]".\n'
        "- Forecast probabilities must be between 0 and 1 and monotone non-decreasing across thresholds.\n"
        "- If the executed subtask is finished, mark it done and put any follow-up as a new id.\n"
        "- If you want to stop because further work is not worth its cost, use stop_economic.\n"
    )


def _fmt_metric(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.3f}"


def _clone_jsonish(value: Any) -> Any:
    return json.loads(json.dumps(value))


def run_protocol(problems: list[PreparedProblem], model_name: str) -> dict[str, Any]:
    session = GeminiChatSession(
        model_name=model_name,
        system_instruction=build_system_prompt(),
    )
    run_start = time.monotonic()
    problems_by_id = {problem.problem_id: problem for problem in problems}
    problem_ids = set(problems_by_id)
    turns: list[dict[str, Any]] = []
    current_answers = {problem.problem_id: _clone_jsonish(problem.baseline_answer) for problem in problems}
    current_scores = {problem.problem_id: float(problem.baseline_score) for problem in problems}
    current_sources = {problem.problem_id: "baseline" for problem in problems}
    forecast_history = {problem.problem_id: [] for problem in problems}
    per_problem_turns = {problem.problem_id: [] for problem in problems}
    plan_evolution: list[dict[str, Any]] = []
    initial_plan: list[dict[str, Any]] | None = None
    plan_state: list[dict[str, Any]] = []
    next_sub_id: int | str | None = None
    turn1_died = False
    parse_fail = False
    subtask_killed_count = 0
    revised_best_guess_downward = False
    feasibility_failures = 0
    stop_reason = "unknown"

    plan_response, plan_payload = _call_structured_with_retry(
        session,
        format_turn1_prompt(problems),
        PLAN_TURN_BUDGET_S,
        response_json_schema=_plan_turn_json_schema(problem_ids),
    )
    plan_parsed = None if plan_response["timed_out"] else _parse_plan_turn(plan_payload, problem_ids)
    plan_turn = {
        "turn_index": 1,
        "phase": "plan",
        "raw_text": plan_response["text"],
        "attempts": plan_response["attempts"],
        "retry_count": plan_response["retry_count"],
        "wall_seconds": plan_response["wall_seconds"],
        "input_tokens": plan_response["input_tokens"],
        "output_tokens": plan_response["output_tokens"],
        "total_tokens": plan_response["total_tokens"],
        "thinking_tokens": plan_response["thinking_tokens"],
        "timed_out": plan_response["timed_out"],
        "structured_parse_ok": plan_payload is not None,
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
        initial_plan = plan_parsed["plan"]
        plan_state = plan_parsed["plan"]
        next_sub_id = plan_parsed["next_sub_id"]

    turn_number = 2
    while (
        isinstance(next_sub_id, int)
        and stop_reason == "unknown"
        and (time.monotonic() - run_start) < TOTAL_BUDGET_S
        and turn_number <= MAX_EXEC_TURNS + 1
    ):
        plan_lookup = {item["id"]: item for item in plan_state}
        next_sub = plan_lookup.get(next_sub_id)
        if next_sub is None or next_sub.get("status") != "pending":
            parse_fail = True
            stop_reason = "invalid_next_sub"
            break

        elapsed_s = time.monotonic() - run_start
        remaining_s = max(1, int(TOTAL_BUDGET_S - elapsed_s))
        next_sub = dict(next_sub)
        next_sub["budget_s"] = max(1, min(int(next_sub["budget_s"]), MAX_SUBTASK_BUDGET_S, remaining_s))

        exec_response, exec_payload = _call_structured_with_retry(
            session,
            format_exec_prompt(
                turn_number=turn_number,
                previous_turn=turns[-1],
                elapsed_s=elapsed_s,
                problems_by_id=problems_by_id,
                current_answers=current_answers,
                current_scores=current_scores,
                plan_state=plan_state,
                next_sub=next_sub,
            ),
            next_sub["budget_s"],
            response_json_schema=_exec_turn_json_schema(problem_ids),
        )
        exec_parsed = None
        if not exec_response["timed_out"]:
            exec_parsed = _parse_exec_turn(
                exec_payload,
                prior_plan=plan_state,
                problem_ids=problem_ids,
                executed_subtask_id=next_sub["id"],
            )

        exec_turn: dict[str, Any] = {
            "turn_index": turn_number,
            "phase": "exec",
            "next_sub_in": next_sub,
            "raw_text": exec_response["text"],
            "attempts": exec_response["attempts"],
            "retry_count": exec_response["retry_count"],
            "wall_seconds": exec_response["wall_seconds"],
            "input_tokens": exec_response["input_tokens"],
            "output_tokens": exec_response["output_tokens"],
            "total_tokens": exec_response["total_tokens"],
            "thinking_tokens": exec_response["thinking_tokens"],
            "timed_out": exec_response["timed_out"],
            "structured_parse_ok": exec_payload is not None,
            "parse_ok": exec_parsed is not None,
            "parsed": exec_parsed,
        }

        if exec_response["timed_out"]:
            turns.append(exec_turn)
            subtask_killed_count += 1
            stop_reason = "subtask_timeout"
            break

        if exec_parsed is None or exec_parsed["subtask_id"] != next_sub["id"]:
            turns.append(exec_turn)
            parse_fail = True
            stop_reason = "subtask_parse_fail"
            break

        touched_problem = problems_by_id[next_sub["problem"]]
        verification = touched_problem.verify_answer(exec_parsed["candidate_answer"])
        exec_turn["verification"] = {
            "feasible": verification.feasible,
            "score": verification.score,
            "failure_reason": verification.failure_reason,
            "details": verification.details,
        }
        exec_turn["subtask_result"] = exec_parsed["subtask_result"]

        if verification.feasible and verification.score is not None:
            previous_score = current_scores[touched_problem.problem_id]
            if verification.score <= previous_score + 1e-9 and verification.normalized_answer is not None:
                current_answers[touched_problem.problem_id] = _clone_jsonish(verification.normalized_answer)
                current_scores[touched_problem.problem_id] = verification.score
                current_sources[touched_problem.problem_id] = "model"
            elif verification.score > previous_score + 1e-9:
                revised_best_guess_downward = True
        else:
            feasibility_failures += 1

        realized_score = current_scores[touched_problem.problem_id]
        realized_bucket = touched_problem.realized_bucket(realized_score)
        forecast_history[touched_problem.problem_id].append(
            {
                "turn_index": turn_number,
                "forecast": exec_parsed["forecast"],
                "realized_score": realized_score,
            }
        )
        per_problem_turns[touched_problem.problem_id].append(turn_number)

        merged_plan = _merge_revised_plan(
            exec_parsed["revised_plan"],
            prior_plan=plan_state,
            executed_item=next_sub,
            realized_bucket=realized_bucket,
        )
        delta = _plan_delta(plan_state, merged_plan)
        exec_turn["plan_delta"] = delta
        exec_turn["plan_state_out"] = merged_plan
        turns.append(exec_turn)
        plan_evolution.append(
            {
                "turn_index": turn_number,
                "problem": touched_problem.problem_id,
                "executed_sub_id": next_sub["id"],
                "plan_size": delta["plan_size"],
                "additions": delta["additions"],
                "revisions": delta["revisions"],
                "status_flips": delta["status_flips"],
                "next_sub_id_out": exec_parsed["next_sub_id"],
            }
        )
        plan_state = merged_plan

        if exec_parsed["next_sub_id"] in STOP_TOKENS:
            stop_reason = str(exec_parsed["next_sub_id"])
            break

        next_sub_id = exec_parsed["next_sub_id"]
        turn_number += 1

    if stop_reason == "unknown":
        if turn_number > MAX_EXEC_TURNS + 1 and isinstance(next_sub_id, int):
            stop_reason = "max_exec_turns"
        else:
            stop_reason = "stop_budget"

    total_wall_seconds = time.monotonic() - run_start
    per_problem_results: dict[str, dict[str, Any]] = {}
    brier_by_problem: dict[str, dict[str, float | None]] = {}
    final_value_sum = 0.0
    for problem in problems:
        final_score = current_scores[problem.problem_id]
        value_captured = problem.value_captured(final_score)
        final_value_sum += value_captured
        per_problem_results[problem.problem_id] = {
            "label": problem.label,
            "value_cap": problem.value_cap,
            "metric_name": problem.metric_name,
            "baseline_score": problem.baseline_score,
            "gold_score": problem.gold_score,
            "final_score": final_score,
            "final_gap_pct": problem.gap_pct_for_score(final_score),
            "value_captured": value_captured,
            "subtasks_executed": len(per_problem_turns[problem.problem_id]),
            "final_answer": current_answers[problem.problem_id],
            "final_source": current_sources[problem.problem_id],
        }
        entries = forecast_history[problem.problem_id]
        brier_by_problem[problem.problem_id] = {
            key: (
                sum(
                    (
                        entry["forecast"][key]
                        - forecast_event_map(problem, entry["realized_score"])[key]
                    )
                    ** 2
                    for entry in entries
                )
                / len(entries)
            )
            if entries
            else None
            for key in FORECAST_KEYS
        }

    time_cost = COST_PER_SECOND * total_wall_seconds
    net_score = final_value_sum - time_cost
    initial_allocation = {
        problem.problem_id: sum(item["budget_s"] for item in (initial_plan or []) if item["problem"] == problem.problem_id)
        for problem in problems
    }
    abandoned_problems = sorted(
        problem.problem_id
        for problem in problems
        if initial_allocation[problem.problem_id] > 0 and not per_problem_turns[problem.problem_id]
    )

    return {
        "model": model_name,
        "seed": problems[0].instance.seed if problems else None,
        "cost_per_second": COST_PER_SECOND,
        "total_wall_budget_s": TOTAL_BUDGET_S,
        "max_exec_turns": MAX_EXEC_TURNS,
        "problems": per_problem_results,
        "preflight": {
            problem.problem_id: {
                "baseline_score": problem.baseline_score,
                "gold_score": problem.gold_score,
                "gap_pct": problem.baseline_gap_pct,
                "gold_method": problem.gold_method,
                "gold_wall_seconds": problem.gold_wall_seconds,
            }
            for problem in problems
        },
        "turns": turns,
        "initial_plan": initial_plan,
        "final_plan": plan_state,
        "plan_evolution": plan_evolution,
        "initial_allocation": initial_allocation,
        "forecast_history": forecast_history,
        "forecast_brier_by_problem": brier_by_problem,
        "forecast_event_by_problem": {
            problem.problem_id: forecast_event_map(problem, current_scores[problem.problem_id])
            for problem in problems
        },
        "per_problem_turns": per_problem_turns,
        "session_value_sum": final_value_sum,
        "session_time_cost": time_cost,
        "session_net_score": net_score,
        "turn_count": len(turns),
        "turn1_wall_seconds": turns[0]["wall_seconds"],
        "stop_reason": stop_reason,
        "turn1_died": turn1_died,
        "parse_fail": parse_fail,
        "subtask_killed_count": subtask_killed_count,
        "revised_best_guess_downward": revised_best_guess_downward,
        "feasibility_failure_count": feasibility_failures,
        "abandoned_problems": abandoned_problems,
        "total_wall_seconds": total_wall_seconds,
    }
