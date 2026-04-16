from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from gemini_client import load_local_env
from portfolio_problem import build_portfolio
from protocol import run_protocol

DEFAULT_MODEL = "models/gemini-3-pro-preview"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local portfolio metagame spike.")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Gemini model id to run.",
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
        help="Optional output JSON path. Defaults to results/portfolio_spike_<timestamp>.json",
    )
    return parser.parse_args()


def default_output_path() -> Path:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return results_dir / f"portfolio_spike_{stamp}.json"


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

    print(f"running model={args.model}")
    result = run_protocol(problems, args.model)

    output_path = args.output or default_output_path()
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"\nresult written to {output_path}")
    print_summary(result)


def print_summary(result: dict[str, object]) -> None:
    print("\nportfolio result:")
    print(f"  stop_reason={result['stop_reason']}")
    print(f"  turn_count={result['turn_count']}")
    print(f"  turn1_wall_seconds={float(result['turn1_wall_seconds']):.2f}")
    print(f"  total_wall_seconds={float(result['total_wall_seconds']):.2f}")
    print(f"  gross_value={float(result['session_value_sum']):.2f}")
    print(f"  time_cost={float(result['session_time_cost']):.2f}")
    print(f"  net_score={float(result['session_net_score']):.2f}")
    problems = result.get("problems", {})
    if isinstance(problems, dict):
        for problem_id in sorted(problems):
            problem = problems[problem_id]
            if not isinstance(problem, dict):
                continue
            print(
                f"  {problem_id}: final={_fmt_metric(float(problem['final_score']))} "
                f"value={float(problem['value_captured']):.2f}/{problem['value_cap']} "
                f"subtasks={problem['subtasks_executed']}"
            )


def _fmt_metric(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.3f}"


if __name__ == "__main__":
    main()
