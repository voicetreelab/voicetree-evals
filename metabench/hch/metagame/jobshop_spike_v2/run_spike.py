from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from gemini_client import load_local_env
from jobshop_spike_v2.analyze import print_summary
from jobshop_spike_v2.jobshop_instance import build_instance
from jobshop_spike_v2.protocol import run_protocol

DEFAULT_MODEL = "gemini-3.1-pro-preview"
DEFAULT_SEEDS = [1, 2, 3]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the harder 5x6 multi-machine Gemini jobshop v2 spike.")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Gemini model id to run. Default is gemini-3.1-pro-preview.",
    )
    parser.add_argument(
        "--seeds",
        nargs="+",
        type=int,
        default=DEFAULT_SEEDS,
        help="Requested instance seeds to run.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSONL path. Defaults to jobshop_spike_v2/results/jobshop_v2_<timestamp>.jsonl",
    )
    return parser.parse_args()


def default_output_path() -> Path:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return results_dir / f"jobshop_v2_{stamp}.jsonl"


def main() -> None:
    args = parse_args()
    load_local_env()
    output_path = args.output or default_output_path()
    rows: list[dict] = []

    with output_path.open("w", encoding="utf-8") as handle:
        for seed in args.seeds:
            print(f"building seed={seed}")
            try:
                instance = build_instance(seed)
            except Exception as exc:
                row = {
                    "model": args.model,
                    "requested_seed": seed,
                    "error": f"instance build failed: {exc}",
                }
                rows.append(row)
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                handle.flush()
                continue

            print(
                "running "
                f"requested_seed={seed} source_seed={instance.source_seed} "
                f"baseline_gap_pct={instance.baseline_gap_pct:.2f} model={args.model}"
            )
            try:
                row = run_protocol(instance, args.model)
            except Exception as exc:
                row = {
                    "model": args.model,
                    "requested_seed": seed,
                    "source_seed": instance.source_seed,
                    "baseline_gap_pct": instance.baseline_gap_pct,
                    "error": str(exc),
                }
            rows.append(row)
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()

    print(f"\nresults written to {output_path}")
    print_summary(rows)


if __name__ == "__main__":
    main()
