from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from analyze import print_summary
from gemini_client import DEFAULT_MODELS, load_local_env
from graph_instance import build_instance
from protocol import run_protocol

DEFAULT_MODEL = DEFAULT_MODELS[0]
DEFAULT_SEED = 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the treewidth MWIS local spike.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini model id to run.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Instance seed to run.")
    parser.add_argument("--n-nodes", type=int, default=120, help="Requested graph size. Defaults to 120.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSONL path. Defaults to results/treewidth_mwis_gemini3pro_seed1_planstate_<date>.jsonl",
    )
    parser.add_argument(
        "--min-baseline-gap-pct",
        type=float,
        default=10.0,
        help="Regenerate deterministically until the baseline weight gap meets this percentage.",
    )
    parser.add_argument(
        "--cp-time-limit-s",
        type=float,
        default=120.0,
        help="CP-SAT time limit in seconds for the MWIS gold solve.",
    )
    return parser.parse_args()


def default_output_path(seed: int) -> Path:
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    return results_dir / f"treewidth_mwis_gemini3pro_seed{seed}_planstate_{stamp}.jsonl"


def main() -> None:
    args = parse_args()
    load_local_env()

    output_path = args.output or default_output_path(args.seed)
    rows: list[dict] = []

    with output_path.open("w", encoding="utf-8") as handle:
        try:
            instance = build_instance(
                seed=args.seed,
                n_nodes=args.n_nodes,
                min_baseline_gap_pct=args.min_baseline_gap_pct,
                cp_time_limit_s=args.cp_time_limit_s,
            )
            print(
                "running "
                f"seed={args.seed} model={args.model} requested_n={args.n_nodes} actual_n={instance.n_nodes}"
            )
            row = run_protocol(instance, args.model)
        except Exception as exc:
            row = {
                "model": args.model,
                "seed": args.seed,
                "n_nodes": args.n_nodes,
                "error": str(exc),
            }
        rows.append(row)
        handle.write(json.dumps(row, sort_keys=True) + "\n")
        handle.flush()

    print(f"\nresults written to {output_path}")
    print_summary(rows)


if __name__ == "__main__":
    main()
