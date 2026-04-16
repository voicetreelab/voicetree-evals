from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from analyze import print_summary
from gemini_client import DEFAULT_MODELS, load_local_env
from jobshop_instance import build_instance
from protocol import run_protocol

DEFAULT_SEEDS = [1, 2, 3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Codex MetaGame v2 coupled job-shop local spike.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help="Gemini model ids to run.",
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
        default=6,
        help="Number of jobs in each factory instance.",
    )
    parser.add_argument(
        "--n-machines",
        type=int,
        default=7,
        help="Number of machines in each factory.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run the 3x4 single-model smoke configuration.",
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
        default=None,
        help="Optional instance prefilter: regenerate deterministically until baseline gap meets this percentage.",
    )
    return parser.parse_args()


def default_output_path() -> Path:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return results_dir / f"spike_{stamp}.jsonl"


def main() -> None:
    args = parse_args()
    load_local_env()

    models = args.models
    seeds = args.seeds
    n_jobs = args.n_jobs
    n_machines = args.n_machines
    min_baseline_gap_pct = args.min_baseline_gap_pct
    if args.smoke:
        models = ["gemini-2.5-pro"]
        seeds = [1]
        n_jobs = 3
        n_machines = 4

    output_path = args.output or default_output_path()
    rows: list[dict] = []

    with output_path.open("w", encoding="utf-8") as handle:
        for seed in seeds:
            instance = build_instance(
                seed=seed,
                n_jobs=n_jobs,
                n_machines=n_machines,
                min_baseline_gap_pct=min_baseline_gap_pct,
            )
            for model in models:
                print(f"running seed={seed} model={model} size={n_jobs}x{n_machines}")
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
