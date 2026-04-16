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
OUTPUT_DIR = ROOT / "scratch" / "round2" / "worker7"
OUTPUT_PATH = OUTPUT_DIR / "questions.partial.jsonl"
RUNNER_IDS_PATH = OUTPUT_DIR / "runner_ids.txt"
NOTES_PATH = OUTPUT_DIR / "gen-notes.md"
MANIFEST_PATH = OUTPUT_DIR / "generation-manifest.json"

PORTFOLIO_CLASSES: tuple[str, ...] = ("cjs", "steiner", "graphcol", "tsp", "mwis", "ve")
ASSIGNED_CELLS: tuple[tuple[str, tuple[int, int, int]], ...] = (
    ("medium", (32, 33, 34)),
    ("medium", (35, 36, 37)),
    ("hard", (30, 31, 32)),
    ("hard", (33, 34, 35)),
)
MAX_SEED_FALLBACK = 4


def load_build_questions_module() -> Any:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("round2_worker7_build_questions", BUILD_QUESTIONS_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec from {BUILD_QUESTIONS_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_existing_portfolio_seeds() -> dict[str, set[int]]:
    used: dict[str, set[int]] = {"medium": set(), "hard": set()}
    for raw_line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        row = json.loads(line)
        if row.get("class") != "portfolio":
            continue
        difficulty = str(row["difficulty"])
        used.setdefault(difficulty, set()).add(int(row["seed"]))
    return used


def choose_component_classes(seed: int) -> tuple[str, str, str]:
    return tuple(random.Random(seed).sample(list(PORTFOLIO_CLASSES), 3))


def build_component_for_seed(
    *,
    bq: Any,
    builders: dict[str, Any],
    cls: str,
    difficulty: str,
    seed: int,
) -> tuple[Any, str | None]:
    builder = builders[cls]
    if difficulty == "medium":
        smoke_row = bq._build_timed_row(builder, seed, "medium")
        return smoke_row, None

    try:
        smoke_row = bq._build_timed_row(builder, seed, "hard")
        return smoke_row, None
    except Exception as exc:
        failures = [f"default: {bq._error_summary(exc)}"]

    for key, value in bq.HARD_SIZE_FALLBACKS.get(cls, ()):
        override = {key: value}
        try:
            smoke_row = bq._build_timed_row(builder, seed, "hard", config_override=override)
            return smoke_row, f"{cls} {key}={value} override"
        except Exception as exc:
            failures.append(f"{cls} {key}={value} override: {bq._error_summary(exc)}")

    raise RuntimeError(" | ".join(failures))


def build_portfolio_candidate(
    *,
    bq: Any,
    builders: dict[str, Any],
    difficulty: str,
    actual_seed: int,
) -> tuple[Any, tuple[str, str, str], list[str], list[str]]:
    component_classes = choose_component_classes(actual_seed)
    component_rows: list[Any] = []
    component_ids: list[str] = []
    component_overrides: list[str] = []

    for cls in component_classes:
        smoke_row, override_note = build_component_for_seed(
            bq=bq,
            builders=builders,
            cls=cls,
            difficulty=difficulty,
            seed=actual_seed,
        )
        component_rows.append(smoke_row)
        component_ids.append(str(smoke_row.row["id"]))
        if override_note is not None:
            component_overrides.append(override_note)

    portfolio_row = bq._build_portfolio_row(
        solo_rows=component_rows,
        difficulty=difficulty,
        seed=actual_seed,
        component_ids=tuple(component_ids),
    )
    return portfolio_row, component_classes, component_ids, component_overrides


def render_generated_line(item: dict[str, Any]) -> str:
    parts = [
        f"- generated `{item['actual_id']}` for requested seed {item['requested_seed']}",
        f"fallback attempts: {item['fallback_attempts']}",
        f"final classes {', '.join(item['component_classes'])}",
        f"components={item['component_ids']}",
    ]
    if item["component_overrides"]:
        parts.append(f"component overrides={item['component_overrides']}")
    return "; ".join(parts)


def render_notes(*, generated: list[dict[str, Any]], skipped: list[dict[str, Any]], runner_ids: list[str]) -> str:
    lines = [
        "# Worker 7 Generation Notes",
        "",
        f"- Generated rows: {len(generated)}",
        f"- Skipped slots: {len(skipped)}",
        f"- Runner ids: {', '.join(runner_ids) if runner_ids else '(none)'}",
        "",
        "## Generated",
        "",
    ]
    if not generated:
        lines.append("- None")
    else:
        lines.extend(render_generated_line(item) for item in generated)

    lines.extend(["", "## Skipped", ""])
    if not skipped:
        lines.append("- None")
    else:
        for item in skipped:
            lines.append(f"- `{item['requested_slot']}`: {item['reason']}")
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
    used_actual_seeds = load_existing_portfolio_seeds()

    generated_rows: list[Any] = []
    generated_notes: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    runner_ids: list[str] = []

    for difficulty, requested_seeds in ASSIGNED_CELLS:
        cell_first_id: str | None = None
        for requested_seed in requested_seeds:
            seed_failures: list[tuple[int, str]] = []
            generated_row = None
            component_classes: tuple[str, str, str] | None = None
            component_ids: list[str] | None = None
            component_overrides: list[str] | None = None
            actual_seed_used: int | None = None

            for candidate_seed in range(requested_seed, requested_seed + MAX_SEED_FALLBACK + 1):
                if candidate_seed in used_actual_seeds[difficulty]:
                    seed_failures.append((candidate_seed, "skipped because actual seed already used earlier in this difficulty"))
                    continue
                try:
                    generated_row, component_classes, component_ids, component_overrides = build_portfolio_candidate(
                        bq=bq,
                        builders=builders,
                        difficulty=difficulty,
                        actual_seed=candidate_seed,
                    )
                except Exception as exc:
                    seed_failures.append((candidate_seed, str(exc).replace("\n", " ")))
                    continue

                used_actual_seeds[difficulty].add(candidate_seed)
                actual_seed_used = candidate_seed
                break

            if generated_row is None or component_classes is None or component_ids is None or component_overrides is None:
                skipped.append(
                    {
                        "requested_slot": f"portfolio_{difficulty}_seed{requested_seed}",
                        "reason": (
                            f"failed after whole-row seed fallback: "
                            f"{'; '.join(f'seed={seed}: {reason}' for seed, reason in seed_failures) or 'no attempts recorded'}"
                        ),
                    }
                )
                continue

            generated_rows.append(generated_row)
            actual_id = str(generated_row.row["id"])
            if cell_first_id is None:
                cell_first_id = actual_id

            generated_notes.append(
                {
                    "requested_seed": requested_seed,
                    "actual_seed": actual_seed_used,
                    "actual_id": actual_id,
                    "difficulty": difficulty,
                    "component_classes": list(component_classes),
                    "component_ids": component_ids,
                    "component_overrides": component_overrides,
                    "fallback_attempts": (
                        "none"
                        if not seed_failures
                        else "; ".join(f"seed={seed}: {reason}" for seed, reason in seed_failures)
                    ),
                }
            )

        if cell_first_id is not None:
            runner_ids.append(cell_first_id)

    bq._sanity_check_round_trip(generated_rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bq._write_jsonl(OUTPUT_PATH, [entry.row for entry in generated_rows])
    RUNNER_IDS_PATH.write_text("\n".join(runner_ids) + "\n", encoding="utf-8")
    NOTES_PATH.write_text(
        render_notes(generated=generated_notes, skipped=skipped, runner_ids=runner_ids),
        encoding="utf-8",
    )
    MANIFEST_PATH.write_text(
        json.dumps(
            {
                "generated_count": len(generated_rows),
                "generated": generated_notes,
                "runner_ids": runner_ids,
                "skipped": skipped,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "generated_count": len(generated_rows),
                "output_path": str(OUTPUT_PATH),
                "runner_ids": runner_ids,
                "skipped_count": len(skipped),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
