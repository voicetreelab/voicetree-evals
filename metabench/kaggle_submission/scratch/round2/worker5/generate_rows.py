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
OUTPUT_DIR = ROOT / "scratch" / "round2" / "worker5"
OUTPUT_PATH = OUTPUT_DIR / "questions.partial.jsonl"
NOTES_PATH = OUTPUT_DIR / "gen-notes.md"
RUNNER_IDS_PATH = OUTPUT_DIR / "child-question-ids.txt"

ASSIGNED_SEEDS: tuple[int, ...] = (14, 15, 17, 21, 24, 25, 26, 27, 28, 29, 30, 31)
CHUNK_STARTS = {14, 21, 26, 29}
MAX_SEED_FALLBACK = 4
SOLO_CLASSES = ("cjs", "steiner", "graphcol", "tsp", "mwis", "ve")
MEDIUM_MWIS_SIZE_FALLBACKS: tuple[int, ...] = (100, 80)


def load_build_questions_module() -> Any:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("worker5_round2_build_questions", BUILD_QUESTIONS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec from {BUILD_QUESTIONS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_existing_portfolio_medium_seeds() -> set[int]:
    used: set[int] = set()
    for raw_line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        row_id = str(row.get("id", ""))
        if row_id.startswith("portfolio_medium_seed"):
            used.add(int(row_id.split("seed", 1)[1]))
    return used


def choose_component_classes(seed: int) -> tuple[str, str, str]:
    return tuple(random.Random(seed).sample(SOLO_CLASSES, 3))


def build_component_row(
    *,
    bq: Any,
    cls: str,
    seed: int,
) -> tuple[Any, str | None]:
    builders = {
        "cjs": bq._build_cjs_row,
        "steiner": bq._build_steiner_row,
        "graphcol": bq._build_graphcol_row,
        "tsp": bq._build_tsp_row,
        "mwis": bq._build_mwis_row,
        "ve": bq._build_ve_row,
    }
    builder = builders[cls]
    if cls != "mwis":
        return bq._build_timed_row(builder, seed, "medium"), None

    try:
        return bq._build_timed_row(builder, seed, "medium"), None
    except Exception as default_exc:
        failure_parts = [f"default: {bq._error_summary(default_exc)}"]
        for n_nodes in MEDIUM_MWIS_SIZE_FALLBACKS:
            try:
                return (
                    bq._build_timed_row(builder, seed, "medium", config_override={"n_nodes": n_nodes}),
                    f"mwis n_nodes={n_nodes} override",
                )
            except Exception as exc:
                failure_parts.append(f"n_nodes={n_nodes}: {bq._error_summary(exc)}")
        raise RuntimeError(" | ".join(failure_parts))


def build_portfolio_row_for_seed(
    *,
    bq: Any,
    actual_seed: int,
) -> tuple[Any, tuple[str, str, str], tuple[str, str, str], list[str]]:
    component_classes = choose_component_classes(actual_seed)
    solo_rows = []
    component_override_notes: list[str] = []
    for cls in component_classes:
        solo_row, override_note = build_component_row(bq=bq, cls=cls, seed=actual_seed)
        solo_rows.append(solo_row)
        if override_note is not None:
            component_override_notes.append(f"{cls}: {override_note}")
    component_ids = tuple(entry.row["id"] for entry in solo_rows)
    portfolio_row = bq._build_portfolio_row(
        solo_rows=solo_rows,
        difficulty="medium",
        seed=actual_seed,
        component_ids=component_ids,
    )
    return portfolio_row, component_classes, component_ids, component_override_notes


def render_attempt_summary(attempt: dict[str, Any]) -> str:
    return f"{attempt['actual_seed']} ({attempt['status']}): {attempt['reason']}"


def render_notes(
    *,
    generated_rows: list[Any],
    attempts_by_request: list[dict[str, Any]],
    skipped: list[dict[str, Any]],
    runner_ids: list[str],
) -> str:
    lines = [
        "# Round 2 Worker 5 Generation Notes",
        "",
        f"- Generated rows: {len(generated_rows)}",
        f"- Skipped requested seeds: {len(skipped)}",
        f"- Runner ids: {', '.join(runner_ids) if runner_ids else '(none)'}",
        "",
        "## Generated",
        "",
        "| requested_seed | actual_id | actual_seed | component_classes | component_ids | notes |",
        "|---:|---|---:|---|---|---|",
    ]
    for smoke_row in generated_rows:
        component_classes = ",".join(smoke_row.row["component_classes"])
        component_ids = ",".join(smoke_row.row["component_ids"])
        notes = (smoke_row.notes or "").replace("\n", " ").replace("|", "\\|")
        lines.append(
            f"| {smoke_row.requested_seed} | {smoke_row.row['id']} | {smoke_row.row['seed']} | "
            f"{component_classes} | {component_ids} | {notes or '-'} |"
        )

    lines.extend(["", "## Attempts", ""])
    for record in attempts_by_request:
        request = record["requested_seed"]
        lines.append(f"- requested `{request}`:")
        if not record["attempts"]:
            lines.append("  - none")
            continue
        for attempt in record["attempts"]:
            lines.append(f"  - {render_attempt_summary(attempt)}")

    lines.extend(["", "## Skipped", ""])
    if not skipped:
        lines.append("- None")
    else:
        for item in skipped:
            lines.append(f"- `portfolio_medium_seed{item['requested_seed']}`: {item['reason']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    bq = load_build_questions_module()
    used_actual_seeds = load_existing_portfolio_medium_seeds()

    generated_rows: list[Any] = []
    attempts_by_request: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    runner_ids: list[str] = []

    for requested_seed in ASSIGNED_SEEDS:
        attempts: list[dict[str, Any]] = []
        generated = None
        component_classes: tuple[str, str, str] | None = None
        component_ids: tuple[str, str, str] | None = None
        component_override_notes: list[str] = []

        for actual_seed in range(requested_seed, requested_seed + MAX_SEED_FALLBACK + 1):
            if actual_seed in used_actual_seeds:
                attempts.append(
                    {
                        "actual_seed": actual_seed,
                        "status": "reserved",
                        "reason": "skipped because portfolio_medium seed already exists globally or was used earlier",
                    }
                )
                continue

            try:
                generated, component_classes, component_ids, component_override_notes = build_portfolio_row_for_seed(
                    bq=bq,
                    actual_seed=actual_seed,
                )
            except Exception as exc:
                attempts.append(
                    {
                        "actual_seed": actual_seed,
                        "status": "failed",
                        "reason": bq._error_summary(exc),
                    }
                )
                continue

            used_actual_seeds.add(actual_seed)
            note = bq._build_fallback_note(
                cls="portfolio",
                difficulty="medium",
                requested_seed=requested_seed,
                actual_seed=actual_seed,
                seed_failures=[(item["actual_seed"], item["reason"]) for item in attempts],
            )
            if component_override_notes:
                suffix = f"Applied component fallback(s): {', '.join(component_override_notes)}."
                note = suffix if note is None else f"{note} {suffix}"
            generated = bq._annotate_row(generated, requested_seed=requested_seed, note=note)
            generated.row["component_classes"] = list(component_classes)
            generated.row["component_ids"] = list(component_ids)
            attempts.append(
                {
                    "actual_seed": actual_seed,
                    "status": "generated",
                    "reason": ", ".join(component_ids + tuple(component_override_notes)),
                }
            )
            generated_rows.append(generated)
            if requested_seed in CHUNK_STARTS:
                runner_ids.append(str(generated.row["id"]))
            break

        attempts_by_request.append(
            {
                "requested_seed": requested_seed,
                "attempts": attempts,
            }
        )

        if generated is None:
            skipped.append(
                {
                    "requested_seed": requested_seed,
                    "reason": "; ".join(render_attempt_summary(item) for item in attempts) or "no attempts recorded",
                }
            )

    bq._sanity_check_round_trip(generated_rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_PATH.write_text(
        render_notes(
            generated_rows=generated_rows,
            attempts_by_request=attempts_by_request,
            skipped=skipped,
            runner_ids=runner_ids,
        ),
        encoding="utf-8",
    )
    for smoke_row in generated_rows:
        smoke_row.row.pop("component_classes", None)
        smoke_row.row.pop("component_ids", None)
    bq._write_jsonl(OUTPUT_PATH, [entry.row for entry in generated_rows])
    RUNNER_IDS_PATH.write_text("\n".join(runner_ids) + "\n", encoding="utf-8")

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
