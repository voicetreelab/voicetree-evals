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

MAX_EXTRA_SEED_ATTEMPTS = 4
MWIS_HARD_N = 140
MWIS_NODE_FALLBACK_DELTAS = (20, 40)

CELL_SPECS: tuple[tuple[str, str, tuple[int, int, int]], ...] = (
    ("ve", "hard", (10, 11, 12)),
    ("mwis", "hard", (5, 6, 7)),
    ("mwis", "hard", (8, 9, 10)),
    ("mwis", "hard", (11, 12, 13)),
)


@dataclass(frozen=True)
class SlotResult:
    smoke_row: Any
    requested_seed: int
    actual_seed: int
    attempt_lines: tuple[str, ...]
    failure_reason: str | None = None


def load_build_questions() -> Any:
    if str(KAGGLE_ROOT) not in sys.path:
        sys.path.insert(0, str(KAGGLE_ROOT))
    spec = importlib.util.spec_from_file_location("worker4_build_questions", BUILD_QUESTIONS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"failed to load build_questions module from {BUILD_QUESTIONS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_existing_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not GLOBAL_QUESTIONS_PATH.exists():
        return rows
    for raw_line in GLOBAL_QUESTIONS_PATH.read_text(encoding="utf-8").splitlines():
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


def config_overrides_for(cls: str) -> tuple[dict[str, Any], ...]:
    if cls != "mwis":
        return ()
    overrides: list[dict[str, Any]] = []
    for delta in MWIS_NODE_FALLBACK_DELTAS:
        n_nodes = MWIS_HARD_N - delta
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
        "mwis": module._build_mwis_row,
        "ve": module._build_ve_row,
    }[cls]
    attempt_lines: list[str] = []

    for candidate_seed in seed_candidates(requested_seed):
        if candidate_seed in used_actual_seeds:
            attempt_lines.append(
                f"  - seed={candidate_seed}: skipped duplicate actual_seed"
            )
            continue
        try:
            smoke_row = module._build_timed_row(builder, candidate_seed, difficulty)
        except Exception as exc:
            attempt_lines.append(
                f"  - seed={candidate_seed}: {type(exc).__name__}: {error_summary(exc)}"
            )
            continue
        return SlotResult(
            smoke_row=smoke_row,
            requested_seed=requested_seed,
            actual_seed=candidate_seed,
            attempt_lines=tuple(attempt_lines),
        )

    for override in config_overrides_for(cls):
        override_label = ", ".join(f"{key}={value}" for key, value in override.items())
        for candidate_seed in seed_candidates(requested_seed):
            if candidate_seed in used_actual_seeds:
                attempt_lines.append(
                    f"  - seed={candidate_seed}: skipped duplicate actual_seed for size fallback {override_label}"
                )
                continue
            try:
                smoke_row = module._build_timed_row(
                    builder,
                    candidate_seed,
                    difficulty,
                    config_override=override,
                )
            except Exception as exc:
                attempt_lines.append(
                    f"  - seed={candidate_seed}: {override_label} -> {type(exc).__name__}: {error_summary(exc)}"
                )
                continue
            return SlotResult(
                smoke_row=smoke_row,
                requested_seed=requested_seed,
                actual_seed=candidate_seed,
                attempt_lines=tuple(attempt_lines),
            )

    return SlotResult(
        smoke_row=None,
        requested_seed=requested_seed,
        actual_seed=-1,
        attempt_lines=tuple(attempt_lines),
        failure_reason=(
            f"{cls}_{difficulty}_seed{requested_seed} exhausted seed fallback (+4)"
            + (" and MWIS n fallback (-20, -40)" if cls == "mwis" else "")
        ),
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def format_slot_block(slot: SlotResult) -> list[str]:
    requested_slot = (
        f"{slot.smoke_row.row['class']}_{slot.smoke_row.row['difficulty']}_seed{slot.requested_seed}"
        if slot.smoke_row is not None
        else f"(requested seed {slot.requested_seed})"
    )
    lines: list[str] = []
    if slot.smoke_row is None:
        lines.append(f"- skipped requested seed `{slot.requested_seed}`: {slot.failure_reason}")
        lines.extend(slot.attempt_lines)
        return lines

    row = slot.smoke_row.row
    row_instance = row.get("instance", {})
    extra_notes: list[str] = []
    if slot.smoke_row.notes:
        extra_notes.append(str(slot.smoke_row.notes))
    if row["class"] == "mwis":
        requested_n_nodes = row_instance.get("requested_n_nodes")
        realized_n_nodes = row_instance.get("n_nodes")
        if requested_n_nodes is not None and int(requested_n_nodes) != MWIS_HARD_N:
            extra_notes.append(
                f"size fallback requested_n_nodes={requested_n_nodes}, realized_n_nodes={realized_n_nodes}"
            )
    builder_note = f"; builder note: {' '.join(extra_notes)}" if extra_notes else ""
    lines.append(
        f"- requested `{requested_slot}` -> actual `{row['id']}`{builder_note}"
    )
    lines.extend(slot.attempt_lines)
    wall_s = slot.smoke_row.wall_s_to_compute_gold
    if wall_s is not None:
        lines.append(f"  - gold wall_s: {wall_s:.2f}")
    return lines


def build_notes(
    *,
    cell_results: list[dict[str, Any]],
    all_rows: list[dict[str, Any]],
    child_ids: list[str],
    skipped_slots: list[str],
) -> str:
    lines = [
        "# Worker 4 Generation Notes",
        "",
        f"- rows_written: {len(all_rows)}",
        f"- output: `kaggle_submission/scratch/round2/worker4/questions.partial.jsonl`",
        f"- probe_ids_by_cell: {child_ids}",
    ]
    if skipped_slots:
        lines.append(f"- skipped_slots: {len(skipped_slots)}")
    lines.append("")

    for cell in cell_results:
        requested_range = f"{cell['requested_seeds'][0]}-{cell['requested_seeds'][-1]}"
        lines.append(f"## {cell['class']} {cell['difficulty']} requested {requested_range}")
        if cell["probe_id"] is None:
            lines.append("- no row generated for this cell")
        for slot in cell["slots"]:
            lines.extend(format_slot_block(slot))
        lines.append("")

    if skipped_slots:
        lines.append("## skipped slots")
        for entry in skipped_slots:
            lines.append(f"- {entry}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    module = load_build_questions()
    existing_rows = load_existing_rows()
    used_actual_seeds_by_key: dict[tuple[str, str], set[int]] = {}
    for row in existing_rows:
        key = (str(row["class"]), str(row["difficulty"]))
        used_actual_seeds_by_key.setdefault(key, set()).add(int(row["seed"]))

    all_smoke_rows: list[Any] = []
    all_rows: list[dict[str, Any]] = []
    child_ids: list[str] = []
    cell_results: list[dict[str, Any]] = []
    skipped_slots: list[str] = []

    for cls, difficulty, requested_seeds in CELL_SPECS:
        key = (cls, difficulty)
        used_actual_seeds = used_actual_seeds_by_key.setdefault(key, set())
        slots: list[SlotResult] = []
        probe_id: str | None = None

        for requested_seed in requested_seeds:
            slot = build_slot(
                module=module,
                cls=cls,
                difficulty=difficulty,
                requested_seed=requested_seed,
                used_actual_seeds=used_actual_seeds,
            )
            slots.append(slot)
            if slot.smoke_row is None:
                skipped_slots.append(
                    f"`{cls}_{difficulty}_seed{requested_seed}`: {slot.failure_reason or 'unknown failure'}"
                )
                continue

            used_actual_seeds.add(slot.actual_seed)
            all_smoke_rows.append(slot.smoke_row)
            all_rows.append(slot.smoke_row.row)
            if probe_id is None:
                probe_id = str(slot.smoke_row.row["id"])

        if probe_id is not None:
            child_ids.append(probe_id)
        cell_results.append(
            {
                "class": cls,
                "difficulty": difficulty,
                "requested_seeds": list(requested_seeds),
                "probe_id": probe_id,
                "slots": slots,
            }
        )

    module._sanity_check_round_trip(all_smoke_rows)
    write_jsonl(QUESTIONS_PATH, all_rows)
    CHILD_IDS_PATH.write_text("\n".join(child_ids) + ("\n" if child_ids else ""), encoding="utf-8")
    NOTES_PATH.write_text(
        build_notes(
            cell_results=cell_results,
            all_rows=all_rows,
            child_ids=child_ids,
            skipped_slots=skipped_slots,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "rows_written": len(all_rows),
                "probe_ids_by_cell": child_ids,
                "skipped_slots": len(skipped_slots),
                "questions_path": str(QUESTIONS_PATH),
                "notes_path": str(NOTES_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
