#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
BUILD_QUESTIONS_PATH = ROOT / "scripts" / "build_questions.py"
QUESTIONS_PATH = ROOT / "questions.jsonl"
OUTPUT_DIR = ROOT / "scratch" / "round2" / "worker1"
OUTPUT_PATH = OUTPUT_DIR / "questions.partial.jsonl"
RUNNER_IDS_PATH = OUTPUT_DIR / "runner_ids.txt"
NOTES_PATH = OUTPUT_DIR / "gen-notes.md"

ASSIGNED_CELLS: tuple[tuple[str, str, tuple[int, int, int]], ...] = (
    ("cjs", "hard", (7, 8, 9)),
    ("cjs", "hard", (10, 11, 12)),
    ("steiner", "hard", (7, 8, 9)),
    ("steiner", "hard", (10, 11, 12)),
)
MAX_EXTRA_SEED_ATTEMPTS = 4
SIZE_FALLBACK_DELTAS = (20, 40)


@dataclass(frozen=True)
class SlotResult:
    smoke_row: Any
    requested_seed: int
    actual_seed: int
    attempt_lines: tuple[str, ...]


def load_build_questions_module() -> Any:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("round2_worker1_build_questions", BUILD_QUESTIONS_PATH)
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


def seed_candidates(requested_seed: int) -> range:
    return range(requested_seed, requested_seed + MAX_EXTRA_SEED_ATTEMPTS + 1)


def config_overrides_for(cls: str, *, bq: Any) -> tuple[dict[str, Any], ...]:
    overrides: list[dict[str, Any]] = []
    seen_keys: set[tuple[tuple[str, Any], ...]] = set()

    def add_override(override: dict[str, Any]) -> None:
        key = tuple(sorted(override.items()))
        if key in seen_keys:
            return
        seen_keys.add(key)
        overrides.append(override)

    if cls == "steiner":
        base_n = int(bq.steiner.DIFFICULTY_CONFIGS["hard"]["n"])
        for delta in SIZE_FALLBACK_DELTAS:
            n_value = base_n - delta
            if n_value > 0:
                add_override({"n": n_value})

    for key, value in bq.HARD_SIZE_FALLBACKS.get(cls, ()):
        add_override({str(key): value})

    return tuple(overrides)


def build_slot(
    *,
    bq: Any,
    cls: str,
    difficulty: str,
    requested_seed: int,
    used_actual_seeds: set[int],
) -> SlotResult:
    builder = {
        "cjs": bq._build_cjs_row,
        "steiner": bq._build_steiner_row,
    }[cls]
    attempt_lines: list[str] = []
    seed_failures: list[tuple[int, str]] = []

    for candidate_seed in seed_candidates(requested_seed):
        if candidate_seed in used_actual_seeds:
            reason = "skipped because that actual seed was already used earlier"
            seed_failures.append((candidate_seed, reason))
            attempt_lines.append(
                f"- requested seed {requested_seed}: skipped actual seed {candidate_seed} because it was already used earlier"
            )
            continue
        try:
            smoke_row = bq._build_timed_row(builder, candidate_seed, difficulty)
        except Exception as exc:
            reason = bq._error_summary(exc)
            seed_failures.append((candidate_seed, reason))
            attempt_lines.append(
                f"- requested seed {requested_seed}: seed fallback attempt {candidate_seed} failed: {reason}"
            )
            continue
        note = bq._build_fallback_note(
            cls=cls,
            difficulty=difficulty,
            requested_seed=requested_seed,
            actual_seed=candidate_seed,
            seed_failures=seed_failures,
        )
        return SlotResult(
            smoke_row=bq._annotate_row(smoke_row, requested_seed=requested_seed, note=note),
            requested_seed=requested_seed,
            actual_seed=candidate_seed,
            attempt_lines=tuple(attempt_lines),
        )

    for override in config_overrides_for(cls, bq=bq):
        override_label = ", ".join(f"{key}={value}" for key, value in override.items())
        for candidate_seed in seed_candidates(requested_seed):
            if candidate_seed in used_actual_seeds:
                reason = f"{override_label} skipped because that actual seed was already used earlier"
                seed_failures.append((candidate_seed, reason))
                attempt_lines.append(
                    f"- requested seed {requested_seed}: skipped actual seed {candidate_seed} for size fallback {override_label} because it was already used earlier"
                )
                continue
            try:
                smoke_row = bq._build_timed_row(builder, candidate_seed, difficulty, config_override=override)
            except Exception as exc:
                reason = f"{override_label} -> {bq._error_summary(exc)}"
                seed_failures.append((candidate_seed, reason))
                attempt_lines.append(
                    f"- requested seed {requested_seed}: size fallback {override_label} at actual seed {candidate_seed} failed: {bq._error_summary(exc)}"
                )
                continue
            size_override = next(iter(override.items()))
            note = bq._build_fallback_note(
                cls=cls,
                difficulty=difficulty,
                requested_seed=requested_seed,
                actual_seed=candidate_seed,
                seed_failures=seed_failures,
                size_override=size_override,
            )
            return SlotResult(
                smoke_row=bq._annotate_row(smoke_row, requested_seed=requested_seed, note=note),
                requested_seed=requested_seed,
                actual_seed=candidate_seed,
                attempt_lines=tuple(attempt_lines),
            )

    raise RuntimeError(
        f"{cls}_{difficulty}_seed{requested_seed} exhausted seed fallback and size fallback attempts"
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def build_notes(
    *,
    generated_cells: list[dict[str, Any]],
    skipped_cells: list[dict[str, Any]],
    total_rows: int,
    runner_ids: list[str],
) -> str:
    lines = [
        "# Round 2 Worker 1 Generation Notes",
        "",
        f"- Generated rows: {total_rows}",
        f"- Generated cells: {len(generated_cells)}",
        f"- Skipped cells: {len(skipped_cells)}",
        f"- Runner ids: {', '.join(runner_ids) if runner_ids else '(none)'}",
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
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    bq = load_build_questions_module()
    existing_rows = load_existing_rows()
    used_actual_seeds_by_key: dict[tuple[str, str], set[int]] = {}
    for row in existing_rows:
        key = (str(row["class"]), str(row["difficulty"]))
        used_actual_seeds_by_key.setdefault(key, set()).add(int(row["seed"]))

    generated_rows: list[Any] = []
    generated_cells: list[dict[str, Any]] = []
    skipped_cells: list[dict[str, Any]] = []
    runner_ids: list[str] = []

    for cls, difficulty, requested_seeds in ASSIGNED_CELLS:
        used_actual_seeds = used_actual_seeds_by_key.setdefault((cls, difficulty), set())
        cell_slot_results: list[SlotResult] = []
        cell_attempt_lines: list[str] = []
        skip_reason: str | None = None

        for requested_seed in requested_seeds:
            try:
                slot_result = build_slot(
                    bq=bq,
                    cls=cls,
                    difficulty=difficulty,
                    requested_seed=requested_seed,
                    used_actual_seeds=used_actual_seeds,
                )
            except Exception as exc:
                skip_reason = bq._error_summary(exc)
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
                    "attempt_lines": tuple(cell_attempt_lines) or ("- no successful seed attempts before skip",),
                }
            )
            continue

        cell_rows = [slot_result.smoke_row for slot_result in cell_slot_results]
        generated_rows.extend(cell_rows)
        row_ids = [entry.row["id"] for entry in cell_rows]
        runner_ids.append(row_ids[0])
        generated_cells.append(
            {
                "class": cls,
                "difficulty": difficulty,
                "requested_seeds": list(requested_seeds),
                "row_ids": row_ids,
                "attempt_lines": tuple(cell_attempt_lines),
            }
        )

    bq._sanity_check_round_trip(generated_rows)
    write_jsonl(OUTPUT_PATH, [entry.row for entry in generated_rows])
    RUNNER_IDS_PATH.write_text("\n".join(runner_ids) + ("\n" if runner_ids else ""), encoding="utf-8")
    NOTES_PATH.write_text(
        build_notes(
            generated_cells=generated_cells,
            skipped_cells=skipped_cells,
            total_rows=len(generated_rows),
            runner_ids=runner_ids,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "generated_count": len(generated_rows),
                "skipped_cells": len(skipped_cells),
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
