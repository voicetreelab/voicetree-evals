#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
from string import Template


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from hch.codex_metagame_v2.jobshop_instance import build_instance  # noqa: E402


SEEDS = (1, 2, 3)
N_JOBS = 5
N_MACHINES = 6
OUTPUT_PATH = REPO_ROOT / "kaggle" / "examples" / "coupled_jobshop_spike" / "cjs_5x6.py"


TASK_TEMPLATE = Template(
    textwrap.dedent(
        """\
        from __future__ import annotations

        import ast
        import json
        import os
        import re
        import time
        from typing import Any

        import kaggle_benchmarks as kbench

        SEED = int(globals().get("CJS_TARGET_SEED", 1))
        N_JOBS = 5
        N_MACHINES = 6

        TOTAL_BUDGET_S = 1800
        SUBTASK_BUDGET_S = 600
        PLAN_TURN_BUDGET_S = 300
        MAX_EXEC_TURNS = 4
        TIME_PENALTY = 0.01
        GAP_THRESHOLDS = (2.0, 5.0, 10.0)

        CANONICAL_SYSTEM_PROMPT = \"\"\"You are running a locked budget-metagame protocol on a coupled two-factory job-shop scheduling problem.
        You earn score for reducing makespan gap and lose score for wall-clock time.
        Turn 1 is planning only: do not emit a schedule there.
        Execution turns must emit BEST_GUESS as valid JSON with machine timelines for both factories.
        When forecasting quality, do not give a probability of exact correctness. Give calibrated probabilities for thresholded gap-to-optimal events.
        When forecasting continuation, estimate whether exactly one more subtask is worth its time cost relative to stopping now.
        Do not call tools.
        Do not write Python, pseudocode, or solver sketches.
        Work only from the prompt, the current best schedule, and your own scheduling reasoning.
        When a field expects JSON, emit valid JSON.
        \"\"\"

        INSTANCE_DATA_BY_SEED = $INSTANCE_JSON

        _FLOAT_PATTERN = r"[-+]?\\d*\\.?\\d+(?:[eE][-+]?\\d+)?"
        _DECISION_RE = re.compile(
            r"^\\s*\\**\\s*DECISION\\**\\s*:\\s*\\**\\s*(continue|stop)\\s*\\**\\s*$$",
            re.IGNORECASE | re.MULTILINE,
        )
        _SUB_RE = re.compile(
            r"^\\s*\\**\\s*SUB_(\\d+)\\**\\s*:\\s*(.*?)(?=^\\s*\\**\\s*[A-Z][A-Z0-9_]*\\**\\s*:|\\Z)",
            re.DOTALL | re.MULTILINE,
        )


        def _instance() -> dict[str, Any]:
            try:
                return INSTANCE_DATA_BY_SEED[str(SEED)]
            except KeyError as exc:
                raise RuntimeError(f"Unsupported seed {SEED}. Expected one of {sorted(INSTANCE_DATA_BY_SEED)}.") from exc


        def _extract_label_block(text: str, label: str) -> str | None:
            pattern = re.compile(
                rf"^\\s*\\**\\s*{re.escape(label)}\\**\\s*:\\s*(.*?)(?=^\\s*\\**\\s*[A-Z][A-Z0-9_]*\\**\\s*:|\\Z)",
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
                    return "\\n".join(lines[1:-1]).strip()
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


        def _safe_float(value: Any) -> float | None:
            try:
                return float(value)
            except Exception:
                return None


        def _gap_key(threshold: float) -> str:
            return f"p_gap_le_{int(threshold)}"


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


        def _duration_for_machine(route: list[dict[str, Any]], machine_name: str) -> int | None:
            for op in route:
                if op["machine_name"] == machine_name:
                    return int(op["duration"])
            return None


        def _check_machine_conflicts(entries: list[tuple[int, int, int]]) -> str | None:
            for index in range(1, len(entries)):
                prev = entries[index - 1]
                current = entries[index]
                if current[1] < prev[2]:
                    return f"machine overlap between J{prev[0]} and J{current[0]}"
            return None


        def _check_route_precedence(
            route: list[dict[str, Any]],
            start_lookup: dict[str, int],
            completion_lookup: dict[str, int],
        ) -> str | None:
            previous_end = None
            for op in route:
                machine_name = op["machine_name"]
                if machine_name not in start_lookup or machine_name not in completion_lookup:
                    return f"missing timing for {machine_name}"
                current_start = start_lookup[machine_name]
                current_end = completion_lookup[machine_name]
                if previous_end is not None and current_start < previous_end:
                    return f"{machine_name} starts at {current_start} before predecessor finished at {previous_end}"
                previous_end = current_end
            return None


        def _parse_factory_schedule(
            factory_schedule: dict[str, Any],
            expected_machines: set[str],
        ) -> dict[str, list[tuple[int, int, int]]] | str:
            parsed: dict[str, list[tuple[int, int, int]]] = {}
            for machine_name in expected_machines:
                entries = factory_schedule.get(machine_name, [])
                if not isinstance(entries, list):
                    return f"machine {machine_name} must map to a list"
                machine_entries: list[tuple[int, int, int]] = []
                for item in entries:
                    if not isinstance(item, list) or len(item) != 3:
                        return f"machine {machine_name} entries must be [job, start, end]"
                    job_label, start, end = item
                    try:
                        job_id = int(str(job_label).lstrip("Jj"))
                        start_int = int(start)
                        end_int = int(end)
                    except Exception:
                        return f"machine {machine_name} has non-integer schedule entry"
                    if end_int <= start_int:
                        return f"machine {machine_name} has non-positive duration for J{job_id}"
                    machine_entries.append((job_id, start_int, end_int))
                parsed[machine_name] = sorted(machine_entries, key=lambda item: (item[1], item[2], item[0]))
            unknown = set(factory_schedule) - expected_machines
            if unknown:
                return f"unknown machines in schedule: {sorted(unknown)}"
            return parsed


        def verify_schedule(
            *,
            jobs: list[dict[str, Any]],
            n_machines: int,
            schedule: dict[str, Any] | None,
        ) -> dict[str, Any]:
            if not isinstance(schedule, dict):
                return {"is_feasible": False, "verified_makespan": None, "failure_reason": "schedule must be an object"}

            try:
                factory_a = schedule["factory_a"]
                factory_b = schedule["factory_b"]
                claimed_makespan = int(schedule["makespan"])
            except Exception:
                return {
                    "is_feasible": False,
                    "verified_makespan": None,
                    "failure_reason": "schedule must contain factory_a, factory_b, makespan",
                }

            expected_a = {f"MA{index}" for index in range(1, n_machines + 1)}
            expected_b = {f"MB{index}" for index in range(1, n_machines + 1)}
            if not isinstance(factory_a, dict) or not isinstance(factory_b, dict):
                return {
                    "is_feasible": False,
                    "verified_makespan": None,
                    "failure_reason": "factory schedules must be objects",
                }

            parsed_a = _parse_factory_schedule(factory_a, expected_a)
            if isinstance(parsed_a, str):
                return {"is_feasible": False, "verified_makespan": None, "failure_reason": parsed_a}
            parsed_b = _parse_factory_schedule(factory_b, expected_b)
            if isinstance(parsed_b, str):
                return {"is_feasible": False, "verified_makespan": None, "failure_reason": parsed_b}

            jobs_by_id = {int(job["job_id"]): job for job in jobs}
            seen_ops_a: set[tuple[int, str]] = set()
            seen_ops_b: set[tuple[int, str]] = set()
            start_a: dict[int, dict[str, int]] = {job_id: {} for job_id in jobs_by_id}
            completion_a: dict[int, dict[str, int]] = {job_id: {} for job_id in jobs_by_id}
            start_b: dict[int, dict[str, int]] = {job_id: {} for job_id in jobs_by_id}
            completion_b: dict[int, dict[str, int]] = {job_id: {} for job_id in jobs_by_id}
            max_end = 0

            for machine_name, entries in parsed_a.items():
                reason = _check_machine_conflicts(entries)
                if reason:
                    return {"is_feasible": False, "verified_makespan": None, "failure_reason": reason}
                for job_id, start, end in entries:
                    job = jobs_by_id.get(job_id)
                    if job is None:
                        return {"is_feasible": False, "verified_makespan": None, "failure_reason": f"unknown job J{job_id} in {machine_name}"}
                    duration = _duration_for_machine(job["factory_a"], machine_name)
                    if duration is None:
                        return {
                            "is_feasible": False,
                            "verified_makespan": None,
                            "failure_reason": f"job J{job_id} does not use machine {machine_name} in factory A",
                        }
                    if end - start != duration:
                        return {
                            "is_feasible": False,
                            "verified_makespan": None,
                            "failure_reason": f"duration mismatch for J{job_id} on {machine_name}: expected {duration}, got {end - start}",
                        }
                    op_key = (job_id, machine_name)
                    if op_key in seen_ops_a:
                        return {
                            "is_feasible": False,
                            "verified_makespan": None,
                            "failure_reason": f"duplicate operation for J{job_id} on {machine_name}",
                        }
                    seen_ops_a.add(op_key)
                    start_a[job_id][machine_name] = start
                    completion_a[job_id][machine_name] = end
                    max_end = max(max_end, end)

            for machine_name, entries in parsed_b.items():
                reason = _check_machine_conflicts(entries)
                if reason:
                    return {"is_feasible": False, "verified_makespan": None, "failure_reason": reason}
                for job_id, start, end in entries:
                    job = jobs_by_id.get(job_id)
                    if job is None:
                        return {"is_feasible": False, "verified_makespan": None, "failure_reason": f"unknown job J{job_id} in {machine_name}"}
                    duration = _duration_for_machine(job["factory_b"], machine_name)
                    if duration is None:
                        return {
                            "is_feasible": False,
                            "verified_makespan": None,
                            "failure_reason": f"job J{job_id} does not use machine {machine_name} in factory B",
                        }
                    if end - start != duration:
                        return {
                            "is_feasible": False,
                            "verified_makespan": None,
                            "failure_reason": f"duration mismatch for J{job_id} on {machine_name}: expected {duration}, got {end - start}",
                        }
                    op_key = (job_id, machine_name)
                    if op_key in seen_ops_b:
                        return {
                            "is_feasible": False,
                            "verified_makespan": None,
                            "failure_reason": f"duplicate operation for J{job_id} on {machine_name}",
                        }
                    seen_ops_b.add(op_key)
                    start_b[job_id][machine_name] = start
                    completion_b[job_id][machine_name] = end
                    max_end = max(max_end, end)

            for job_id, job in jobs_by_id.items():
                if len(seen_ops_a.intersection({(job_id, op["machine_name"]) for op in job["factory_a"]})) != len(job["factory_a"]):
                    return {"is_feasible": False, "verified_makespan": None, "failure_reason": f"missing factory A operations for J{job_id}"}
                if len(seen_ops_b.intersection({(job_id, op["machine_name"]) for op in job["factory_b"]})) != len(job["factory_b"]):
                    return {"is_feasible": False, "verified_makespan": None, "failure_reason": f"missing factory B operations for J{job_id}"}

                reason = _check_route_precedence(job["factory_a"], start_a[job_id], completion_a[job_id])
                if reason:
                    return {
                        "is_feasible": False,
                        "verified_makespan": None,
                        "failure_reason": f"factory A precedence failed for J{job_id}: {reason}",
                    }
                reason = _check_route_precedence(job["factory_b"], start_b[job_id], completion_b[job_id])
                if reason:
                    return {
                        "is_feasible": False,
                        "verified_makespan": None,
                        "failure_reason": f"factory B precedence failed for J{job_id}: {reason}",
                    }

                last_a_machine = job["factory_a"][-1]["machine_name"]
                first_b_machine = job["factory_b"][0]["machine_name"]
                if start_b[job_id][first_b_machine] < completion_a[job_id][last_a_machine]:
                    return {"is_feasible": False, "verified_makespan": None, "failure_reason": f"coupling violation for J{job_id}"}

            if claimed_makespan != max_end:
                return {
                    "is_feasible": False,
                    "verified_makespan": None,
                    "failure_reason": f"claimed makespan {claimed_makespan} does not match verified {max_end}",
                }

            return {"is_feasible": True, "verified_makespan": max_end, "failure_reason": None}


        def schedule_summary(schedule: dict[str, Any]) -> str:
            parts: list[str] = []
            for factory_key, title in (("factory_a", "Factory A"), ("factory_b", "Factory B")):
                lines = []
                for machine_name in sorted(schedule.get(factory_key, {})):
                    entries = ",".join(
                        f"{job}[{start}-{end}]"
                        for job, start, end in schedule[factory_key][machine_name]
                    )
                    lines.append(f"{machine_name}: {entries}")
                parts.append(f"{title}: " + "; ".join(lines))
            parts.append(f"Makespan: {schedule.get('makespan')}")
            return "\\n".join(parts)


        def format_turn1_prompt(instance: dict[str, Any]) -> str:
            return (
                f"{instance['problem_statement']}\\n"
                "Turn 1 is planning only. Do not emit BEST_GUESS or a full schedule yet.\\n"
                "Forecast the quality of an atomic answer and whether one more subtask is economically worth it.\\n"
                "Use calibrated probabilities for distance-to-optimal thresholds, not a probability of exact correctness.\\n"
                "Your CONTINUE_FORECAST should estimate the value of taking exactly one more subtask instead of stopping now.\\n"
                "Use this exact output contract:\\n"
                'ATOMIC_FORECAST: {"p_gap_le_2": <float>, "p_gap_le_5": <float>, "p_gap_le_10": <float>}\\n'
                'CONTINUE_FORECAST: {"p_improve_if_one_more_subtask": <float>, "expected_gap_reduction": <float>, "expected_delta_score": <float>}\\n'
                "DECISION: continue | stop\\n"
                f'NEXT_SUB: {{"id": 1, "desc": "...", "time_budget_s": {SUBTASK_BUDGET_S}}}\\n'
                "If DECISION is stop, omit NEXT_SUB.\\n"
                f"Probabilities must be between 0 and 1 and must be monotone: {_gap_key(2.0)} <= {_gap_key(5.0)} <= {_gap_key(10.0)}.\\n"
            )


        def _fmt_token(value: Any) -> str:
            return "NA" if value is None else str(value)


        def format_exec_prompt(
            *,
            turn_number: int,
            previous_turn: dict[str, Any],
            elapsed_s: float,
            current_best_schedule: dict[str, Any],
            current_best_source: str,
            current_best_makespan: int,
            next_sub: dict[str, Any],
        ) -> str:
            remaining_s = max(0.0, TOTAL_BUDGET_S - elapsed_s)
            prev_input = previous_turn.get("input_tokens")
            prev_output = previous_turn.get("output_tokens")
            prev_wall = previous_turn.get("wall_seconds")
            prev_total = previous_turn.get("total_tokens")
            schedule_json = json.dumps(current_best_schedule, indent=2, sort_keys=True)
            return (
                f"TURN_{turn_number - 1} STATS: wall={prev_wall:.1f}s, input_tok={_fmt_token(prev_input)}, "
                f"output_tok={_fmt_token(prev_output)}, total_tok={_fmt_token(prev_total)}\\n"
                f"CUMULATIVE: wall={elapsed_s:.1f}s / {TOTAL_BUDGET_S}s, remaining={remaining_s:.1f}s\\n"
                f"SUBTASK BUDGET: {next_sub['time_budget_s']}s per turn (hard kill)\\n"
                f"NEXT_SUB_TO_EXECUTE: {json.dumps(next_sub, sort_keys=True)}\\n"
                f"CURRENT_BEST_SOURCE: {current_best_source}\\n"
                f"CURRENT_BEST_MAKESPAN: {current_best_makespan}\\n"
                f"CURRENT_BEST_SUMMARY:\\n{schedule_summary(current_best_schedule)}\\n"
                f"CURRENT_BEST_JSON:\\n{schedule_json}\\n"
                "Now execute NEXT_SUB_TO_EXECUTE. You may keep the current schedule if you judge further edits are not worth it.\\n"
                "QUALITY_FORECAST should describe the quality of the BEST_GUESS you emit this turn.\\n"
                "CONTINUE_FORECAST should estimate the value of taking exactly one more subtask after this turn instead of stopping.\\n"
                "Use this exact output contract:\\n"
                f"SUB_{turn_number - 1}: <work>\\n"
                "BEST_GUESS: {\\n"
                '  "factory_a": {"MA1": [["J1", 0, 3]], "...": []},\\n'
                '  "factory_b": {"MB1": [["J2", 8, 10]], "...": []},\\n'
                '  "makespan": 24\\n'
                "}\\n"
                'QUALITY_FORECAST: {"p_gap_le_2": <float>, "p_gap_le_5": <float>, "p_gap_le_10": <float>}\\n'
                'CONTINUE_FORECAST: {"p_improve_if_one_more_subtask": <float>, "expected_gap_reduction": <float>, "expected_delta_score": <float>}\\n'
                "DECISION: continue | stop\\n"
                f'NEXT_SUB: {{"id": {turn_number}, "desc": "...", "time_budget_s": {SUBTASK_BUDGET_S}}}\\n'
                "If DECISION is stop, omit NEXT_SUB.\\n"
                f"Probabilities must be between 0 and 1 and must be monotone: {_gap_key(2.0)} <= {_gap_key(5.0)} <= {_gap_key(10.0)}.\\n"
                "Every required operation must appear exactly once. Start/end times must be integers. Claimed makespan must match the schedule.\\n"
            )


        def _call_model(llm: Any, prompt: str, timeout_s: int) -> dict[str, Any]:
            start = time.monotonic()
            kbench.actors.user.send(prompt)
            response = llm.respond(system=CANONICAL_SYSTEM_PROMPT, temperature=0)
            wall_seconds = time.monotonic() - start
            meta = getattr(response, "_meta", {}) or {}
            return {
                "text": str(response.content or "").strip(),
                "wall_seconds": wall_seconds,
                "input_tokens": meta.get("input_tokens"),
                "output_tokens": meta.get("output_tokens"),
                "total_tokens": meta.get("total_tokens"),
                "thinking_tokens": meta.get("thinking_tokens"),
                "timed_out": wall_seconds > timeout_s,
            }


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


        def run_protocol(llm: Any, instance: dict[str, Any]) -> dict[str, Any]:
            run_start = time.monotonic()
            turns: list[dict[str, Any]] = []
            current_best_schedule = instance["baseline_schedule"]
            current_best_makespan = int(instance["baseline_makespan"])
            current_best_source = "baseline"
            final_schedule_source = "baseline"
            atomic_forecast: dict[str, float] | None = None
            plan_continue_forecast: dict[str, float] | None = None
            final_quality_forecast: dict[str, float] | None = None
            final_continue_forecast: dict[str, float] | None = None
            turn1_died = False
            parse_fail = False
            subtask_killed_count = 0
            revised_best_guess_downward = False
            stop_reason = "unknown"
            next_sub: dict[str, Any] | None = None
            max_exec_turns_reached = False
            feasible_failures = 0
            valid_model_turns: list[int] = []
            error_message: str | None = None

            try:
                plan_response = _call_model(llm, format_turn1_prompt(instance), PLAN_TURN_BUDGET_S)
            except Exception as exc:
                plan_response = {
                    "text": "",
                    "wall_seconds": time.monotonic() - run_start,
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "thinking_tokens": None,
                    "timed_out": False,
                }
                error_message = f"{type(exc).__name__}: {exc}"
                turn1_died = True
                stop_reason = "plan_error"

            plan_parsed = None if plan_response["timed_out"] or error_message else parse_plan_turn(plan_response["text"])
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

            if stop_reason == "unknown":
                if plan_response["timed_out"] or plan_parsed is None:
                    turn1_died = True
                    if not plan_response["timed_out"]:
                        parse_fail = True
                    stop_reason = "turn1_died" if plan_response["timed_out"] else "plan_parse_fail"
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
                try:
                    exec_response = _call_model(
                        llm,
                        format_exec_prompt(
                            turn_number=turn_number,
                            previous_turn=turns[-1],
                            elapsed_s=elapsed_s,
                            current_best_schedule=current_best_schedule,
                            current_best_source=current_best_source,
                            current_best_makespan=current_best_makespan,
                            next_sub=next_sub,
                        ),
                        next_sub["time_budget_s"],
                    )
                except Exception as exc:
                    exec_response = {
                        "text": "",
                        "wall_seconds": time.monotonic() - run_start,
                        "input_tokens": None,
                        "output_tokens": None,
                        "total_tokens": None,
                        "thinking_tokens": None,
                        "timed_out": False,
                    }
                    error_message = f"{type(exc).__name__}: {exc}"
                    stop_reason = "subtask_error"

                if stop_reason != "unknown":
                    break

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
                    jobs=instance["jobs"],
                    n_machines=instance["n_machines"],
                    schedule=exec_parsed["best_guess"],
                )
                exec_turn["verification"] = verification
                turns.append(exec_turn)

                if verification["is_feasible"] and verification["verified_makespan"] is not None:
                    if verification["verified_makespan"] > current_best_makespan:
                        revised_best_guess_downward = True
                    current_best_schedule = exec_parsed["best_guess"]
                    current_best_makespan = int(verification["verified_makespan"])
                    final_quality_forecast = exec_parsed["quality_forecast"]
                    final_continue_forecast = exec_parsed["continue_forecast"]
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
            baseline_gap_pct = 100.0 * (instance["baseline_makespan"] - instance["optimal_makespan"]) / instance["optimal_makespan"]
            gap_pct = 100.0 * (current_best_makespan - instance["optimal_makespan"]) / instance["optimal_makespan"]
            brier = _gap_forecast_brier(atomic_forecast, gap_pct)
            final_quality_brier = _gap_forecast_brier(final_quality_forecast, gap_pct)
            score = _score_for_gap(gap_pct, total_wall_seconds)
            plan_stop_now_score = _score_for_gap(baseline_gap_pct, plan_turn["wall_seconds"])
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
                "task_name": f"cjs_5x6_seed{instance['seed']}",
                "model": os.environ.get("LLM_DEFAULT", "unknown"),
                "seed": instance["seed"],
                "n_jobs": instance["n_jobs"],
                "n_machines": instance["n_machines"],
                "jobs": instance["jobs"],
                "baseline_schedule": instance["baseline_schedule"],
                "baseline_makespan": instance["baseline_makespan"],
                "baseline_gap_pct": baseline_gap_pct,
                "optimal_schedule": instance["optimal_schedule"],
                "optimal_makespan": instance["optimal_makespan"],
                "turns": turns,
                "atomic_forecast": atomic_forecast,
                "continue_forecast": plan_continue_forecast,
                "final_quality_forecast": final_quality_forecast,
                "final_continue_forecast": final_continue_forecast,
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
                "wall_s": total_wall_seconds,
                "total_wall_seconds": total_wall_seconds,
                "turn_count": len(turns),
                "subtasks_used": len([turn for turn in turns if turn["phase"] == "exec"]),
                "turn1_died": turn1_died,
                "subtask_killed_count": subtask_killed_count,
                "stop_reason": stop_reason,
                "revised_best_guess_downward": revised_best_guess_downward,
                "final_schedule_feasible": True,
                "final_schedule_source": final_schedule_source,
                "feasibility_failure_count": feasible_failures,
                "max_exec_turns_reached": max_exec_turns_reached,
                "valid_model_turns": valid_model_turns,
                "infeasible": feasible_failures > 0,
                "killed": subtask_killed_count > 0 or stop_reason in {"turn1_died", "subtask_timeout"},
                "error": error_message,
                "parse_fail": parse_fail,
            }


        @kbench.task(
            name=f"cjs_5x6_seed{SEED}",
            description=(
                f"Coupled jobshop 5x6 metagame spike for seed {SEED}. "
                "Planning turn + execution turns with thresholded gap forecasts."
            ),
        )
        def cjs_5x6_spike(llm):
            instance = _instance()
            row = run_protocol(llm, instance)
            kbench.assertions.assert_true(
                True,
                expectation=(
                    f"CJS_5x6 seed={row['seed']} model={row['model']} stop_reason={row['stop_reason']} "
                    f"gap_pct={row['gap_pct']:.2f} score={row['score']:.2f} subtasks_used={row['subtasks_used']} "
                    f"error={row['error']}"
                ),
            )
            return row
        """
    )
)


def build_instance_payload(seed: int) -> dict[str, object]:
    instance = build_instance(seed=seed, n_jobs=N_JOBS, n_machines=N_MACHINES)
    return {
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
        "optimal_schedule": instance.optimal_schedule,
        "optimal_makespan": instance.optimal_makespan,
        "problem_statement": instance.problem_statement,
    }


def render_task() -> str:
    payload = {str(seed): build_instance_payload(seed) for seed in SEEDS}
    instance_json = json.dumps(payload, indent=2, sort_keys=True)
    return TASK_TEMPLATE.substitute(INSTANCE_JSON=instance_json)


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_task(), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
