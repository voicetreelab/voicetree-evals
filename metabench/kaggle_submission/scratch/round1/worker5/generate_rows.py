#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = ROOT.parent
BUILD_QUESTIONS_PATH = ROOT / "scripts" / "build_questions.py"
QUESTIONS_PATH = ROOT / "questions.jsonl"
OUTPUT_DIR = ROOT / "scratch" / "round1" / "worker5"
OUTPUT_PATH = OUTPUT_DIR / "questions.partial.jsonl"
RUNNER_IDS_PATH = OUTPUT_DIR / "runner_ids.txt"
NOTES_PATH = OUTPUT_DIR / "gen-notes.md"

ASSIGNED_CELLS: tuple[tuple[str, str, tuple[int, int, int]], ...] = (
    ("ve", "medium", (5, 6, 7)),
    ("ve", "medium", (8, 9, 10)),
    ("cjs", "hard", (4, 5, 6)),
    ("steiner", "hard", (4, 5, 6)),
)
MAX_SEED_FALLBACK = 4


def load_build_questions_module() -> Any:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("worker5_build_questions", BUILD_QUESTIONS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec from {BUILD_QUESTIONS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_existing_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def build_medium_row_with_fallback(
    *,
    bq: Any,
    cls: str,
    requested_seed: int,
    builder: Any,
    used_actual_seeds: set[int],
) -> Any:
    seed_failures: list[tuple[int, str]] = []
    for candidate_seed in range(requested_seed, requested_seed + MAX_SEED_FALLBACK + 1):
        if candidate_seed in used_actual_seeds:
            seed_failures.append((candidate_seed, "skipped because that actual seed was already used earlier"))
            continue
        try:
            built = bq._build_timed_row(builder, candidate_seed, "medium")
        except Exception as exc:  # pragma: no cover - exercised by generator failures
            seed_failures.append((candidate_seed, bq._error_summary(exc)))
            continue
        used_actual_seeds.add(candidate_seed)
        note = bq._build_fallback_note(
            cls=cls,
            difficulty="medium",
            requested_seed=requested_seed,
            actual_seed=candidate_seed,
            seed_failures=seed_failures,
        )
        return bq._annotate_row(built, requested_seed=requested_seed, note=note)
    failure_summary = bq._seed_failure_summary(seed_failures) or "no attempts recorded"
    raise RuntimeError(
        f"failed to generate {cls}_medium_seed{requested_seed} after seed fallback: {failure_summary}"
    )


def render_notes(
    *,
    generated_rows: list[Any],
    skipped: list[dict[str, Any]],
    runner_ids: list[str],
) -> str:
    lines = [
        "# Worker 5 Generation Notes",
        "",
        f"- Generated rows: {len(generated_rows)}",
        f"- Skipped slots: {len(skipped)}",
        f"- Runner ids: {', '.join(runner_ids) if runner_ids else '(none)'}",
        "",
        "## Generated",
        "",
        "| requested_slot | actual_id | class | difficulty | actual_seed | wall_s_to_compute_gold | notes |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for smoke_row in generated_rows:
        requested_seed = smoke_row.requested_seed
        actual_id = str(smoke_row.row["id"])
        wall_s = smoke_row.wall_s_to_compute_gold
        notes = (smoke_row.notes or "").replace("\n", " ").replace("|", "\\|")
        lines.append(
            "| "
            f"{smoke_row.row['class']}_{smoke_row.row['difficulty']}_seed{requested_seed} | "
            f"{actual_id} | {smoke_row.row['class']} | {smoke_row.row['difficulty']} | "
            f"{smoke_row.row['seed']} | {wall_s:.3f} | {notes or '-'} |"
        )

    lines.extend(["", "## Skipped", ""])
    if not skipped:
        lines.append("- None")
    else:
        for item in skipped:
            lines.append(
                f"- `{item['requested_slot']}`: {item['reason']}"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    bq = load_build_questions_module()
    builders = {
        "cjs": bq._build_cjs_row,
        "steiner": bq._build_steiner_row,
        "graphcol": bq._build_graphcol_row,
        "tsp": bq._build_tsp_row,
        "mwis": bq._build_mwis_row,
        "ve": bq._build_ve_row,
    }
    existing_rows = load_existing_rows()
    used_actual_seeds: dict[tuple[str, str], set[int]] = {}
    for row in existing_rows:
        key = (str(row["class"]), str(row["difficulty"]))
        used_actual_seeds.setdefault(key, set()).add(int(row["seed"]))

    generated_rows: list[Any] = []
    skipped: list[dict[str, Any]] = []
    runner_ids: list[str] = []

    for cls, difficulty, requested_seeds in ASSIGNED_CELLS:
        cell_first_id: str | None = None
        for requested_seed in requested_seeds:
            key = (cls, difficulty)
            used_actual_seeds.setdefault(key, set())
            builder = builders[cls]
            try:
                if difficulty == "hard":
                    smoke_row = bq._build_hard_row_with_fallback(
                        cls=cls,
                        requested_seed=requested_seed,
                        builder=builder,
                        used_actual_seeds=used_actual_seeds[key],
                    )
                elif difficulty == "medium":
                    smoke_row = build_medium_row_with_fallback(
                        bq=bq,
                        cls=cls,
                        requested_seed=requested_seed,
                        builder=builder,
                        used_actual_seeds=used_actual_seeds[key],
                    )
                else:  # pragma: no cover - unreachable for this worker
                    raise ValueError(f"unsupported difficulty {difficulty!r}")
            except Exception as exc:
                skipped.append(
                    {
                        "requested_slot": f"{cls}_{difficulty}_seed{requested_seed}",
                        "reason": str(exc).replace("\n", " "),
                    }
                )
                continue

            generated_rows.append(smoke_row)
            if requested_seed == requested_seeds[0]:
                cell_first_id = str(smoke_row.row["id"])

        if cell_first_id is not None:
            runner_ids.append(cell_first_id)

    bq._sanity_check_round_trip(generated_rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bq._write_jsonl(OUTPUT_PATH, [entry.row for entry in generated_rows])
    RUNNER_IDS_PATH.write_text("\n".join(runner_ids) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(
        render_notes(generated_rows=generated_rows, skipped=skipped, runner_ids=runner_ids),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "generated_count": len(generated_rows),
                "skipped_count": len(skipped),
                "runner_ids": runner_ids,
                "output_path": str(OUTPUT_PATH),
                "notes_path": str(NOTES_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
