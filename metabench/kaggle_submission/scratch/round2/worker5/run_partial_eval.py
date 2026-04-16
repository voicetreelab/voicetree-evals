from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
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
IDS_PATH = WORKER_ROOT / "child-question-ids.txt"
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
PER_ATTEMPT_TIMEOUT_S = 600
MAX_ATTEMPTS = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run worker5 partial evals into results/full/<id>/ artifacts.")
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
    parser.add_argument("--single-run", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--row-id", help=argparse.SUPPRESS)
    parser.add_argument("--model", help=argparse.SUPPRESS)
    parser.add_argument("--payload-out", type=Path, help=argparse.SUPPRESS)
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


def get_row_by_id(rows: list[dict[str, Any]], row_id: str) -> dict[str, Any]:
    for row in rows:
        if row["id"] == row_id:
            return row
    raise ValueError(f"unknown row id: {row_id}")


def ensure_question_artifact(question_dir: Path, row: dict[str, Any]) -> None:
    question_dir.mkdir(parents=True, exist_ok=True)
    (question_dir / "question.json").write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")


def is_timeout_payload(payload: dict[str, Any]) -> bool:
    error_text = str(payload.get("error") or "").lower()
    return payload.get("stop_reason") in {"wall_budget", "runner_timeout"} or "timed out" in error_text


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


def build_runner_placeholder(
    *,
    row: dict[str, Any],
    model: str,
    stop_reason: str,
    error: str,
    wall_s: float,
    attempt_count: int,
) -> dict[str, Any]:
    evaluation_mode = "portfolio" if row["class"] == "portfolio" else row["class"]
    payload = {
        "id": row["id"],
        "model": model,
        "class": row["class"],
        "difficulty": row["difficulty"],
        "seed": row["seed"],
        "gold_objective": row["gold_objective"],
        "baseline_objective": row["baseline_objective"],
        "value_cap": row["value_cap"],
        "transcript": [],
        "n_exec_turns": 0,
        "parse_events": [],
        "parsed": {},
        "cf_parsed": {},
        "score": 0.0,
        "wall_s": wall_s,
        "error": error,
        "stop_reason": stop_reason,
        "feasible": False,
        "final_submission_source": "baseline",
        "final_evaluation": {
            "mode": evaluation_mode,
            "gap_pct": None,
            "details": {},
            "components": [] if evaluation_mode == "portfolio" else None,
        },
        "parse_path": stop_reason,
        "attempt_count": attempt_count,
    }
    return payload


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
    details = payload.get("final_evaluation", {}).get("details", {})
    objective = details.get("computed_length")
    if objective is None:
        objective = details.get("scored_cost")
    if objective is None:
        objective = details.get("captured_value")
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
        fixes.append("- Add stronger self-checks before stop so invalid portfolio components are rejected before final answer.")
    if any(is_timeout_payload(payload) for payload in payloads):
        fixes.append("- At least one run exhausted the 600s local wrapper budget; investigate model latency or prompt search breadth.")
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
    lines = ["# Worker 5 Runner Log", ""]
    lines.extend(f"- {event}" for event in events)
    LOG_PATH.write_text("\n".join(lines) + "\n")


def run_single(args: argparse.Namespace) -> int:
    if not args.row_id or not args.model or args.payload_out is None:
        raise ValueError("--single-run requires --row-id, --model, and --payload-out")
    rows = load_rows(args.questions_file)
    row = get_row_by_id(rows, args.row_id)
    payload = build_payload(row, args.model, build_system_prompt())
    args.payload_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


def run_attempt(script_path: Path, row: dict[str, Any], model: str) -> tuple[dict[str, Any], str]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir=WORKER_ROOT) as handle:
        payload_path = Path(handle.name)
    command = [
        sys.executable,
        str(script_path),
        "--single-run",
        "--questions-file",
        str(QUESTIONS_PATH),
        "--row-id",
        row["id"],
        "--model",
        model,
        "--payload-out",
        str(payload_path),
    ]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=PER_ATTEMPT_TIMEOUT_S,
            cwd=str(KAGGLE_ROOT),
            check=False,
        )
    except subprocess.TimeoutExpired:
        if payload_path.exists():
            payload_path.unlink()
        return (
            build_runner_placeholder(
                row=row,
                model=model,
                stop_reason="runner_timeout",
                error=f"subprocess timed out after {PER_ATTEMPT_TIMEOUT_S}s",
                wall_s=float(PER_ATTEMPT_TIMEOUT_S),
                attempt_count=1,
            ),
            "timeout",
        )

    wall_s = time.monotonic() - started
    if completed.returncode == 0 and payload_path.exists():
        payload = json.loads(payload_path.read_text())
        payload_path.unlink()
        payload["wall_s"] = float(payload.get("wall_s", wall_s))
        return payload, "ok"

    stderr = (completed.stderr or completed.stdout or "").strip()
    if payload_path.exists():
        payload_path.unlink()
    return (
        build_runner_placeholder(
            row=row,
            model=model,
            stop_reason="runner_error",
            error=f"subprocess exited {completed.returncode}: {stderr[:1000] or 'no stderr'}",
            wall_s=wall_s,
            attempt_count=1,
        ),
        "error",
    )


def main() -> int:
    args = parse_args()
    if args.single_run:
        return run_single(args)

    models = [model.strip() for model in args.models.split(",") if model.strip()]
    if not models:
        raise ValueError("no models selected")

    rows = select_rows(load_rows(args.questions_file), args.ids)
    script_path = Path(__file__).resolve()
    events: list[str] = []

    for row in rows:
        question_dir = args.output_dir / row["id"]
        ensure_question_artifact(question_dir, row)
        for model in models:
            attempts = 0
            payload: dict[str, Any] | None = None
            while attempts < MAX_ATTEMPTS:
                attempts += 1
                payload, status = run_attempt(script_path, row, model)
                payload["attempt_count"] = attempts
                if status != "timeout":
                    break
                if attempts < MAX_ATTEMPTS:
                    events.append(
                        f"timeout retry {attempts} for `{row['id']}` on `{model}` after {PER_ATTEMPT_TIMEOUT_S}s"
                    )

            assert payload is not None
            model_path = question_dir / f"{model}.json"
            model_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            write_concerns(question_dir, row, models)
            parse_path = payload.get("parse_path")
            events.append(
                f"`{row['id']}` on `{model}` -> parse={parse_path} feasible={payload['feasible']} "
                f"score={payload['score']:.2f} stop={payload['stop_reason']} attempts={payload['attempt_count']}"
            )

    write_log(events)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
