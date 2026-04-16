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
GLOBAL_QUESTIONS_PATH = KAGGLE_ROOT / "questions.jsonl"
QUESTIONS_PATH = WORKER_ROOT / "questions.partial.jsonl"
CHILD_IDS_PATH = WORKER_ROOT / "child-question-ids.txt"
NOTES_PATH = WORKER_ROOT / "gen-notes.md"
MANIFEST_PATH = WORKER_ROOT / "generation-manifest.json"
MAX_EXTRA_SEED_ATTEMPTS = 4

CELL_SPECS: tuple[tuple[str, str, tuple[int, int, int]], ...] = (
    ("tsp", "hard", (7, 8, 9)),
    ("tsp", "hard", (10, 11, 12)),
    ("ve", "hard", (4, 5, 6)),
    ("ve", "hard", (7, 8, 9)),
)


@dataclass(frozen=True)
class SlotResult:
    smoke_row: Any
    requested_seed: int
    actual_seed: int
    attempt_lines: tuple[str, ...]


def load_build_questions() -> Any:
    spec = importlib.util.spec_from_file_location("round2_worker3_build_questions", BUILD_QUESTIONS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load build_questions module from {BUILD_QUESTIONS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_existing_rows() -> list[dict[str, Any]]:
    if not GLOBAL_QUESTIONS_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    with GLOBAL_QUESTIONS_PATH.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def seed_candidates(requested_seed: int) -> range:
    return range(requested_seed, requested_seed + MAX_EXTRA_SEED_ATTEMPTS + 1)


def error_summary(exc: Exception) -> str:
    message = " ".join(str(exc).split())
    return message or type(exc).__name__


def config_overrides_for(module: Any, cls: str) -> tuple[dict[str, Any], ...]:
    overrides: list[dict[str, Any]] = []
    for key, value in getattr(module, "HARD_SIZE_FALLBACKS", {}).get(cls, ()):
        overrides.append({str(key): value})
    return tuple(overrides)


def format_override(override: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in override.items())


def build_slot(
    *,
    module: Any,
    cls: str,
    difficulty: str,
    requested_seed: int,
    used_actual_seeds: set[int],
) -> SlotResult:
    builder = {
        "tsp": module._build_tsp_row,
        "ve": module._build_ve_row,
    }[cls]
    attempt_lines: list[str] = []
    seed_failures: list[tuple[int, str]] = []

    for candidate_seed in seed_candidates(requested_seed):
        if candidate_seed in used_actual_seeds:
            reason = "skipped because that actual seed was already used earlier"
            seed_failures.append((candidate_seed, reason))
            attempt_lines.append(f"- requested seed {requested_seed}: skipped actual seed {candidate_seed}: {reason}")
            continue
        try:
            built = module._build_timed_row(builder, candidate_seed, difficulty)
        except Exception as exc:
            reason = error_summary(exc)
            seed_failures.append((candidate_seed, reason))
            attempt_lines.append(
                f"- requested seed {requested_seed}: seed fallback attempt {candidate_seed} failed: {reason}"
            )
            continue

        used_actual_seeds.add(candidate_seed)
        note = module._build_fallback_note(
            cls=cls,
            difficulty=difficulty,
            requested_seed=requested_seed,
            actual_seed=candidate_seed,
            seed_failures=seed_failures,
        )
        annotated = module._annotate_row(built, requested_seed=requested_seed, note=note)
        return SlotResult(
            smoke_row=annotated,
            requested_seed=requested_seed,
            actual_seed=candidate_seed,
            attempt_lines=tuple(attempt_lines),
        )

    for override in config_overrides_for(module, cls):
        override_label = format_override(override)
        for candidate_seed in seed_candidates(requested_seed):
            if candidate_seed in used_actual_seeds:
                reason = "skipped because that actual seed was already used earlier"
                attempt_lines.append(
                    f"- requested seed {requested_seed}: skipped actual seed {candidate_seed} for size fallback "
                    f"{override_label}: {reason}"
                )
                continue
            try:
                built = module._build_timed_row(builder, candidate_seed, difficulty, config_override=override)
            except Exception as exc:
                attempt_lines.append(
                    f"- requested seed {requested_seed}: size fallback {override_label} at actual seed "
                    f"{candidate_seed} failed: {error_summary(exc)}"
                )
                continue

            used_actual_seeds.add(candidate_seed)
            note = module._build_fallback_note(
                cls=cls,
                difficulty=difficulty,
                requested_seed=requested_seed,
                actual_seed=candidate_seed,
                seed_failures=seed_failures,
                size_override=next(iter(override.items())),
            )
            annotated = module._annotate_row(built, requested_seed=requested_seed, note=note)
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
    generated_cells: list[dict[str, Any]],
    skipped_cells: list[dict[str, Any]],
    total_rows: int,
    child_ids: list[str],
) -> str:
    lines = [
        "# Round 2 Worker 3 Generation Notes",
        "",
        f"- Generated rows: {total_rows}",
        f"- Generated cells: {len(generated_cells)}",
        f"- Skipped cells: {len(skipped_cells)}",
        f"- Child ids: {', '.join(child_ids) if child_ids else '(none)'}",
        "",
        "## Generated Cells",
    ]
    if generated_cells:
        for cell in generated_cells:
            lines.append(
                f"- `{cell['class']}_{cell['difficulty']}` requested {cell['requested_seeds']} -> ids {cell['row_ids']}"
            )
            if cell["attempt_lines"]:
                lines.extend(cell["attempt_lines"])
            else:
                lines.append("- all requested seeds generated directly without fallback")
    else:
        lines.append("- none")

    lines.extend(["", "## Skipped Cells"])
    if skipped_cells:
        for cell in skipped_cells:
            lines.append(
                f"- `{cell['class']}_{cell['difficulty']}` requested {cell['requested_seeds']} skipped: {cell['reason']}"
            )
            lines.extend(cell["attempt_lines"])
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def main() -> int:
    module = load_build_questions()
    WORKER_ROOT.mkdir(parents=True, exist_ok=True)

    used_actual_seeds_by_key: dict[tuple[str, str], set[int]] = {}
    for row in load_existing_rows():
        key = (str(row["class"]), str(row["difficulty"]))
        used_actual_seeds_by_key.setdefault(key, set()).add(int(row["seed"]))

    generated_rows: list[Any] = []
    generated_cells: list[dict[str, Any]] = []
    skipped_cells: list[dict[str, Any]] = []
    child_ids: list[str] = []

    for cls, difficulty, requested_seeds in CELL_SPECS:
        used_actual_seeds = used_actual_seeds_by_key.setdefault((cls, difficulty), set())
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

        cell_rows = [slot_result.smoke_row.row for slot_result in cell_slot_results]
        generated_rows.extend(slot_result.smoke_row for slot_result in cell_slot_results)
        child_ids.append(cell_rows[0]["id"])
        generated_cells.append(
            {
                "class": cls,
                "difficulty": difficulty,
                "requested_seeds": list(requested_seeds),
                "row_ids": [row["id"] for row in cell_rows],
                "attempt_lines": cell_attempt_lines,
            }
        )

    module._sanity_check_round_trip(generated_rows)
    write_jsonl(QUESTIONS_PATH, [entry.row for entry in generated_rows])
    CHILD_IDS_PATH.write_text("\n".join(child_ids) + ("\n" if child_ids else ""), encoding="utf-8")
    NOTES_PATH.write_text(
        build_notes(
            generated_cells=generated_cells,
            skipped_cells=skipped_cells,
            total_rows=len(generated_rows),
            child_ids=child_ids,
        ),
        encoding="utf-8",
    )
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "worker": 3,
                "round": 2,
                "generated_rows": len(generated_rows),
                "generated_cells": generated_cells,
                "skipped_cells": skipped_cells,
                "child_ids": child_ids,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(generated_rows)} rows to {QUESTIONS_PATH}")
    if child_ids:
        print(f"Child ids: {', '.join(child_ids)}")
    if skipped_cells:
        print(f"Skipped {len(skipped_cells)} cells; see {NOTES_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
