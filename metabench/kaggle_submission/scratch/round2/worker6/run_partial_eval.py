from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

KAGGLE_ROOT = Path(__file__).resolve().parents[3]
if str(KAGGLE_ROOT) not in sys.path:
    sys.path.insert(0, str(KAGGLE_ROOT))

from eval_harness.local_llm import LocalLLM
from eval_harness.run_local import (
    evaluate_final_submission,
    infer_feasible,
    infer_parse_path,
    load_rows,
    parse_requested_ids,
)
from harness.prompt import build_system_prompt
from harness.runner import run_instance

WORKER_ROOT = Path(__file__).resolve().parent
QUESTIONS_PATH = WORKER_ROOT / "questions.partial.jsonl"
IDS_PATH = WORKER_ROOT / "runner_ids.txt"
RESULTS_ROOT = KAGGLE_ROOT / "results" / "full"
LOG_PATH = WORKER_ROOT / "runner-log.md"
DEFAULT_MODELS = [
    "gemini-flash-latest",
    "claude-sonnet-4.6",
    "gpt-5.4-mini",
]
API_FAILURE_NEEDLES = (
    "401",
    "402",
    "403",
    "429",
    "api key",
    "authentication",
    "billing",
    "credit balance",
    "insufficient_quota",
    "invalid_api_key",
    "payment",
    "quota",
    "rate limit",
    "rate_limit",
    "ratelimit",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run worker6 partial evals into results/full/<id>/ artifacts.")
    parser.add_argument(
        "--questions-file",
        type=Path,
        default=QUESTIONS_PATH,
        help="Path to worker-local questions.partial.jsonl.",
    )
    parser.add_argument(
        "--ids",
        default=f"@{IDS_PATH}",
        help="`all`, comma-separated ids, or @path/to/file.",
    )
    parser.add_argument(
        "--models",
        default=",".join(DEFAULT_MODELS),
        help="Comma-separated llm model ids.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=RESULTS_ROOT,
        help="Root directory for per-question artifacts.",
    )
    return parser.parse_args()


def select_rows(rows: list[dict[str, Any]], raw_ids: str) -> list[dict[str, Any]]:
    requested_ids = parse_requested_ids(raw_ids)
    if requested_ids is None:
        return rows
    selected = [row for row in rows if row["id"] in requested_ids]
    missing = sorted(requested_ids - {row["id"] for row in selected})
    if missing:
        raise ValueError(f"unknown ids: {', '.join(missing)}")
    return selected


def ensure_question_artifact(question_dir: Path, row: dict[str, Any]) -> None:
    question_dir.mkdir(parents=True, exist_ok=True)
    (question_dir / "question.json").write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")


def is_timeout_payload(payload: dict[str, Any]) -> bool:
    error_text = str(payload.get("error") or "").lower()
    return payload.get("stop_reason") == "wall_budget" or "timed out" in error_text


def is_api_failure(payload: dict[str, Any]) -> bool:
    error_text = str(payload.get("error") or "").lower()
    return bool(error_text) and any(needle in error_text for needle in API_FAILURE_NEEDLES)


def build_payload(row: dict[str, Any], model: str, system_prompt: str) -> dict[str, Any]:
    llm = LocalLLM(model, system_prompt)
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
    return {
        "id": row["id"],
        "model": model,
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


def load_saved_payloads(question_dir: Path, models: list[str]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for model in models:
        model_path = question_dir / f"{model}.json"
        if model_path.exists():
            payloads.append(json.loads(model_path.read_text()))
    return payloads


def format_parse_line(payload: dict[str, Any]) -> str:
    suffix = ""
    if payload.get("error"):
        suffix = f"; error={payload['error']}"
    return f"- `{payload['model']}`: `{payload['parse_path']}`; stop=`{payload['stop_reason']}`{suffix}"


def format_feasibility_line(payload: dict[str, Any]) -> str:
    gap_pct = payload.get("final_evaluation", {}).get("gap_pct")
    gap_text = "n/a" if gap_pct is None else f"{gap_pct:.2f}%"
    return (
        f"- `{payload['model']}`: feasible=`{payload['feasible']}`; "
        f"submission_source=`{payload['final_submission_source']}`; gap_pct={gap_text}"
    )


def format_score_line(payload: dict[str, Any], row: dict[str, Any]) -> str:
    objective = payload.get("final_evaluation", {}).get("details", {}).get("computed_length")
    if objective is None:
        objective = payload.get("final_evaluation", {}).get("details", {}).get("scored_cost")
    objective_text = "n/a" if objective is None else f"{objective:.3f}"
    return (
        f"- `{payload['model']}`: score={payload['score']:.2f}; baseline_obj={row['baseline_objective']}; "
        f"gold_obj={row['gold_objective']}; final_obj={objective_text}; wall_s={payload['wall_s']:.1f}"
    )


def format_transcript_line(payload: dict[str, Any]) -> str:
    transcript = payload.get("transcript") or []
    if not transcript:
        return f"- `{payload['model']}`: no transcript captured."
    if payload.get("parse_path") == "strict_parse_failed":
        return f"- `{payload['model']}`: transcript exists but protocol parse failed after {payload['n_exec_turns']} exec turns."
    if payload.get("stop_reason") == "decision_stop":
        return f"- `{payload['model']}`: coherent plan/exec flow; stopped after {payload['n_exec_turns']} exec turns."
    return f"- `{payload['model']}`: transcript ended with stop=`{payload['stop_reason']}` after {payload['n_exec_turns']} exec turns."


def build_suggested_fixes(payloads: list[dict[str, Any]]) -> list[str]:
    fixes: list[str] = []
    if any(payload.get("parse_path") == "strict_parse_failed" for payload in payloads):
        fixes.append("- Tighten protocol-label compliance; at least one run produced an unparseable exec turn.")
    if any(not payload.get("feasible", False) for payload in payloads):
        fixes.append("- Add stronger self-checks before stop so invalid assignments/tours are rejected before final answer.")
    if any(is_timeout_payload(payload) for payload in payloads):
        fixes.append("- Reduce per-turn search breadth or use a faster model; at least one run hit a timeout budget.")
    if any(is_api_failure(payload) for payload in payloads):
        fixes.append("- Re-run affected models only after resolving API/billing/rate-limit issues in `llm`.")
    if any(payload.get("score", 0.0) < 60.0 and payload.get("feasible", False) for payload in payloads):
        fixes.append("- Solver quality is weak on at least one feasible run; a better local-improvement strategy is needed.")
    if not fixes:
        fixes.append("- No urgent fixes from the current sample; rerun only if you need more stable rate estimates.")
    return fixes


def write_concerns(question_dir: Path, row: dict[str, Any], models: list[str]) -> None:
    payloads = load_saved_payloads(question_dir, models)
    lines = [f"# Concerns for `{row['id']}`", "", "## parse"]
    if payloads:
        lines.extend(format_parse_line(payload) for payload in payloads)
    else:
        lines.append("- No model artifacts written yet.")

    lines.extend(["", "## feasibility"])
    if payloads:
        lines.extend(format_feasibility_line(payload) for payload in payloads)
    else:
        lines.append("- No feasibility signal yet.")

    lines.extend(["", "## score-vs-baseline"])
    if payloads:
        lines.extend(format_score_line(payload, row) for payload in payloads)
    else:
        lines.append("- No score signal yet.")

    lines.extend(["", "## transcript coherence"])
    if payloads:
        lines.extend(format_transcript_line(payload) for payload in payloads)
    else:
        lines.append("- No transcript signal yet.")

    lines.extend(["", "## suggested fixes"])
    lines.extend(build_suggested_fixes(payloads))
    (question_dir / "concerns.md").write_text("\n".join(lines) + "\n")


def write_log(events: list[str]) -> None:
    lines = ["# Worker 6 Runner Log", ""]
    lines.extend(f"- {event}" for event in events)
    LOG_PATH.write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    models = [model.strip() for model in args.models.split(",") if model.strip()]
    if not models:
        raise ValueError("no models selected")

    rows = select_rows(load_rows(args.questions_file), args.ids)
    system_prompt = build_system_prompt()
    events: list[str] = []
    model_attempt_counts = {model: 0 for model in models}
    model_api_fail_counts = {model: 0 for model in models}
    skipped_models: set[str] = set()

    for row in rows:
        question_dir = args.output_dir / row["id"]
        ensure_question_artifact(question_dir, row)
        for model in models:
            if model in skipped_models:
                events.append(f"skipped remaining rows for `{model}` after two early API failures")
                continue

            model_attempt_counts[model] += 1
            attempts = 0
            payload: dict[str, Any] | None = None
            while attempts < 3:
                attempts += 1
                payload = build_payload(row, model, system_prompt)
                if not is_timeout_payload(payload):
                    break
                events.append(f"timeout retry {attempts} for `{row['id']}` on `{model}`")

            assert payload is not None
            if is_api_failure(payload) and model_attempt_counts[model] <= 2:
                model_api_fail_counts[model] += 1
                if model_attempt_counts[model] == 2 and model_api_fail_counts[model] == 2:
                    skipped_models.add(model)
                    events.append(f"model `{model}` failed on its first two rows with API/billing/rate-limit errors")

            model_path = question_dir / f"{model}.json"
            model_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            write_concerns(question_dir, row, models)
            parse_path = payload.get("parse_path")
            events.append(
                f"`{row['id']}` on `{model}` -> parse={parse_path} feasible={payload['feasible']} "
                f"score={payload['score']:.2f} stop={payload['stop_reason']}"
            )

    write_log(events)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
