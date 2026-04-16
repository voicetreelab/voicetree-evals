#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = Path(__file__).resolve().with_name("run_assigned_rows.py")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.prompt import build_system_prompt


def load_runner_module() -> Any:
    spec = importlib.util.spec_from_file_location("worker5_runner", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module spec from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def budget_skip_reason(model_payload: dict[str, Any]) -> str:
    return (
        "skipped after ve_medium_seed5 because repeating this model's observed row-1 wall time "
        f"({float(model_payload['wall_s']):.1f}s) across the remaining rows would blow past the "
        "worker's 15-20 minute budget"
    )


def main() -> int:
    runner = load_runner_module()
    rows = runner.load_rows(runner.ROWS_PATH)
    row_by_id = {row["id"]: row for row in rows}
    runner_ids = runner.load_runner_ids(runner.RUNNER_IDS_PATH)
    system_prompt = build_system_prompt()

    seed_row_id = "ve_medium_seed5"
    seed_row_dir = runner.RESULTS_ROOT / seed_row_id
    gemini_seed = load_json(seed_row_dir / "gemini-flash-latest.json")
    sonnet_seed = load_json(seed_row_dir / "claude-sonnet-4.6.json")
    skip_reasons = {
        "gemini-flash-latest": budget_skip_reason(gemini_seed),
        "claude-sonnet-4.6": budget_skip_reason(sonnet_seed),
    }

    for row_id in runner_ids:
        row = row_by_id[row_id]
        row_dir = runner.RESULTS_ROOT / row_id
        row_dir.mkdir(parents=True, exist_ok=True)
        write_json(row_dir / "question.json", row)

        row_payloads: dict[str, dict[str, Any]] = {}
        for model in runner.MODELS:
            model_path = row_dir / f"{model}.json"
            if model_path.exists():
                payload = load_json(model_path)
            elif model in skip_reasons:
                payload = runner.make_skip_payload(
                    row=row,
                    model=model,
                    reason=skip_reasons[model],
                    stop_reason="model_skipped_by_parent_budget_guardrail",
                )
                write_json(model_path, payload)
            else:
                payload = runner.attempt_row_model(
                    row=row,
                    model=model,
                    system_prompt=system_prompt,
                )
                write_json(model_path, payload)
            row_payloads[model] = payload

        (row_dir / "concerns.md").write_text(
            runner.render_concerns(row, row_payloads),
            encoding="utf-8",
        )

    payloads_by_model = {model: [] for model in runner.MODELS}
    for row_id in runner_ids:
        row_dir = runner.RESULTS_ROOT / row_id
        for model in runner.MODELS:
            payloads_by_model[model].append(load_json(row_dir / f"{model}.json"))

    summary = {
        "question_ids": runner_ids,
        "models": list(runner.MODELS),
        "skip_reasons": skip_reasons,
        "per_model": {
            model: runner.summarize_model_payloads(payloads_by_model[model])
            for model in runner.MODELS
        },
        "per_question": {
            row_id: {
                model: {
                    "parse_path": load_json(runner.RESULTS_ROOT / row_id / f"{model}.json").get("parse_path"),
                    "score": load_json(runner.RESULTS_ROOT / row_id / f"{model}.json").get("score"),
                    "feasible": load_json(runner.RESULTS_ROOT / row_id / f"{model}.json").get("feasible"),
                    "error": load_json(runner.RESULTS_ROOT / row_id / f"{model}.json").get("error"),
                }
                for model in runner.MODELS
            }
            for row_id in runner_ids
        },
    }
    write_json(runner.SUMMARY_PATH, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
