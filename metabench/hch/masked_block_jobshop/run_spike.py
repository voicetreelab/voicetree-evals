from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from analyze import print_summary
from gemini_client import DEFAULT_MODELS, load_local_env
from jobshop_instance import build_instance
from protocol import run_protocol

DEFAULT_SEEDS = [1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the masked block jobshop local spike.")
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
        "--n-jobs",
        type=int,
        default=25,
        help="Requested number of jobs. If 25x15 fails to prove optimal in 10m, the builder falls back to 20x12.",
    )
    parser.add_argument(
        "--n-machines",
        type=int,
        default=15,
        help="Requested number of machines.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run the smaller 20x12 fallback-sized configuration.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSONL path. Defaults to results/spike_<timestamp>.jsonl",
    )
    parser.add_argument(
        "--min-baseline-gap-pct",
        type=float,
        default=20.0,
        help="Regenerate deterministically until the baseline objective gap meets this percentage.",
    )
    parser.add_argument(
        "--min-heuristic-spread-pct",
        type=float,
        default=5.0,
        help="Regenerate until the pre-flight heuristic spread exceeds this percentage.",
    )
    parser.add_argument(
        "--max-heuristic-spread-pct",
        type=float,
        default=35.0,
        help="Regenerate until the pre-flight heuristic spread is at most this percentage.",
    )
    parser.add_argument(
        "--cp-time-limit-s",
        type=float,
        default=600.0,
        help="CP-SAT time limit in seconds for the composite objective solve.",
    )
    return parser.parse_args()


def default_output_path() -> Path:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return results_dir / f"masked_block_spike_{stamp}.jsonl"


def main() -> None:
    args = parse_args()
    load_local_env()

    models = args.models
    seeds = args.seeds
    n_jobs = args.n_jobs
    n_machines = args.n_machines
    min_baseline_gap_pct = args.min_baseline_gap_pct
    min_heuristic_spread_pct = args.min_heuristic_spread_pct
    max_heuristic_spread_pct = args.max_heuristic_spread_pct
    cp_time_limit_s = args.cp_time_limit_s
    if args.smoke:
        models = DEFAULT_MODELS[:1]
        seeds = [1]
        n_jobs = 20
        n_machines = 12
        min_baseline_gap_pct = 10.0

    output_path = args.output or default_output_path()
    rows: list[dict] = []

    with output_path.open("w", encoding="utf-8") as handle:
        for seed in seeds:
            instance = build_instance(
                seed=seed,
                n_jobs=n_jobs,
                n_machines=n_machines,
                min_baseline_gap_pct=min_baseline_gap_pct,
                min_heuristic_spread_pct=min_heuristic_spread_pct,
                max_heuristic_spread_pct=max_heuristic_spread_pct,
                cp_time_limit_s=cp_time_limit_s,
            )
            for model in models:
                print(
                    "running "
                    f"seed={seed} model={model} requested={n_jobs}x{n_machines} actual={instance.n_jobs}x{instance.n_machines}"
                )
                try:
                    row = run_protocol(instance, model)
                except Exception as exc:
                    row = {
                        "model": model,
                        "seed": seed,
                        "n_jobs": n_jobs,
                        "n_machines": n_machines,
                        "error": str(exc),
                    }
                rows.append(row)
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                handle.flush()

    print(f"\nresults written to {output_path}")
    print_summary(rows)


if __name__ == "__main__":
    main()
