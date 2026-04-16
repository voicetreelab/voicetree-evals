from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from analyze import print_summary
from gemini_client import load_local_env
from protocol import run_protocol
from steiner_coloring_instance import build_instance

DEFAULT_MODELS = ["gemini-3.1-pro-preview"]
DEFAULT_SEEDS = [1, 2, 3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Steiner x coloring composite local spike.")
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
        "--n",
        type=int,
        default=8,
        help="Number of villages in the generated instance.",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=3,
        help="k-nearest neighborhood size for generated cable graphs.",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run only seed 1 with the default model.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSONL path. Defaults to results/steiner_color_<timestamp>.jsonl",
    )
    parser.add_argument(
        "--skip-exact-gold",
        action="store_true",
        help="Skip exact gold solving and run in exploratory mode with baseline-only scoring context.",
    )
    return parser.parse_args()


def default_output_path() -> Path:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return results_dir / f"steiner_color_{stamp}.jsonl"


def main() -> None:
    args = parse_args()
    load_local_env()

    models = args.models
    seeds = args.seeds
    if args.smoke:
        models = [DEFAULT_MODELS[0]]
        seeds = [1]

    output_path = args.output or default_output_path()
    rows: list[dict] = []

    with output_path.open("w", encoding="utf-8") as handle:
        for seed in seeds:
            instance = build_instance(seed=seed, n=args.n, k=args.k, skip_exact_gold=args.skip_exact_gold)
            print(
                "seed="
                f"{seed} baseline={instance.baseline_cost} cable_only={instance.cable_only_cost} "
                f"optimal={instance.optimal_cost} skip_exact_gold={args.skip_exact_gold}"
            )
            for model in models:
                print(f"running seed={seed} model={model} n={args.n} k={args.k}")
                try:
                    row = run_protocol(instance, model)
                except Exception as exc:
                    row = {
                        "model": model,
                        "seed": seed,
                        "n": args.n,
                        "k": args.k,
                        "skip_exact_gold": args.skip_exact_gold,
                        "error": str(exc),
                    }
                rows.append(row)
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                handle.flush()

    print(f"\nresults written to {output_path}")
    print_summary(rows)


if __name__ == "__main__":
    main()
