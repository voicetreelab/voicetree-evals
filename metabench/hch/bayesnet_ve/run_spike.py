from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from bayesnet_instance import build_instance
from gemini_client import DEFAULT_MODELS, load_local_env
from protocol import run_protocol

DEFAULT_SEEDS = [1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Bayesian VE local spike.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help="Gemini model ids to run. Defaults to one Gemini 3 Pro configuration.",
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=DEFAULT_SEEDS,
        help="Instance seeds to run.",
    )
    parser.add_argument(
        "--requested-total-variables",
        type=int,
        default=22,
        help="Initial variable count request. The builder may escalate to 26-28 if 22 is too easy.",
    )
    parser.add_argument(
        "--max-generation-attempts",
        type=int,
        default=16,
        help="How many deterministic instance candidates to try at each size.",
    )
    parser.add_argument(
        "--random-order-samples",
        type=int,
        default=1000,
        help="How many random elimination orders to search when approximating the gold peak factor size.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSONL path. Defaults to results/bayesnet_ve_gemini3pro_seed1_planstate_<date>.jsonl",
    )
    return parser.parse_args()


def default_output_path(models: list[str], seeds: list[int]) -> Path:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    if models == DEFAULT_MODELS and seeds == DEFAULT_SEEDS:
        return results_dir / f"bayesnet_ve_gemini3pro_seed1_planstate_{stamp}.jsonl"
    detailed = datetime.now().strftime("%Y%m%d_%H%M%S")
    return results_dir / f"bayesnet_ve_spike_{detailed}.jsonl"


def print_summary(rows: list[dict]) -> None:
    for row in rows:
        if "error" in row:
            print(f"{row['model']} seed={row['seed']} ERROR: {row['error']}")
            continue
        gap_text = "NA" if row["gap_nats"] is None else f"{row['gap_nats']:.4f}"
        final_p = "NA" if row["final_p_query_given_evidence"] is None else f"{row['final_p_query_given_evidence']:.6f}"
        print(
            f"{row['model']} seed={row['seed']} vars={row['total_variables']} "
            f"p_hat={final_p} p*={row['exact_posterior']:.6f} gap_nats={gap_text} "
            f"axis={row['declared_elimination_axis']} exec_turns={row['exec_turn_count']} "
            f"stop={row['stop_reason']} wall={row['total_wall_seconds']:.2f}s"
        )


def main() -> None:
    args = parse_args()
    load_local_env()

    output_path = args.output or default_output_path(args.models, args.seeds)
    rows: list[dict] = []

    with output_path.open("w", encoding="utf-8") as handle:
        for seed in args.seeds:
            instance = build_instance(
                seed=seed,
                requested_total_variables=args.requested_total_variables,
                max_generation_attempts=args.max_generation_attempts,
                random_order_samples=args.random_order_samples,
            )
            for model in args.models:
                print(
                    "running "
                    f"seed={seed} model={model} requested_vars={args.requested_total_variables} "
                    f"actual_vars={instance.total_variables} query={instance.query_variable}"
                )
                try:
                    row = run_protocol(instance, model)
                except Exception as exc:
                    row = {
                        "model": model,
                        "seed": seed,
                        "requested_total_variables": args.requested_total_variables,
                        "total_variables": instance.total_variables,
                        "error": str(exc),
                    }
                rows.append(row)
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                handle.flush()

    print(f"\nresults written to {output_path}")
    print_summary(rows)


if __name__ == "__main__":
    main()
