#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
WORKER_ROOT = SCRIPT_PATH.parent
KAGGLE_ROOT = SCRIPT_PATH.parents[3]
BUILD_QUESTIONS_PATH = KAGGLE_ROOT / "scripts" / "build_questions.py"
QUESTIONS_PATH = WORKER_ROOT / "questions.partial.jsonl"
CHILD_IDS_PATH = WORKER_ROOT / "child-question-ids.txt"
NOTES_PATH = WORKER_ROOT / "gen-notes.md"
MAX_EXTRA_SEED_ATTEMPTS = 4
GRAPHCOL_BASE_NODES = 30
GRAPHCOL_NODE_FALLBACK_DELTAS = (20, 40)

CELL_SPECS: tuple[tuple[str, str, tuple[int, int, int]], ...] = (
    ("graphcol", "hard", (4, 5, 6)),
    ("graphcol", "hard", (7, 8, 9)),
    ("graphcol", "hard", (10, 11, 12)),
    ("tsp", "hard", (4, 5, 6)),
)


@dataclass(frozen=True)
class SlotResult:
    smoke_row: Any
    requested_seed: int
    actual_seed: int
    attempt_lines: tuple[str, ...]


def load_build_questions() -> Any:
    spec = importlib.util.spec_from_file_location("worker2_round2_build_questions", BUILD_QUESTIONS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load build_questions module from {BUILD_QUESTIONS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def seed_candidates(requested_seed: int) -> range:
    return range(requested_seed, requested_seed + MAX_EXTRA_SEED_ATTEMPTS + 1)


def error_summary(exc: Exception) -> str:
    message = " ".join(str(exc).split())
    return message or type(exc).__name__


def config_overrides_for(cls: str) -> tuple[dict[str, Any], ...]:
    if cls != "graphcol":
        return ()
    overrides: list[dict[str, Any]] = []
    for delta in GRAPHCOL_NODE_FALLBACK_DELTAS:
        n_nodes = GRAPHCOL_BASE_NODES - delta
        if n_nodes > 0:
            overrides.append({"n_nodes": n_nodes})
    return tuple(overrides)


def build_slot(
    *,
    module: Any,
    cls: str,
    difficulty: str,
    requested_seed: int,
    used_actual_seeds: set[int],
) -> SlotResult:
    builder = {
        "graphcol": module._build_graphcol_row,
        "tsp": module._build_tsp_row,
    }[cls]
    attempt_lines: list[str] = []

    for candidate_seed in seed_candidates(requested_seed):
        if candidate_seed in used_actual_seeds:
            attempt_lines.append(
                f"- requested seed {requested_seed}: skipped actual seed {candidate_seed} because it was already used earlier"
            )
            continue
        try:
            smoke_row = module._build_timed_row(builder, candidate_seed, difficulty)
        except Exception as exc:
            attempt_lines.append(
                f"- requested seed {requested_seed}: seed fallback attempt {candidate_seed} failed: {error_summary(exc)}"
            )
            continue
        note = module._build_fallback_note(
            cls=cls,
            difficulty=difficulty,
            requested_seed=requested_seed,
            actual_seed=candidate_seed,
            seed_failures=[],
            size_override=None,
        )
        annotated = module._annotate_row(smoke_row, requested_seed=requested_seed, note=note)
        return SlotResult(
            smoke_row=annotated,
            requested_seed=requested_seed,
            actual_seed=candidate_seed,
            attempt_lines=tuple(attempt_lines),
        )

    for override in config_overrides_for(cls):
        override_label = ", ".join(f"{key}={value}" for key, value in override.items())
        for candidate_seed in seed_candidates(requested_seed):
            if candidate_seed in used_actual_seeds:
                attempt_lines.append(
                    f"- requested seed {requested_seed}: skipped actual seed {candidate_seed} for size fallback {override_label} because it was already used earlier"
                )
                continue
            try:
                smoke_row = module._build_timed_row(builder, candidate_seed, difficulty, config_override=override)
            except Exception as exc:
                attempt_lines.append(
                    f"- requested seed {requested_seed}: size fallback {override_label} at actual seed {candidate_seed} failed: {error_summary(exc)}"
                )
                continue
            note = module._build_fallback_note(
                cls=cls,
                difficulty=difficulty,
                requested_seed=requested_seed,
                actual_seed=candidate_seed,
                seed_failures=[],
                size_override=next(iter(override.items())),
            )
            annotated = module._annotate_row(smoke_row, requested_seed=requested_seed, note=note)
            return SlotResult(
                smoke_row=annotated,
                requested_seed=requested_seed,
                actual_seed=candidate_seed,
                attempt_lines=tuple(attempt_lines),
            )

    raise RuntimeError(
        f"{cls}_{difficulty}_seed{requested_seed} exhausted seed fallback and size fallback attempts"
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def build_notes(
    *,
    generated_rows: list[dict[str, Any]],
    skipped_cells: list[dict[str, Any]],
    child_ids: list[str],
) -> str:
    lines = [
        "# Worker 2 Generation Notes",
        "",
        f"- Generated rows: {len(generated_rows)}",
        f"- Skipped cells: {len(skipped_cells)}",
        f"- Runner ids: {', '.join(child_ids) if child_ids else 'none'}",
        "",
        "## Generated",
        "",
        "| requested_slot | actual_id | class | difficulty | actual_seed | wall_s_to_compute_gold | notes |",
        "|---|---|---|---|---:|---:|---|",
    ]
    if generated_rows:
        for row in generated_rows:
            lines.append(
                f"| `{row['requested_slot']}` | `{row['actual_id']}` | `{row['class']}` | `{row['difficulty']}` | {row['actual_seed']} | {row['wall_s_to_compute_gold']:.3f} | {row['notes']} |"
            )
    else:
        lines.append("| - | - | - | - | - | - | no rows generated |")

    lines.extend(["", "## Skipped", ""])
    if skipped_cells:
        for cell in skipped_cells:
            lines.append(
                f"- `{cell['class']}_{cell['difficulty']}` requested {cell['requested_seeds']} skipped: {cell['reason']}"
            )
            lines.extend(cell["attempt_lines"])
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"


def main() -> int:
    module = load_build_questions()
    WORKER_ROOT.mkdir(parents=True, exist_ok=True)

    smoke_rows: list[Any] = []
    generated_rows: list[dict[str, Any]] = []
    child_ids: list[str] = []
    skipped_cells: list[dict[str, Any]] = []
    used_actual_seeds_by_class: dict[str, set[int]] = {}

    for cls, difficulty, requested_seeds in CELL_SPECS:
        used_actual_seeds = used_actual_seeds_by_class.setdefault(cls, set())
        cell_slot_results: list[SlotResult] = []
        cell_attempt_lines: list[str] = []
        skip_reason: str | None = None

        for requested_seed in requested_seeds:
            try:
                slot_result = build_slot(
                    module=module,
                    cls=cls,
                    difficulty=difficulty,
                    requested_seed=requested_seed,
                    used_actual_seeds=used_actual_seeds,
                )
            except Exception as exc:
                skip_reason = error_summary(exc)
                break

            used_actual_seeds.add(slot_result.actual_seed)
            cell_slot_results.append(slot_result)
            cell_attempt_lines.extend(slot_result.attempt_lines)

        if skip_reason is not None:
            skipped_cells.append(
                {
                    "class": cls,
                    "difficulty": difficulty,
                    "requested_seeds": list(requested_seeds),
                    "reason": skip_reason,
                    "attempt_lines": cell_attempt_lines or ("- no successful seed attempts before skip",),
                }
            )
            continue

        child_ids.append(cell_slot_results[0].smoke_row.row["id"])
        for slot_result in cell_slot_results:
            smoke_rows.append(slot_result.smoke_row)
            generated_rows.append(
                {
                    "requested_slot": f"{cls}_{difficulty}_seed{slot_result.requested_seed}",
                    "actual_id": slot_result.smoke_row.row["id"],
                    "class": cls,
                    "difficulty": difficulty,
                    "actual_seed": slot_result.actual_seed,
                    "wall_s_to_compute_gold": slot_result.smoke_row.wall_s_to_compute_gold or 0.0,
                    "notes": slot_result.smoke_row.notes or "-",
                }
            )

    module._sanity_check_round_trip(smoke_rows)
    write_jsonl(QUESTIONS_PATH, [smoke_row.row for smoke_row in smoke_rows])
    CHILD_IDS_PATH.write_text("\n".join(child_ids) + ("\n" if child_ids else ""), encoding="utf-8")
    NOTES_PATH.write_text(
        build_notes(generated_rows=generated_rows, skipped_cells=skipped_cells, child_ids=child_ids),
        encoding="utf-8",
    )

    print(f"Wrote {len(smoke_rows)} rows to {QUESTIONS_PATH}")
    if child_ids:
        print(f"Child ids: {', '.join(child_ids)}")
    if skipped_cells:
        print(f"Skipped {len(skipped_cells)} cells; see {NOTES_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
