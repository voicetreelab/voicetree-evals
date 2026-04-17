from __future__ import annotations

import json
import threading
import time
from contextlib import nullcontext
from typing import Any

from harness.prompt import (
    build_exec_prompt,
    build_force_continue_prompt,
    build_system_prompt,
    build_turn1_prompt,
)
from harness.protocol import (
    CF_RESERVE_S,
    MAX_EXEC_TURNS,
    PLAN_TURN_BUDGET_S,
    TOTAL_BUDGET_S,
    parse_exec_turn,
    parse_exec_turn_partial,
    parse_plan_turn,
)
from harness.render_nl import render_nl
from harness.scoring import score_portfolio, score_solo
from verifiers import CLASS_TO_VERIFIER

try:
    import kaggle_benchmarks as kbench
    from kaggle_benchmarks import chats as kbench_chats
    from kaggle_benchmarks import contexts as kbench_contexts
except Exception:  # pragma: no cover - local tests do not require kaggle_benchmarks.
    kbench = None
    kbench_chats = None
    kbench_contexts = None


def run_instance(
    llm: Any,
    instance: dict[str, Any],
    cls: str,
    difficulty: str,
    seed: int,
    gold_objective: float,
    baseline_objective: float,
    value_cap: float,
    *,
    components: list[Any] | None = None,
) -> dict[str, Any]:
    del gold_objective, baseline_objective, value_cap  # encoded in the instance/components payloads.

    system_prompt = build_system_prompt()
    instance_nl = render_nl(instance, cls, components=components)
    run_start = time.monotonic()

    transcript: list[dict[str, str]] = []
    parsed: dict[str, Any] = {}
    cf_parsed: dict[str, Any] = {}
    error: str | None = None
    stop_reason = "error"
    n_exec_turns = 0

    current_best = _initial_best_guess(instance, cls=cls, components=components)
    current_eval = _evaluate_submission(
        cls=cls,
        instance=instance,
        submission=current_best,
        components=components,
    )
    last_emitted_best_guess = current_best
    last_eval = current_eval
    last_subtask: dict[str, Any] | None = None
    subtask_history: list[dict[str, Any]] = []
    parse_events: list[dict[str, Any]] = []

    label = f"{cls}-{difficulty}-s{seed}"

    with _chat_session(name=f"run-{cls}-{difficulty}-seed{seed}", system_prompt=system_prompt):
        print(f"  [{label}] plan turn (budget={PLAN_TURN_BUDGET_S}s)...", flush=True)
        try:
            plan_response = _call_model(
                llm=llm,
                prompt_text=build_turn1_prompt(instance_nl, cls=cls),
                timeout_s=PLAN_TURN_BUDGET_S,
            )
        except Exception as exc:  # noqa: BLE001
            plan_response = {"text": "", "timed_out": False, "wall_s": time.monotonic() - run_start}
            error = f"{type(exc).__name__}: {exc}"

        if plan_response["text"]:
            transcript.append({"role": "assistant", "content": plan_response["text"]})

        plan_parsed = None
        if error is None and not plan_response["timed_out"]:
            plan_parsed = parse_plan_turn(plan_response["text"], cls=cls)

        if error is not None:
            print(f"  [{label}] plan ERROR: {error} ({plan_response['wall_s']:.1f}s)", flush=True)
            stop_reason = "error"
        elif plan_response["timed_out"]:
            print(f"  [{label}] plan TIMEOUT ({plan_response['wall_s']:.1f}s)", flush=True)
            stop_reason = "wall_budget"
            error = f"plan turn timed out after {PLAN_TURN_BUDGET_S}s"
        elif plan_parsed is None:
            print(f"  [{label}] plan PARSE FAILED ({plan_response['wall_s']:.1f}s)", flush=True)
            stop_reason = "error"
            error = "plan turn parse failed"
        else:
            next_sub = plan_parsed.get("next_sub")
            if not next_sub:
                print(f"  [{label}] plan PARSE FAILED — no NEXT_SUB ({plan_response['wall_s']:.1f}s)", flush=True)
                stop_reason = "error"
                error = "plan turn omitted NEXT_SUB"
            else:
                print(f"  [{label}] plan ✓ ({plan_response['wall_s']:.1f}s)", flush=True)
                turn_index = 2
                while next_sub is not None:
                    if n_exec_turns >= MAX_EXEC_TURNS:
                        stop_reason = "turn_cap"
                        break

                    elapsed_s = time.monotonic() - run_start
                    expected_turn_s = int(next_sub.get("time_budget_s", 0))
                    if elapsed_s + expected_turn_s > TOTAL_BUDGET_S - CF_RESERVE_S:
                        stop_reason = "wall_budget"
                        break

                    exec_prompt = build_exec_prompt(
                        instance_nl=instance_nl,
                        cls=cls,
                        turn_index=turn_index,
                        transcript=_render_transcript(transcript),
                        elapsed_s=elapsed_s,
                        current_best=current_best,
                        last_subtask=last_subtask,
                        subtask_history=subtask_history,
                    )

                    print(f"  [{label}] exec turn {turn_index} (budget={expected_turn_s}s, elapsed={elapsed_s:.0f}s)...", flush=True)
                    try:
                        exec_response = _call_model(
                            llm=llm,
                            prompt_text=exec_prompt,
                            timeout_s=expected_turn_s,
                        )
                    except Exception as exc:  # noqa: BLE001
                        exec_response = {"text": "", "timed_out": False, "wall_s": time.monotonic() - run_start}
                        error = f"{type(exc).__name__}: {exc}"
                        print(f"  [{label}] exec {turn_index} ERROR: {error}", flush=True)
                        stop_reason = "error"
                        break

                    if exec_response["text"]:
                        transcript.append({"role": "assistant", "content": exec_response["text"]})

                    n_exec_turns += 1
                    last_subtask = {
                        "id": next_sub["id"],
                        "desc": next_sub["desc"],
                        "budgeted_s": expected_turn_s,
                        "actual_s": exec_response["wall_s"],
                    }
                    subtask_history.append(last_subtask)

                    if exec_response["timed_out"]:
                        print(f"  [{label}] exec {turn_index} TIMEOUT ({exec_response['wall_s']:.1f}s)", flush=True)
                        stop_reason = "wall_budget"
                        error = f"exec turn {turn_index} timed out after {expected_turn_s}s"
                        break

                    parse_outcome = _parse_exec_with_rescue(
                        llm=llm,
                        raw_text=exec_response["text"],
                        cls=cls,
                        expected_subtask_id=next_sub["id"],
                        require_decision=True,
                    )
                    exec_parsed = parse_outcome["parsed"]
                    parse_events.append(
                        {
                            "turn_index": turn_index,
                            "mode": parse_outcome["mode"],
                            "missing_or_invalid": parse_outcome["missing_or_invalid"],
                        }
                    )
                    if exec_parsed is None:
                        print(f"  [{label}] exec {turn_index} PARSE FAILED ({exec_response['wall_s']:.1f}s)", flush=True)
                        stop_reason = "error"
                        error = f"exec turn {turn_index} parse failed"
                        break

                    parsed = exec_parsed
                    if exec_parsed.get("best_guess") is not None:
                        last_emitted_best_guess = exec_parsed["best_guess"]
                        last_eval = _evaluate_submission(
                            cls=cls,
                            instance=instance,
                            submission=last_emitted_best_guess,
                            components=components,
                        )

                        feasible_flag = last_eval.get("feasible", False)
                        gap = last_eval.get("gap_pct", 100.0)
                        mode_suffix = "" if parse_outcome["mode"] == "strict" else f" via {parse_outcome['mode']}"
                        print(
                            f"  [{label}] exec {turn_index} ✓ feasible={feasible_flag} gap={gap:.1f}%"
                            f"{mode_suffix} ({exec_response['wall_s']:.1f}s)",
                            flush=True,
                        )

                        if _is_prompt_worthy(last_eval):
                            current_best = last_eval["submission"]
                            current_eval = last_eval
                    else:
                        print(
                            f"  [{label}] exec {turn_index} parsed without usable BEST_GUESS"
                            f" via {parse_outcome['mode']} ({exec_response['wall_s']:.1f}s)",
                            flush=True,
                        )

                    if exec_parsed.get("decision") == "stop":
                        stop_reason = "decision_stop"
                        break

                    next_sub = exec_parsed.get("next_sub")
                    if exec_parsed.get("decision") != "continue" or next_sub is None:
                        print(
                            f"  [{label}] exec {turn_index} rescued partial output but missing control fields",
                            flush=True,
                        )
                        stop_reason = "error"
                        error = f"exec turn {turn_index} parse failed"
                        break
                    turn_index += 1

    stop_eval = last_eval if last_eval is not None else current_eval
    score_at_stop = _score_evaluation(stop_eval, wall_s=time.monotonic() - run_start)
    score_after_cf = score_at_stop

    if stop_reason == "decision_stop":
        cf_turn_index = n_exec_turns + 2
        cf_timeout_s = min(CF_RESERVE_S, max(0, int(TOTAL_BUDGET_S - (time.monotonic() - run_start))))
        if cf_timeout_s >= 1:
            cf_prompt = build_force_continue_prompt(
                instance_nl=instance_nl,
                cls=cls,
                turn_index=cf_turn_index,
                transcript=_render_transcript(transcript),
                elapsed_s=time.monotonic() - run_start,
                current_best=last_emitted_best_guess,
                last_subtask=last_subtask,
                subtask_history=subtask_history,
            )
            try:
                cf_response = _call_model(llm=llm, prompt_text=cf_prompt, timeout_s=cf_timeout_s)
            except Exception as exc:  # noqa: BLE001
                cf_response = {"text": "", "timed_out": False, "wall_s": time.monotonic() - run_start}
                if error is None:
                    error = f"{type(exc).__name__}: {exc}"

            if cf_response["text"]:
                transcript.append({"role": "assistant", "content": cf_response["text"]})

            if cf_response["timed_out"]:
                error = error or f"counterfactual turn timed out after {cf_timeout_s}s"
            else:
                cf_parse_outcome = _parse_exec_with_rescue(
                    llm=llm,
                    raw_text=cf_response["text"],
                    cls=cls,
                    expected_subtask_id=cf_turn_index - 1,
                    require_decision=False,
                )
                parsed_cf = cf_parse_outcome["parsed"]
                parse_events.append(
                    {
                        "turn_index": cf_turn_index,
                        "mode": f"cf_{cf_parse_outcome['mode']}",
                        "missing_or_invalid": cf_parse_outcome["missing_or_invalid"],
                    }
                )
                if parsed_cf is None:
                    error = error or "counterfactual turn parse failed"
                else:
                    cf_parsed = parsed_cf
                    if parsed_cf.get("best_guess") is not None:
                        cf_eval = _evaluate_submission(
                            cls=cls,
                            instance=instance,
                            submission=parsed_cf["best_guess"],
                            components=components,
                        )
                        score_after_cf = _score_evaluation(cf_eval, wall_s=time.monotonic() - run_start)
        else:
            error = error or "counterfactual turn skipped because no wall budget remained"

    wall_s = time.monotonic() - run_start
    cf_delta = score_after_cf - score_at_stop
    return {
        "score": score_after_cf,
        "score_at_stop": score_at_stop,
        "score_after_cf": score_after_cf,
        "cf_delta": cf_delta,
        "wall_s": wall_s,
        "n_exec_turns": n_exec_turns,
        "stop_reason": stop_reason,
        "transcript": transcript,
        "parsed": parsed,
        "cf_parsed": cf_parsed,
        "parse_events": parse_events,
        "error": error,
    }


def _parse_exec_with_rescue(
    *,
    llm: Any,
    raw_text: str,
    cls: str | None,
    expected_subtask_id: int | None,
    require_decision: bool,
) -> dict[str, Any]:
    strict = parse_exec_turn(
        raw_text,
        cls=cls,
        expected_subtask_id=expected_subtask_id,
        require_decision=require_decision,
    )
    if strict is not None:
        return {"parsed": strict, "mode": "strict", "missing_or_invalid": []}

    partial = parse_exec_turn_partial(
        raw_text,
        cls=cls,
        expected_subtask_id=expected_subtask_id,
        require_decision=require_decision,
    )
    missing_or_invalid = list(partial.pop("missing_or_invalid", []))
    if partial.get("best_guess") is not None:
        return {
            "parsed": partial,
            "mode": "partial_rescue",
            "missing_or_invalid": missing_or_invalid,
        }

    judge_llm = _get_judge_llm()
    if judge_llm is None:
        return {"parsed": partial or None, "mode": "strict_parse_failed", "missing_or_invalid": missing_or_invalid}

    rescue_prompt = _build_exec_rescue_prompt(
        raw_text=raw_text,
        cls=cls,
        expected_subtask_id=expected_subtask_id,
        require_decision=require_decision,
        missing_or_invalid=missing_or_invalid,
    )
    try:
        rescue_response = _call_model(llm=judge_llm, prompt_text=rescue_prompt, timeout_s=45)
    except Exception:
        return {"parsed": partial or None, "mode": "strict_parse_failed", "missing_or_invalid": missing_or_invalid}
    if rescue_response["timed_out"] or not rescue_response["text"]:
        return {"parsed": partial or None, "mode": "strict_parse_failed", "missing_or_invalid": missing_or_invalid}

    rescued = parse_exec_turn_partial(
        rescue_response["text"],
        cls=cls,
        expected_subtask_id=expected_subtask_id,
        require_decision=require_decision,
    )
    rescued.pop("missing_or_invalid", None)
    merged = dict(partial)
    for key, value in rescued.items():
        if key not in merged:
            merged[key] = value

    mode = "judge_rescue" if merged.get("best_guess") is not None else "strict_parse_failed"
    return {"parsed": merged or None, "mode": mode, "missing_or_invalid": missing_or_invalid}


def _get_judge_llm() -> Any | None:
    if kbench is not None and hasattr(kbench, "judge_llm"):
        return getattr(kbench, "judge_llm")
    return None


def _build_exec_rescue_prompt(
    *,
    raw_text: str,
    cls: str | None,
    expected_subtask_id: int | None,
    require_decision: bool,
    missing_or_invalid: list[str],
) -> str:
    subtask_label = "SUB_N"
    if expected_subtask_id is not None:
        subtask_label = f"SUB_{expected_subtask_id}"

    decision_rule = "Include `DECISION`." if require_decision else "Do not include `DECISION` unless explicit."
    missing_text = ", ".join(missing_or_invalid) if missing_or_invalid else "unknown"

    return (
        "You are extracting structured fields from a prior model response. Do not solve the task again.\n\n"
        f"Problem class: {cls or 'unknown'}\n"
        f"Fields missing or invalid in strict parse: {missing_text}\n\n"
        "Return only literal labelled lines that can be recovered confidently from the raw response.\n"
        f"Allowed labels: `{subtask_label}`, `BEST_GUESS`, `UPDATED_PLAN_STATE`, `QUALITY_FORECAST`, "
        "`CONTINUE_FORECAST`, `DECISION`, `NEXT_SUB`.\n"
        f"{decision_rule} Include `NEXT_SUB` only if the decision is `continue`.\n"
        "If a field cannot be recovered confidently, omit it.\n\n"
        "RAW RESPONSE:\n"
        f"{raw_text.strip()}"
    )


def _chat_session(*, name: str, system_prompt: str):
    if kbench_chats is None:
        return nullcontext()
    return kbench_chats.new(name=name, system_instructions=system_prompt)


def _call_model(llm: Any, prompt_text: str, timeout_s: int) -> dict[str, Any]:
    start = time.monotonic()
    result: list[Any] = [None]
    error: list[BaseException | None] = [None]
    current_context = kbench_contexts.get_current() if kbench_contexts is not None else None

    def _invoke() -> None:
        try:
            if current_context is not None and kbench_contexts is not None:
                kbench_contexts.set_from_context(current_context)
            result[0] = _prompt_once(llm, prompt_text)
        except BaseException as exc:  # noqa: BLE001
            error[0] = exc

    thread = threading.Thread(target=_invoke, daemon=True)
    thread.start()
    thread.join(timeout=timeout_s)
    wall_s = time.monotonic() - start

    if thread.is_alive():
        return {"text": "", "timed_out": True, "wall_s": wall_s}
    if error[0] is not None:
        raise error[0]

    raw = result[0]
    if isinstance(raw, str):
        text = raw
    else:
        text = str(getattr(raw, "content", raw) or "")
    return {"text": text.strip(), "timed_out": wall_s > timeout_s, "wall_s": wall_s}


def _prompt_once(llm: Any, prompt_text: str) -> Any:
    if hasattr(llm, "prompt"):
        prompt = getattr(llm, "prompt")
        try:
            return prompt(prompt_text, temperature=0)
        except TypeError:
            return prompt(prompt_text)
    if callable(llm):
        return llm(prompt_text)
    raise TypeError("llm must expose .prompt(message) or be callable")


def _render_transcript(transcript: list[dict[str, str]]) -> str:
    chunks = []
    for index, entry in enumerate(transcript, start=1):
        chunks.append(f"TURN_{index}_MODEL_RESPONSE:\n{entry['content']}")
    return "\n\n".join(chunks)


def _initial_best_guess(
    instance: dict[str, Any],
    *,
    cls: str,
    components: list[Any] | None,
) -> dict[str, Any] | None:
    baseline = instance.get("baseline_submission")
    if isinstance(baseline, dict):
        return baseline
    if cls != "portfolio" or not components:
        return None

    answers: dict[str, Any] = {}
    for component in components:
        if not isinstance(component, dict):
            continue
        problem_id = component.get("problem_id")
        sub_instance = component.get("sub_instance")
        if not isinstance(problem_id, str) or not isinstance(sub_instance, dict):
            continue
        baseline_submission = sub_instance.get("baseline_submission")
        if baseline_submission is None:
            baseline_submission = sub_instance.get("baseline_answer")
        if baseline_submission is None:
            baseline_tour = sub_instance.get("baseline_tour")
            if baseline_tour is not None:
                baseline_submission = {"tour": list(baseline_tour)}
        if baseline_submission is not None:
            answers[problem_id] = baseline_submission
    return answers or None


def _evaluate_submission(
    *,
    cls: str,
    instance: dict[str, Any],
    submission: Any,
    components: list[Any] | None,
) -> dict[str, Any]:
    if cls == "portfolio":
        return _evaluate_portfolio_submission(submission=submission, components=components)

    verifier = CLASS_TO_VERIFIER.get(cls)
    if verifier is None:
        return {
            "mode": "solo",
            "gap_pct": 100.0,
            "feasible": False,
            "details": {"failure_reason": f"missing verifier for class {cls}"},
            "submission": submission if isinstance(submission, dict) else None,
        }

    gap_pct, feasible, details = verifier(instance, submission)
    normalized_submission = details.get("normalized_submission", submission)
    return {
        "mode": "solo",
        "gap_pct": float(gap_pct),
        "feasible": bool(feasible),
        "details": details,
        "submission": normalized_submission if isinstance(normalized_submission, dict) else submission,
    }


def _evaluate_portfolio_submission(
    *,
    submission: Any,
    components: list[Any] | None,
) -> dict[str, Any]:
    if not isinstance(submission, dict):
        return {
            "mode": "portfolio",
            "submission": {},
            "components": [],
            "details": {"failure_reason": "portfolio submission must be an object"},
        }

    raw_answers = submission.get("answers", submission)
    if not isinstance(raw_answers, dict):
        raw_answers = {}

    component_rows: list[dict[str, Any]] = []
    normalized_submission: dict[str, Any] = {}
    for component in components or []:
        if not isinstance(component, dict):
            continue

        problem_id = str(component.get("problem_id", "")).strip()
        component_cls = component.get("class")
        sub_instance = component.get("sub_instance")
        value_cap = float(component.get("value_cap", 0.0))
        verifier = CLASS_TO_VERIFIER.get(component_cls) if isinstance(component_cls, str) else None
        raw_component_submission = raw_answers.get(problem_id)

        if verifier is None or not isinstance(sub_instance, dict):
            component_rows.append(
                {
                    "problem_id": problem_id,
                    "class": component_cls,
                    "gap_pct": 100.0,
                    "feasible": False,
                    "value_cap": value_cap,
                    "details": {"failure_reason": f"missing verifier or instance for {problem_id}"},
                }
            )
            continue

        gap_pct, feasible, details = verifier(sub_instance, raw_component_submission)
        normalized_component = details.get("normalized_submission", raw_component_submission)
        normalized_submission[problem_id] = normalized_component
        component_rows.append(
            {
                "problem_id": problem_id,
                "class": component_cls,
                "gap_pct": float(gap_pct),
                "feasible": bool(feasible),
                "value_cap": value_cap,
                "details": details,
            }
        )

    return {
        "mode": "portfolio",
        "submission": normalized_submission,
        "components": component_rows,
        "details": {"components": component_rows},
    }


def _is_prompt_worthy(evaluation: dict[str, Any]) -> bool:
    if evaluation["mode"] == "portfolio":
        return bool(evaluation["components"])
    return bool(evaluation["feasible"]) and isinstance(evaluation["submission"], dict)


def _score_evaluation(evaluation: dict[str, Any], *, wall_s: float) -> float:
    if evaluation["mode"] == "portfolio":
        return score_portfolio(evaluation["components"], wall_s)
    return score_solo(
        gap_pct=float(evaluation["gap_pct"]),
        feasible=bool(evaluation["feasible"]),
        wall_s=wall_s,
    )
