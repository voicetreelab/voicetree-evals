from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from eval_harness.local_llm import LocalLLM
from harness.prompt import build_system_prompt
from harness.runner import _evaluate_submission, _initial_best_guess, run_instance

KAGGLE_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = KAGGLE_ROOT / "questions.jsonl"
RESULTS_ROOT = KAGGLE_ROOT / "results" / "runs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m eval_harness.run_local",
        description="Run local parity evals through the production run_instance() harness.",
    )
    parser.add_argument("--model", required=True, help="`llm` model id, for example `gemini-flash-latest`.")
    parser.add_argument(
        "--ids",
        required=True,
        help="`all`, a comma-separated list of ids, or `@path/to/file` with one id per line.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap after filtering ids.",
    )
    parser.add_argument(
        "--questions-file",
        type=Path,
        default=QUESTIONS_PATH,
        help="JSONL file to load rows from. Defaults to kaggle_submission/questions.jsonl.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RESULTS_ROOT,
        help="Directory to write per-model JSON results into. Defaults to kaggle_submission/results/runs.",
    )
    return parser.parse_args()


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open() as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def parse_requested_ids(raw_ids: str) -> set[str] | None:
    if raw_ids == "all":
        return None
    if raw_ids.startswith("@"):
        source = Path(raw_ids[1:]).expanduser()
        content = source.read_text()
        tokens = content.replace(",", "\n").splitlines()
    else:
        tokens = raw_ids.split(",")
    requested = {token.strip() for token in tokens if token.strip()}
    if not requested:
        raise ValueError("no ids selected")
    return requested


def slugify_model(model: str) -> str:
    return model.replace("/", "_")


def select_submission_source(result: dict[str, Any], row: dict[str, Any]) -> tuple[str, Any]:
    if result.get("cf_parsed"):
        return "cf_parsed", result["cf_parsed"].get("best_guess")
    if result.get("parsed"):
        return "parsed", result["parsed"].get("best_guess")
    return (
        "baseline",
        _initial_best_guess(
            row["instance"],
            cls=row["class"],
            components=row.get("components"),
        ),
    )


def evaluate_final_submission(result: dict[str, Any], row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    submission_source, submission = select_submission_source(result, row)
    evaluation = _evaluate_submission(
        cls=row["class"],
        instance=row["instance"],
        submission=submission,
        components=row.get("components"),
    )
    return submission_source, evaluation


def infer_feasible(evaluation: dict[str, Any]) -> bool:
    if evaluation["mode"] == "portfolio":
        return bool(evaluation["components"]) and all(
            bool(component.get("feasible")) for component in evaluation["components"]
        )
    return bool(evaluation.get("feasible"))


def infer_parse_path(result: dict[str, Any]) -> str:
    parse_events = result.get("parse_events") or []
    modes = [str(event.get("mode")) for event in parse_events]
    if any(mode == "judge_rescue" for mode in modes):
        return "judge_rescue"
    if any(mode == "partial_rescue" for mode in modes):
        return "partial_rescue"
    if any(mode == "strict_parse_failed" for mode in modes):
        return "strict_parse_failed"
    if result.get("cf_parsed"):
        return "strict_protocol_cf"
    if result.get("parsed"):
        return "strict_protocol"
    return "baseline_only"


def looks_like_billing_error(message: str | None) -> bool:
    text = (message or "").lower()
    needles = (
        "401",
        "402",
        "insufficient_quota",
        "quota",
        "billing",
        "credit balance",
        "payment",
    )
    return any(needle in text for needle in needles)


def format_summary(payload: dict[str, Any]) -> str:
    error = payload.get("error") or "-"
    return (
        f"{payload['id']} | {payload['feasible']} | {payload['score']:.2f} | "
        f"{payload['wall_s']:.1f}s | {payload['stop_reason']} | {payload['n_exec_turns']} | {error}"
    )


def main() -> int:
    args = parse_args()
    rows = load_rows(args.questions_file)
    requested_ids = parse_requested_ids(args.ids)
    if requested_ids is None:
        selected = rows
    else:
        selected = [row for row in rows if row["id"] in requested_ids]
        missing = sorted(requested_ids - {row["id"] for row in selected})
        if missing:
            raise ValueError(f"unknown ids: {', '.join(missing)}")
    if args.limit is not None:
        selected = selected[: args.limit]
    if not selected:
        raise ValueError("no rows matched the requested ids")

    model_slug = slugify_model(args.model)
    output_dir = args.output_dir / model_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    wall_times: list[float] = []
    system_prompt = build_system_prompt()
    for row in selected:
        llm = LocalLLM(args.model, system_prompt)
        result = run_instance(
            llm,
            row["instance"],
            row["class"],
            row["difficulty"],
            row["seed"],
            row["gold_objective"],
            row["baseline_objective"],
            row["value_cap"],
            components=row.get("components"),
        )
        submission_source, evaluation = evaluate_final_submission(result, row)
        payload = {
            "id": row["id"],
            "model": args.model,
            "model_slug": model_slug,
            "class": row["class"],
            "difficulty": row["difficulty"],
            "seed": row["seed"],
            "gold_objective": row["gold_objective"],
            "baseline_objective": row["baseline_objective"],
            "value_cap": row["value_cap"],
            **result,
            "feasible": infer_feasible(evaluation),
            "final_submission_source": submission_source,
            "final_evaluation": evaluation,
            "parse_path": infer_parse_path(result),
        }
        output_path = output_dir / f"{row['id']}.json"
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(format_summary(payload), flush=True)

        wall_times.append(float(result["wall_s"]))
        if looks_like_billing_error(result.get("error")):
            break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
