from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from analyze import print_summary
from gemini_client import DEFAULT_MODELS, load_local_env
from protocol import run_protocol
from tsp_instance import build_instance

DEFAULT_ARMS = ["greedy", "exhaustive", "smart"]
DEFAULT_SEEDS = [1, 2, 3, 4, 5]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local Gemini TSP budget-metagame spike.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help="Gemini model ids to run.",
    )
    parser.add_argument(
        "--arms",
        nargs="+",
        default=DEFAULT_ARMS,
        choices=DEFAULT_ARMS,
        help="Protocol arms to run.",
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=DEFAULT_SEEDS,
        help="Instance seeds to run.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSONL path. Defaults to results/spike_<timestamp>.jsonl",
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
    output_path = args.output or default_output_path()
    rows: list[dict] = []

    with output_path.open("w", encoding="utf-8") as handle:
        for seed in args.seeds:
            instance = build_instance(seed)
            for model in args.models:
                for arm in args.arms:
                    print(f"running seed={seed} model={model} arm={arm}")
                    try:
                        row = run_protocol(instance, model, arm)
                    except Exception as exc:
                        row = {
                            "model": model,
                            "arm": arm,
                            "seed": seed,
                            "error": str(exc),
                        }
                    rows.append(row)
                    handle.write(json.dumps(row, sort_keys=True) + "\n")
                    handle.flush()

    print(f"\nresults written to {output_path}")
    print_summary(rows)


if __name__ == "__main__":
    main()
