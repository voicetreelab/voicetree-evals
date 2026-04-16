from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from extract import (
    DEFAULT_EXTRACTOR_MODEL,
    extract_problem_answers,
    extract_session_metrics,
)
from gemini_client import load_local_env
from portfolio_problem import PreparedProblem, build_portfolio
from protocol import COST_PER_SECOND, MAX_TURNS, WALL_BUDGET_S, run_counterfactual_turn, run_main_loop

DEFAULT_MODEL = "models/gemini-3-pro-preview"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local portfolio v2 raw-transcript spike.")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Gemini model id to run for the main conversation loop.",
    )
    parser.add_argument(
        "--extractor-model",
        default=DEFAULT_EXTRACTOR_MODEL,
        help="Gemini model id to use for transcript extraction.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Instance seed to run.",
    )
    parser.add_argument(
        "--min-baseline-gap-pct",
        type=float,
        default=15.0,
        help="Minimum baseline-to-gold headroom required for each problem in preflight.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON path. Defaults to results/portfolio_v2_<timestamp>.json",
    )
    return parser.parse_args()


def default_output_path() -> Path:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return results_dir / f"portfolio_v2_{stamp}.json"


def transcript_output_path(result_path: Path) -> Path:
    return result_path.with_name(result_path.stem + "_transcript.md")


def extended_transcript_output_path(result_path: Path) -> Path:
    return result_path.with_name(result_path.stem + "_extended_transcript.md")


def main() -> None:
    args = parse_args()
    load_local_env()

    print(f"building portfolio seed={args.seed} min_gap={args.min_baseline_gap_pct:.1f}%")
    problems = build_portfolio(
        seed=args.seed,
        min_baseline_gap_pct=args.min_baseline_gap_pct,
    )
    print("preflight passed:")
    for problem in problems:
        print(
            f"  {problem.problem_id} {problem.short_label}: "
            f"baseline={_fmt_metric(problem.baseline_score)} "
            f"gold={_fmt_metric(problem.gold_score)} "
            f"gap={problem.baseline_gap_pct:.2f}% "
            f"gold_solve={problem.gold_wall_seconds:.2f}s"
        )

    print(f"running main loop model={args.model}")
    session, base_protocol = run_main_loop(problems, args.model)
    base_evaluation = evaluate_transcript(
        problems,
        base_protocol["transcript_text"],
        extractor_model=args.extractor_model,
        run_wall_seconds=float(base_protocol["total_wall_seconds"]),
        transcript_label="base",
    )

    counterfactual: dict[str, Any]
    if base_protocol["stop_reason"] in {"api_error", "turn_timeout"}:
        counterfactual = {
            "skipped": True,
            "skip_reason": f"base run ended with {base_protocol['stop_reason']}",
            "protocol": None,
            "evaluation": None,
            "comparison": None,
        }
    else:
        print("running forced counterfactual turn")
        counterfactual_protocol = run_counterfactual_turn(session, base_protocol)
        counterfactual_evaluation = evaluate_transcript(
            problems,
            counterfactual_protocol["transcript_text"],
            extractor_model=args.extractor_model,
            run_wall_seconds=float(base_protocol["total_wall_seconds"])
            + float(_branch_wall_seconds(counterfactual_protocol)),
            transcript_label="counterfactual",
        )
        counterfactual = {
            "skipped": False,
            "skip_reason": None,
            "protocol": counterfactual_protocol,
            "evaluation": counterfactual_evaluation,
            "comparison": compare_counterfactual(
                problems,
                base_evaluation,
                counterfactual_evaluation,
                branch_wall_seconds=_branch_wall_seconds(counterfactual_protocol),
            ),
        }

    output_path = args.output or default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    base_transcript_path = transcript_output_path(output_path)
    base_transcript_path.write_text(base_protocol["transcript_text"], encoding="utf-8")
    extended_transcript_path = None
    if not counterfactual["skipped"] and counterfactual["protocol"] is not None:
        extended_transcript_path = extended_transcript_output_path(output_path)
        extended_transcript_path.write_text(
            counterfactual["protocol"]["transcript_text"],
            encoding="utf-8",
        )

    result = {
        "model": args.model,
        "extractor_model": args.extractor_model,
        "seed": args.seed,
        "max_turns": MAX_TURNS,
        "wall_budget_s": WALL_BUDGET_S,
        "cost_per_second": COST_PER_SECOND,
        "preflight": build_preflight_summary(problems),
        "base_run": {
            "protocol": {
                **base_protocol,
                "transcript_path": str(base_transcript_path),
            },
            "evaluation": base_evaluation,
        },
        "stop_counterfactual": {
            **counterfactual,
            "protocol": (
                None
                if counterfactual["protocol"] is None
                else {
                    **counterfactual["protocol"],
                    "transcript_path": (
                        str(extended_transcript_path)
                        if extended_transcript_path is not None
                        else None
                    ),
                }
            ),
        },
    }

    output_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nresult written to {output_path}")
    print(f"base transcript written to {base_transcript_path}")
    if extended_transcript_path is not None:
        print(f"extended transcript written to {extended_transcript_path}")
    print_summary(result)


def evaluate_transcript(
    problems: list[PreparedProblem],
    transcript_text: str,
    *,
    extractor_model: str,
    run_wall_seconds: float,
    transcript_label: str,
) -> dict[str, Any]:
    extracted_answers = extract_problem_answers(
        problems,
        transcript_text,
        model_name=extractor_model,
    )
    session_metrics = extract_session_metrics(
        transcript_text,
        model_name=extractor_model,
    )

    problem_results: dict[str, Any] = {}
    value_sum = 0.0
    for problem in problems:
        extraction = extracted_answers[problem.problem_id]
        result = verify_extracted_problem(problem, extraction)
        problem_results[problem.problem_id] = result
        value_sum += float(result["value_captured"])

    time_cost = COST_PER_SECOND * run_wall_seconds
    return {
        "transcript_label": transcript_label,
        "problems": problem_results,
        "session_metrics": session_metrics,
        "session_value_sum": value_sum,
        "session_time_cost": time_cost,
        "session_net_score": value_sum - time_cost,
        "raw_transcript_stats": {
            "assistant_turns": sum(
                1
                for line in transcript_text.splitlines()
                if line.startswith("[ASSISTANT")
            ),
            "transcript_chars": len(transcript_text),
            "run_wall_seconds": run_wall_seconds,
            "extractor_total_tokens": _sum_extractor_tokens(
                extracted_answers,
                session_metrics,
            ),
        },
    }


def verify_extracted_problem(
    problem: PreparedProblem,
    extraction: dict[str, Any],
) -> dict[str, Any]:
    extracted_answer = extraction.get("answer")
    if not extraction["json_valid"]:
        return _fallback_problem_result(
            problem,
            extraction=extraction,
            failure_reason=f"extractor_invalid_json: {extraction['parse_error']}",
        )
    if extraction["missing"]:
        return _fallback_problem_result(
            problem,
            extraction=extraction,
            failure_reason="extractor_missing_answer",
        )

    outcome = problem.verify_answer(extracted_answer)
    extracted_answer_score = float(outcome.score) if outcome.score is not None else None
    extracted_answer_valid = bool(outcome.feasible and extracted_answer_score is not None)
    if not extracted_answer_valid:
        return _fallback_problem_result(
            problem,
            extraction=extraction,
            failure_reason=outcome.failure_reason or "verification_failed",
            verifier_outcome=outcome,
        )

    final_score = extracted_answer_score
    value_captured = problem.value_captured(final_score)
    return {
        "problem_id": problem.problem_id,
        "label": problem.label,
        "baseline_score": problem.baseline_score,
        "gold_score": problem.gold_score,
        "baseline_gap_pct": problem.baseline_gap_pct,
        "extracted_answer_valid": True,
        "extracted_answer_score": extracted_answer_score,
        "final_score_used": final_score,
        "value_cap": problem.value_cap,
        "value_captured": value_captured,
        "final_realized_bucket": problem.realized_bucket(final_score),
        "failure_reason": None,
        "extractor": extraction,
        "verification": {
            "feasible": outcome.feasible,
            "failure_reason": outcome.failure_reason,
            "details": outcome.details,
            "normalized_answer": outcome.normalized_answer,
        },
    }


def compare_counterfactual(
    problems: list[PreparedProblem],
    base_evaluation: dict[str, Any],
    extended_evaluation: dict[str, Any],
    *,
    branch_wall_seconds: float,
) -> dict[str, Any]:
    per_problem: dict[str, Any] = {}
    for problem in problems:
        base_problem = base_evaluation["problems"][problem.problem_id]
        extended_problem = extended_evaluation["problems"][problem.problem_id]
        base_score = float(base_problem["final_score_used"])
        extended_score = float(extended_problem["final_score_used"])
        if extended_score < base_score - 1e-9:
            delta_label = "improved"
        elif extended_score > base_score + 1e-9:
            delta_label = "degraded"
        else:
            delta_label = "same"
        per_problem[problem.problem_id] = {
            "delta_label": delta_label,
            "base_final_score": base_score,
            "extended_final_score": extended_score,
            "base_value_captured": float(base_problem["value_captured"]),
            "extended_value_captured": float(extended_problem["value_captured"]),
            "value_delta": float(extended_problem["value_captured"])
            - float(base_problem["value_captured"]),
        }

    base_value = float(base_evaluation["session_value_sum"])
    extended_value = float(extended_evaluation["session_value_sum"])
    branch_time_cost = COST_PER_SECOND * branch_wall_seconds
    return {
        "base_value_sum": base_value,
        "base_net_score": float(base_evaluation["session_net_score"]),
        "extended_value_sum": extended_value,
        "extended_net_score": float(extended_evaluation["session_net_score"]),
        "raw_value_delta": extended_value - base_value,
        "branch_wall_seconds": branch_wall_seconds,
        "branch_time_cost": branch_time_cost,
        "net_delta_after_cost": (extended_value - base_value) - branch_time_cost,
        "per_problem": per_problem,
    }


def build_preflight_summary(problems: list[PreparedProblem]) -> dict[str, Any]:
    return {
        problem.problem_id: {
            "label": problem.label,
            "baseline_score": problem.baseline_score,
            "gold_score": problem.gold_score,
            "gap_pct": problem.baseline_gap_pct,
            "value_cap": problem.value_cap,
            "gold_method": problem.gold_method,
            "gold_wall_seconds": problem.gold_wall_seconds,
        }
        for problem in problems
    }


def _fallback_problem_result(
    problem: PreparedProblem,
    *,
    extraction: dict[str, Any],
    failure_reason: str,
    verifier_outcome: Any | None = None,
) -> dict[str, Any]:
    final_score = problem.baseline_score
    verification = None
    if verifier_outcome is not None:
        verification = {
            "feasible": verifier_outcome.feasible,
            "failure_reason": verifier_outcome.failure_reason,
            "details": verifier_outcome.details,
            "normalized_answer": verifier_outcome.normalized_answer,
        }
    return {
        "problem_id": problem.problem_id,
        "label": problem.label,
        "baseline_score": problem.baseline_score,
        "gold_score": problem.gold_score,
        "baseline_gap_pct": problem.baseline_gap_pct,
        "extracted_answer_valid": False,
        "extracted_answer_score": None,
        "final_score_used": final_score,
        "value_cap": problem.value_cap,
        "value_captured": problem.value_captured(final_score),
        "final_realized_bucket": problem.realized_bucket(final_score),
        "failure_reason": failure_reason,
        "extractor": extraction,
        "verification": verification,
    }


def _branch_wall_seconds(counterfactual_protocol: dict[str, Any]) -> float:
    branch_turn = counterfactual_protocol.get("turn")
    if not isinstance(branch_turn, dict):
        return 0.0
    wall_seconds = branch_turn.get("wall_seconds")
    if wall_seconds is None:
        return 0.0
    return float(wall_seconds)


def _sum_extractor_tokens(
    extracted_answers: dict[str, dict[str, Any]],
    session_metrics: dict[str, Any],
) -> int | None:
    values = []
    for extraction in extracted_answers.values():
        tokens = extraction.get("total_tokens")
        if tokens is not None:
            values.append(int(tokens))
    metrics_tokens = session_metrics.get("total_tokens")
    if metrics_tokens is not None:
        values.append(int(metrics_tokens))
    if not values:
        return None
    return sum(values)


def print_summary(result: dict[str, Any]) -> None:
    base = result["base_run"]["evaluation"]
    print("\nbase result:")
    print(f"  value_sum={float(base['session_value_sum']):.2f}")
    print(f"  time_cost={float(base['session_time_cost']):.2f}")
    print(f"  net_score={float(base['session_net_score']):.2f}")
    for problem_id, problem in sorted(base["problems"].items()):
        print(
            f"  {problem_id}: final={_fmt_metric(float(problem['final_score_used']))} "
            f"value={float(problem['value_captured']):.2f}/{problem['value_cap']} "
            f"valid={problem['extracted_answer_valid']}"
        )

    counterfactual = result["stop_counterfactual"]
    if counterfactual["skipped"]:
        print(f"\nstop-counterfactual skipped: {counterfactual['skip_reason']}")
        return

    comparison = counterfactual["comparison"]
    print("\nstop-counterfactual:")
    print(f"  extended_value_sum={float(comparison['extended_value_sum']):.2f}")
    print(f"  raw_value_delta={float(comparison['raw_value_delta']):.2f}")
    print(f"  branch_wall_seconds={float(comparison['branch_wall_seconds']):.2f}")
    print(f"  net_delta_after_cost={float(comparison['net_delta_after_cost']):.2f}")


def _fmt_metric(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.3f}"


if __name__ == "__main__":
    main()
