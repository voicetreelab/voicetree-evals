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
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("error"):
            grouped[(row.get("model", "error"), row.get("arm", "error"))].append(row)
            continue
        grouped[(row["model"], row["arm"])].append(row)

    summaries: list[dict[str, Any]] = []
    for (model, arm), group in sorted(grouped.items()):
        gap_values = [row["gap_pct"] for row in group if row.get("gap_pct") is not None]
        wall_values = [row["total_wall_seconds"] for row in group if row.get("total_wall_seconds") is not None]
        score_values = [row["score"] for row in group if row.get("score") is not None]
        brier_values = [row["brier"] for row in group if row.get("brier") is not None]
        summaries.append(
            {
                "model": model,
                "arm": arm,
                "n": len(group),
                "mean_gap_pct": mean(gap_values),
                "mean_wall_s": mean(wall_values),
                "mean_score": mean(score_values),
                "mean_brier": mean(brier_values),
                "turn1_died": sum(1 for row in group if row.get("turn1_died")),
                "subtask_killed": sum(int(row.get("subtask_killed_count", 0)) for row in group),
                "revised_downward": sum(1 for row in group if row.get("revised_best_guess_downward")),
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
        "arm",
        "n",
        "mean_gap",
        "mean_wall_s",
        "mean_score",
        "mean_brier",
        "turn1_died",
        "killed",
        "downward",
        "errors",
    ]
    lines = ["  ".join(headers)]
    for item in summaries:
        lines.append(
            "  ".join(
                [
                    f"{item['model']:<20}",
                    f"{item['arm']:<10}",
                    f"{item['n']:<3}",
                    f"{_fmt_number(item['mean_gap_pct']):>8}",
                    f"{_fmt_number(item['mean_wall_s']):>11}",
                    f"{_fmt_number(item['mean_score']):>10}",
                    f"{_fmt_number(item['mean_brier']):>10}",
                    f"{item['turn1_died']:<10}",
                    f"{item['subtask_killed']:<6}",
                    f"{item['revised_downward']:<8}",
                    f"{item['errors']:<6}",
                ]
            )
        )
    print("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a local Gemini TSP spike JSONL.")
    parser.add_argument("path", type=Path, help="JSONL output from run_spike.py")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = load_rows(args.path)
    print_summary(rows)


if __name__ == "__main__":
    main()
