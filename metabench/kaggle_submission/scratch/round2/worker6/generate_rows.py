from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

KAGGLE_ROOT = Path(__file__).resolve().parents[3]
if str(KAGGLE_ROOT) not in sys.path:
    sys.path.insert(0, str(KAGGLE_ROOT))

from scripts import build_questions as bq

WORKER_ROOT = Path(__file__).resolve().parent
QUESTIONS_PATH = WORKER_ROOT / "questions.partial.jsonl"
MANIFEST_PATH = WORKER_ROOT / "generation-manifest.json"
NOTES_PATH = WORKER_ROOT / "gen-notes.md"
RUNNER_IDS_PATH = WORKER_ROOT / "runner_ids.txt"
GLOBAL_QUESTIONS_PATH = KAGGLE_ROOT / "questions.jsonl"

WORKER_ID = 6
DIFFICULTY = "hard"
SIBLING_RESERVED_ACTUAL_SEEDS = frozenset(range(30, 42))
CHUNKS: tuple[tuple[str, tuple[int, int, int]], ...] = (
    ("Chunk A: gap-fill seeds 6, 11, 14", (6, 11, 14)),
    ("Chunk B: gap-fill seeds 15, 17, 21", (15, 17, 21)),
    ("Chunk C: seeds 24, 25, 26", (24, 25, 26)),
    ("Chunk D: seeds 27, 28, 29", (27, 28, 29)),
)
BUILDERS = {
    "cjs": bq._build_cjs_row,
    "steiner": bq._build_steiner_row,
    "graphcol": bq._build_graphcol_row,
    "tsp": bq._build_tsp_row,
    "mwis": bq._build_mwis_row,
    "ve": bq._build_ve_row,
}


def load_global_reserved_actual_seeds() -> set[int]:
    reserved: set[int] = set()
    with GLOBAL_QUESTIONS_PATH.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("class") == "portfolio" and row.get("difficulty") == DIFFICULTY:
                reserved.add(int(row["seed"]))
    return reserved


def build_component_override_label(cls: str, key: str, value: int) -> str:
    return f"{cls}: {cls} {key}={value} override"


def build_component_row(cls: str, actual_seed: int) -> tuple[bq.SmokeRow, list[str]]:
    failures: list[str] = []
    try:
        built = bq._build_timed_row(BUILDERS[cls], actual_seed, DIFFICULTY)
        return built, []
    except Exception as exc:  # noqa: BLE001
        failures.append(f"default: {bq._error_summary(exc)}")

    for key, value in bq.HARD_SIZE_FALLBACKS.get(cls, ()):
        try:
            built = bq._build_timed_row(
                BUILDERS[cls],
                actual_seed,
                DIFFICULTY,
                config_override={key: value},
            )
            return built, [build_component_override_label(cls, key, value)]
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{cls} {key}={value} override: {bq._error_summary(exc)}")

    raise RuntimeError(" | ".join(failures))


def build_portfolio_candidate(actual_seed: int) -> tuple[bq.SmokeRow, list[str], list[str], list[str]]:
    sampled_classes = random.Random(actual_seed).sample(list(bq.SOLO_CLASSES), 3)
    solo_rows: list[bq.SmokeRow] = []
    component_ids: list[str] = []
    component_overrides: list[str] = []
    for cls in sampled_classes:
        built_component, override_notes = build_component_row(cls, actual_seed)
        solo_rows.append(built_component)
        component_ids.append(str(built_component.row["id"]))
        component_overrides.extend(override_notes)

    portfolio_row = bq._build_portfolio_row(
        solo_rows=solo_rows,
        difficulty=DIFFICULTY,
        seed=actual_seed,
        component_ids=(component_ids[0], component_ids[1], component_ids[2]),
    )
    return portfolio_row, sampled_classes, component_ids, component_overrides


def format_attempts(attempts: list[dict[str, Any]]) -> str:
    if not attempts:
        return "none"
    return "; ".join(f"seed={item['actual_seed']}: {item['reason']}" for item in attempts)


def build_notes(manifest: dict[str, Any]) -> str:
    lines = ["# Worker 6 generation notes", ""]
    for record in manifest["records"]:
        lines.append(f"## {record['chunk_label']}")
        for row in record["rows"]:
            if row["id"] is not None:
                line = (
                    f"- generated `{row['id']}` for requested seed {row['requested_seed']}; "
                    f"fallback attempts: {format_attempts(row['attempts'])}; "
                    f"final classes {', '.join(row['classes'])}; "
                    f"components={repr(row['component_ids'])}"
                )
                if row["component_overrides"]:
                    line += f"; component overrides={repr(row['component_overrides'])}"
            else:
                line = (
                    f"- skipped requested `{DIFFICULTY}` seed {row['requested_seed']} after fallback attempts: "
                    f"{format_attempts(row['attempts'])}"
                )
            lines.append(line)
        lines.append("")

    lines.extend(
        [
            "## Runner ids",
            *(f"- `{question_id}`" for question_id in manifest["runner_question_ids"]),
            "",
            "## Summary",
            f"- rows_written: {sum(1 for record in manifest['records'] for row in record['rows'] if row['id'] is not None)}",
            f"- global_reserved_actual_seeds: {manifest['global_reserved_actual_seeds']}",
            f"- sibling_reserved_actual_seeds: {manifest['sibling_reserved_actual_seeds']}",
            f"- used_actual_seeds: {manifest['used_actual_seeds']}",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    WORKER_ROOT.mkdir(parents=True, exist_ok=True)

    global_reserved_actual_seeds = load_global_reserved_actual_seeds()
    reserved_actual_seeds = set(global_reserved_actual_seeds) | set(SIBLING_RESERVED_ACTUAL_SEEDS)
    used_actual_seeds: set[int] = set()
    generated_rows: list[bq.SmokeRow] = []
    records: list[dict[str, Any]] = []

    for chunk_label, requested_seeds in CHUNKS:
        chunk_rows: list[dict[str, Any]] = []
        for requested_seed in requested_seeds:
            attempts: list[dict[str, Any]] = []
            row_record: dict[str, Any] | None = None
            for actual_seed in range(requested_seed, requested_seed + 5):
                if actual_seed in global_reserved_actual_seeds:
                    attempts.append(
                        {
                            "actual_seed": actual_seed,
                            "reason": "skipped because actual seed already exists in global questions.jsonl",
                            "status": "reserved_global",
                        }
                    )
                    continue
                if actual_seed in SIBLING_RESERVED_ACTUAL_SEEDS:
                    attempts.append(
                        {
                            "actual_seed": actual_seed,
                            "reason": "skipped because actual seed is reserved for another round2 hard portfolio worker",
                            "status": "reserved_elsewhere",
                        }
                    )
                    continue
                if actual_seed in used_actual_seeds:
                    attempts.append(
                        {
                            "actual_seed": actual_seed,
                            "reason": "skipped because actual seed already used earlier in this difficulty",
                            "status": "used_local",
                        }
                    )
                    continue

                try:
                    portfolio_row, classes, component_ids, component_overrides = build_portfolio_candidate(actual_seed)
                except Exception as exc:  # noqa: BLE001
                    attempts.append(
                        {
                            "actual_seed": actual_seed,
                            "reason": bq._error_summary(exc),
                            "status": "failed",
                        }
                    )
                    continue

                generated_rows.append(portfolio_row)
                used_actual_seeds.add(actual_seed)
                row_record = {
                    "requested_seed": requested_seed,
                    "actual_seed": actual_seed,
                    "id": portfolio_row.row["id"],
                    "classes": classes,
                    "component_ids": component_ids,
                    "component_overrides": component_overrides,
                    "attempts": attempts,
                }
                break

            if row_record is None:
                row_record = {
                    "requested_seed": requested_seed,
                    "actual_seed": None,
                    "id": None,
                    "classes": None,
                    "component_ids": [],
                    "component_overrides": [],
                    "attempts": attempts,
                }
            chunk_rows.append(row_record)

        records.append({"chunk_label": chunk_label, "rows": chunk_rows})

    bq._sanity_check_round_trip(generated_rows)

    questions = [entry.row for entry in generated_rows]
    QUESTIONS_PATH.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in questions),
        encoding="utf-8",
    )

    generated_ids_in_order = [str(entry.row["id"]) for entry in generated_rows]
    runner_question_ids: list[str] = []
    for record in records:
        first_success = next((row["id"] for row in record["rows"] if row["id"] is not None), None)
        if first_success is not None:
            runner_question_ids.append(first_success)
    for question_id in generated_ids_in_order:
        if len(runner_question_ids) >= 4:
            break
        if question_id not in runner_question_ids:
            runner_question_ids.append(question_id)
    RUNNER_IDS_PATH.write_text("".join(f"{question_id}\n" for question_id in runner_question_ids), encoding="utf-8")

    manifest = {
        "worker": WORKER_ID,
        "difficulty": DIFFICULTY,
        "global_reserved_actual_seeds": sorted(global_reserved_actual_seeds),
        "sibling_reserved_actual_seeds": sorted(SIBLING_RESERVED_ACTUAL_SEEDS),
        "reserved_actual_seeds": sorted(reserved_actual_seeds),
        "used_actual_seeds": sorted(used_actual_seeds),
        "runner_question_ids": runner_question_ids,
        "records": records,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(build_notes(manifest), encoding="utf-8")

    print(
        f"Generated {len(generated_rows)} worker6 portfolio-hard rows "
        f"with runner ids {runner_question_ids}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
