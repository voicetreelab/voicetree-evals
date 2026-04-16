from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _fmt_number(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "NA"
    return f"{value:.{digits}f}"


def summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row.get("model", "error")].append(row)

    summaries: list[dict[str, Any]] = []
    for model, group in sorted(grouped.items()):
        ok_rows = [row for row in group if not row.get("error")]
        gap_values = [row["gap_pct"] for row in ok_rows if row.get("gap_pct") is not None]
        makespan_values = [row["final_makespan"] for row in ok_rows if row.get("final_makespan") is not None]
        wall_values = [row["total_wall_seconds"] for row in ok_rows if row.get("total_wall_seconds") is not None]
        score_values = [row["score"] for row in ok_rows if row.get("score") is not None]
        brier_values = [row["brier"] for row in ok_rows if row.get("brier") is not None]
        stop_turn_values = [row["stop_turn"] for row in ok_rows if row.get("stop_turn") is not None]
        summaries.append(
            {
                "model": model,
                "n": len(group),
                "mean_gap_pct": mean(gap_values),
                "mean_makespan": mean(makespan_values),
                "mean_wall_s": mean(wall_values),
                "mean_score": mean(score_values),
                "mean_brier": mean(brier_values),
                "mean_stop_turn": mean(stop_turn_values),
                "turn1_died": sum(1 for row in ok_rows if row.get("turn1_died")),
                "parse_fail": sum(1 for row in ok_rows if row.get("parse_fail")),
                "subtask_killed": sum(int(row.get("subtask_killed_count", 0)) for row in ok_rows),
                "revised_downward": sum(1 for row in ok_rows if row.get("revised_best_guess_downward")),
                "solver_attempts": sum(1 for row in ok_rows if row.get("solver_attempt_detected")),
                "errors": sum(1 for row in group if row.get("error")),
            }
        )
    return summaries


def print_summary(rows: list[dict[str, Any]]) -> None:
    summaries = summarize(rows)
    if not summaries:
        print("no rows")
        return

    headers = [
        "model",
        "n",
        "mean_gap",
        "mean_makespan",
        "mean_wall_s",
        "mean_score",
        "mean_brier",
        "mean_stop_turn",
        "turn1_died",
        "parse_fail",
        "killed",
        "downward",
        "solver_attempts",
        "errors",
    ]
    lines = ["  ".join(headers)]
    for item in summaries:
        lines.append(
            "  ".join(
                [
                    f"{item['model']:<24}",
                    f"{item['n']:<3}",
                    f"{_fmt_number(item['mean_gap_pct']):>8}",
                    f"{_fmt_number(item['mean_makespan']):>13}",
                    f"{_fmt_number(item['mean_wall_s']):>11}",
                    f"{_fmt_number(item['mean_score']):>10}",
                    f"{_fmt_number(item['mean_brier']):>10}",
                    f"{_fmt_number(item['mean_stop_turn']):>14}",
                    f"{item['turn1_died']:<10}",
                    f"{item['parse_fail']:<10}",
                    f"{item['subtask_killed']:<6}",
                    f"{item['revised_downward']:<8}",
                    f"{item['solver_attempts']:<15}",
                    f"{item['errors']:<6}",
                ]
            )
        )
    print("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a local Gemini jobshop spike JSONL.")
    parser.add_argument("path", type=Path, help="JSONL output from jobshop_spike.run_spike")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(args.path)
    print_summary(rows)


if __name__ == "__main__":
    main()
