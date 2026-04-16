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
        summaries.append(
            {
                "model": model,
                "n": len(group),
                "mean_gap_pct": mean([row["gap_pct"] for row in ok_rows if row.get("gap_pct") is not None]),
                "mean_wall_s": mean([row["total_wall_seconds"] for row in ok_rows if row.get("total_wall_seconds") is not None]),
                "mean_score": mean([row["score"] for row in ok_rows if row.get("score") is not None]),
                "mean_brier": mean([row["brier"] for row in ok_rows if row.get("brier") is not None]),
                "mean_continue_brier": mean(
                    [row["plan_continue_brier"] for row in ok_rows if row.get("plan_continue_brier") is not None]
                ),
                "mean_delta_error": mean(
                    [
                        row["plan_expected_delta_score_error"]
                        for row in ok_rows
                        if row.get("plan_expected_delta_score_error") is not None
                    ]
                ),
                "mean_turn_count": mean([float(row["turn_count"]) for row in ok_rows if row.get("turn_count") is not None]),
                "turn1_died": sum(1 for row in ok_rows if row.get("turn1_died")),
                "timeout_kills": sum(int(row.get("subtask_killed_count", 0)) for row in ok_rows),
                "feasibility_failures": sum(int(row.get("feasibility_failure_count", 0)) for row in ok_rows),
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
        "mean_wall_s",
        "mean_score",
        "mean_brier",
        "mean_continue_brier",
        "mean_delta_err",
        "mean_turns",
        "turn1_died",
        "killed",
        "infeasible",
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
                    f"{_fmt_number(item['mean_wall_s']):>11}",
                    f"{_fmt_number(item['mean_score']):>10}",
                    f"{_fmt_number(item['mean_brier']):>10}",
                    f"{_fmt_number(item['mean_continue_brier']):>19}",
                    f"{_fmt_number(item['mean_delta_error']):>14}",
                    f"{_fmt_number(item['mean_turn_count']):>10}",
                    f"{item['turn1_died']:<10}",
                    f"{item['timeout_kills']:<6}",
                    f"{item['feasibility_failures']:<10}",
                    f"{item['errors']:<6}",
                ]
            )
        )
    print("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a Codex MetaGame v2 local spike JSONL.")
    parser.add_argument("path", type=Path, help="JSONL output from codex_metagame_v2.run_spike")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print_summary(load_rows(args.path))


if __name__ == "__main__":
    main()
