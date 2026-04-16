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
    parse_plan_turn,
)
from harness.render_nl import render_nl
from harness.scoring import score_portfolio, score_solo
from verifiers import CLASS_TO_VERIFIER

try:
    from kaggle_benchmarks import chats as kbench_chats
    from kaggle_benchmarks import contexts as kbench_contexts
except Exception:  # pragma: no cover - local tests do not require kaggle_benchmarks.
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
    instance_nl = render_nl(instance, cls)
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

    with _chat_session(name=f"run-{cls}-{difficulty}-seed{seed}", system_prompt=system_prompt):
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
            stop_reason = "error"
        elif plan_response["timed_out"]:
            stop_reason = "wall_budget"
            error = f"plan turn timed out after {PLAN_TURN_BUDGET_S}s"
        elif plan_parsed is None:
            stop_reason = "error"
            error = "plan turn parse failed"
        else:
            next_sub = plan_parsed.get("next_sub")
            if not next_sub:
                stop_reason = "error"
                error = "plan turn omitted NEXT_SUB"
            else:
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

                    try:
                        exec_response = _call_model(
                            llm=llm,
                            prompt_text=exec_prompt,
                            timeout_s=expected_turn_s,
                        )
                    except Exception as exc:  # noqa: BLE001
                        exec_response = {"text": "", "timed_out": False, "wall_s": time.monotonic() - run_start}
                        error = f"{type(exc).__name__}: {exc}"
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
                        stop_reason = "wall_budget"
                        error = f"exec turn {turn_index} timed out after {expected_turn_s}s"
                        break

                    exec_parsed = parse_exec_turn(
                        exec_response["text"],
                        cls=cls,
                        expected_subtask_id=next_sub["id"],
                    )
                    if exec_parsed is None:
                        stop_reason = "error"
                        error = f"exec turn {turn_index} parse failed"
                        break

                    parsed = exec_parsed
                    last_emitted_best_guess = exec_parsed["best_guess"]
                    last_eval = _evaluate_submission(
                        cls=cls,
                        instance=instance,
                        submission=last_emitted_best_guess,
                        components=components,
                    )

                    if _is_prompt_worthy(last_eval):
                        current_best = last_eval["submission"]
                        current_eval = last_eval

                    if exec_parsed["decision"] == "stop":
                        stop_reason = "decision_stop"
                        break

                    next_sub = exec_parsed["next_sub"]
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
                parsed_cf = parse_exec_turn(
                    cf_response["text"],
                    cls=cls,
                    expected_subtask_id=cf_turn_index - 1,
                    require_decision=False,
                )
                if parsed_cf is None:
                    error = error or "counterfactual turn parse failed"
                else:
                    cf_parsed = parsed_cf
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
        "error": error,
    }


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
