#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import random
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
BUILD_QUESTIONS_PATH = ROOT / "scripts" / "build_questions.py"
QUESTIONS_PATH = ROOT / "questions.jsonl"
OUTPUT_DIR = ROOT / "scratch" / "round2" / "worker8"
OUTPUT_PATH = OUTPUT_DIR / "questions.partial.jsonl"
RUNNER_IDS_PATH = OUTPUT_DIR / "child-question-ids.txt"
MANIFEST_PATH = OUTPUT_DIR / "generation-manifest.json"
NOTES_PATH = OUTPUT_DIR / "gen-notes.md"

ASSIGNED_CELLS: tuple[tuple[str, tuple[int, int, int]], ...] = (
    ("medium", (38, 39, 40)),
    ("medium", (41, 42, 43)),
    ("hard", (36, 37, 38)),
    ("hard", (39, 40, 41)),
)
MAX_SEED_FALLBACK = 4


def load_build_questions_module() -> Any:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("round2_worker8_build_questions", BUILD_QUESTIONS_PATH)
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


def build_component_row(
    *,
    module: Any,
    cls: str,
    difficulty: str,
    actual_seed: int,
) -> tuple[Any, list[str]]:
    builder = {
        "cjs": module._build_cjs_row,
        "steiner": module._build_steiner_row,
        "graphcol": module._build_graphcol_row,
        "tsp": module._build_tsp_row,
        "mwis": module._build_mwis_row,
        "ve": module._build_ve_row,
    }[cls]

    try:
        return module._build_timed_row(builder, actual_seed, difficulty), []
    except Exception as exc:
        failures = [f"default: {module._error_summary(exc)}"]

    if difficulty == "hard":
        for key, value in module.HARD_SIZE_FALLBACKS.get(cls, ()):
            override = {key: value}
            try:
                smoke_row = module._build_timed_row(builder, actual_seed, difficulty, config_override=override)
            except Exception as exc:
                failures.append(f"{cls} {key}={value} override: {module._error_summary(exc)}")
                continue
            return smoke_row, [f"{cls}: {cls} {key}={value} override"]

    raise RuntimeError(" | ".join(failures))


def seed_candidates(requested_seed: int) -> range:
    return range(requested_seed, requested_seed + MAX_SEED_FALLBACK + 1)


def build_portfolio_slot(
    *,
    module: Any,
    difficulty: str,
    requested_seed: int,
    used_actual_seeds: set[int],
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []

    for candidate_seed in seed_candidates(requested_seed):
        if candidate_seed in used_actual_seeds:
            attempts.append(
                {
                    "actual_seed": candidate_seed,
                    "status": "used_local_or_global",
                    "reason": "skipped because actual seed already used earlier in this difficulty",
                }
            )
            continue

        classes = tuple(random.Random(candidate_seed).sample(module.SOLO_CLASSES, 3))
        component_rows: list[Any] = []
        component_ids: list[str] = []
        component_overrides: list[str] = []

        try:
            for cls in classes:
                smoke_row, overrides = build_component_row(
                    module=module,
                    cls=cls,
                    difficulty=difficulty,
                    actual_seed=candidate_seed,
                )
                component_rows.append(smoke_row)
                component_ids.append(str(smoke_row.row["id"]))
                component_overrides.extend(overrides)
        except Exception as exc:
            attempts.append(
                {
                    "actual_seed": candidate_seed,
                    "status": "failed",
                    "reason": str(exc).replace("\n", " "),
                }
            )
            continue

        portfolio_row = module._build_portfolio_row(
            solo_rows=component_rows,
            difficulty=difficulty,
            seed=candidate_seed,
            component_ids=tuple(component_ids),
        )
        portfolio_row = module._annotate_row(portfolio_row, requested_seed=requested_seed)
        used_actual_seeds.add(candidate_seed)
        return {
            "smoke_row": portfolio_row,
            "requested_seed": requested_seed,
            "actual_seed": candidate_seed,
            "classes": list(classes),
            "component_ids": component_ids,
            "component_overrides": component_overrides,
            "attempts": attempts,
        }

    return {
        "smoke_row": None,
        "requested_seed": requested_seed,
        "actual_seed": None,
        "classes": [],
        "component_ids": [],
        "component_overrides": [],
        "attempts": attempts,
    }


def render_notes(records: list[dict[str, Any]]) -> str:
    lines = ["# Worker 8 generation notes", ""]
    for record in records:
        difficulty = record["difficulty"]
        requested_seeds = record["requested_seeds"]
        label = (
            f"portfolio {difficulty} seeds {requested_seeds[0]}-{requested_seeds[-1]}"
            if requested_seeds == list(range(requested_seeds[0], requested_seeds[-1] + 1))
            else f"portfolio {difficulty} seeds {'/'.join(str(seed) for seed in requested_seeds)}"
        )
        lines.extend([f"## {label}"])
        rows = record["rows"]
        if not rows:
            lines.append("- no rows generated")
            lines.append("")
            continue
        for row in rows:
            if row["actual_seed"] is None:
                attempt_summary = "; ".join(
                    f"seed={attempt['actual_seed']}: {attempt['reason']}" for attempt in row["attempts"]
                ) or "no attempts recorded"
                lines.append(
                    f"- failed requested `portfolio_{difficulty}_seed{row['requested_seed']}`; attempts: {attempt_summary}"
                )
                continue

            attempt_summary = "; ".join(
                f"seed={attempt['actual_seed']}: {attempt['reason']}" for attempt in row["attempts"]
            )
            prefix = (
                f"- generated `portfolio_{difficulty}_seed{row['actual_seed']}` for requested seed {row['requested_seed']}"
            )
            if attempt_summary:
                prefix += f"; fallback attempts: {attempt_summary}"
            prefix += f"; final classes {row['classes']}; components={row['component_ids']}"
            if row["component_overrides"]:
                prefix += f"; component overrides={row['component_overrides']}"
            lines.append(prefix)
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    module = load_build_questions_module()
    existing_rows = load_existing_rows()
    used_actual_seeds_by_difficulty: dict[str, set[int]] = {"medium": set(), "hard": set()}
    for row in existing_rows:
        if row.get("class") != "portfolio":
            continue
        difficulty = str(row["difficulty"])
        used_actual_seeds_by_difficulty.setdefault(difficulty, set()).add(int(row["seed"]))

    generated_rows: list[Any] = []
    runner_ids: list[str] = []
    manifest_records: list[dict[str, Any]] = []

    for difficulty, requested_seeds in ASSIGNED_CELLS:
        rows_for_cell: list[dict[str, Any]] = []
        cell_first_id: str | None = None
        used_actual_seeds = used_actual_seeds_by_difficulty.setdefault(difficulty, set())

        for requested_seed in requested_seeds:
            slot = build_portfolio_slot(
                module=module,
                difficulty=difficulty,
                requested_seed=requested_seed,
                used_actual_seeds=used_actual_seeds,
            )
            rows_for_cell.append(
                {
                    "requested_seed": slot["requested_seed"],
                    "actual_seed": slot["actual_seed"],
                    "id": None if slot["smoke_row"] is None else slot["smoke_row"].row["id"],
                    "classes": slot["classes"],
                    "component_ids": slot["component_ids"],
                    "component_overrides": slot["component_overrides"],
                    "attempts": slot["attempts"],
                }
            )
            if slot["smoke_row"] is None:
                continue

            generated_rows.append(slot["smoke_row"])
            if cell_first_id is None:
                cell_first_id = str(slot["smoke_row"].row["id"])

        if cell_first_id is not None:
            runner_ids.append(cell_first_id)

        manifest_records.append(
            {
                "difficulty": difficulty,
                "requested_seeds": list(requested_seeds),
                "rows": rows_for_cell,
            }
        )

    module._sanity_check_round_trip(generated_rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    module._write_jsonl(OUTPUT_PATH, [entry.row for entry in generated_rows])
    RUNNER_IDS_PATH.write_text("\n".join(runner_ids) + ("\n" if runner_ids else ""), encoding="utf-8")
    MANIFEST_PATH.write_text(json.dumps(manifest_records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(render_notes(manifest_records), encoding="utf-8")

    print(
        json.dumps(
            {
                "generated_count": len(generated_rows),
                "runner_ids": runner_ids,
                "output_path": str(OUTPUT_PATH),
                "manifest_path": str(MANIFEST_PATH),
                "notes_path": str(NOTES_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
