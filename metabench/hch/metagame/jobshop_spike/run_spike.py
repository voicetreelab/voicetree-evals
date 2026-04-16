from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from gemini_client import DEFAULT_MODELS, load_local_env
from jobshop_spike.analyze import print_summary
from jobshop_spike.jobshop_instance import build_instance
from jobshop_spike.protocol import run_protocol

DEFAULT_SEEDS = [1, 2, 3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local Gemini jobshop budget-metagame spike.")
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
        default=12,
        help="Number of jobs in each generated instance.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSONL path. Defaults to jobshop_spike/results/jobshop_<timestamp>.jsonl",
    )
    return parser.parse_args()


def default_output_path() -> Path:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return results_dir / f"jobshop_{stamp}.jsonl"


def main() -> None:
    args = parse_args()
    load_local_env()
    output_path = args.output or default_output_path()
    rows: list[dict] = []

    with output_path.open("w", encoding="utf-8") as handle:
        for seed in args.seeds:
            instance = build_instance(seed=seed, n_jobs=args.n_jobs)
            for model in args.models:
                print(f"running seed={seed} model={model}")
                try:
                    row = run_protocol(instance, model)
                except Exception as exc:
                    row = {
                        "model": model,
                        "arm": "canonical_smart",
                        "seed": seed,
                        "n_jobs": args.n_jobs,
                        "error": str(exc),
                    }
                rows.append(row)
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                handle.flush()

    print(f"\nresults written to {output_path}")
    print_summary(rows)


if __name__ == "__main__":
    main()
