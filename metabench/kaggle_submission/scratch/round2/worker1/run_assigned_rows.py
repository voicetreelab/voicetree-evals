#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from eval_harness.local_llm import LocalLLM
from eval_harness.run_local import (
    evaluate_final_submission,
    infer_feasible,
    infer_parse_path,
    looks_like_billing_error,
    slugify_model,
)
from harness.prompt import build_system_prompt
from harness.runner import run_instance

ROWS_PATH = ROOT / "scratch" / "round2" / "worker1" / "questions.partial.jsonl"
RUNNER_IDS_PATH = ROOT / "scratch" / "round2" / "worker1" / "runner_ids.txt"
RESULTS_ROOT = ROOT / "results" / "full"
SUMMARY_PATH = ROOT / "scratch" / "round2" / "worker1" / "runner-summary.json"

MODELS = (
    "gemini-flash-latest",
    "claude-sonnet-4.6",
    "gpt-5.4-mini",
)
# Initial attempt plus two retries on timeout aligns with the round-two child brief.
MAX_ATTEMPTS_PER_TIMEOUT = 3


def load_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_runner_ids(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_timeout_payload(payload: dict[str, Any]) -> bool:
    text = " ".join(
        str(part)
        for part in (
            payload.get("error"),
            payload.get("stop_reason"),
        )
        if part
    ).lower()
    return "timed out" in text or "timeout" in text or payload.get("stop_reason") == "wall_budget"


def make_skip_payload(
    *,
    row: dict[str, Any],
    model: str,
    reason: str,
    stop_reason: str,
) -> dict[str, Any]:
    return {
        "id": row["id"],
        "model": model,
        "model_slug": slugify_model(model),
        "class": row["class"],
        "difficulty": row["difficulty"],
        "seed": row["seed"],
        "gold_objective": row["gold_objective"],
        "baseline_objective": row["baseline_objective"],
        "value_cap": row["value_cap"],
        "error": reason,
        "feasible": False,
        "final_evaluation": None,
        "final_submission_source": None,
        "gap_pct": None,
        "n_exec_turns": 0,
        "parse_path": "not_run",
        "score": None,
        "score_after_cf": None,
        "score_at_stop": None,
        "stop_reason": stop_reason,
        "transcript": [],
        "wall_s": 0.0,
    }


def run_single_attempt(row: dict[str, Any], model: str, system_prompt: str) -> dict[str, Any]:
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
        "model_slug": slugify_model(model),
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
        "gap_pct": evaluation.get("gap_pct"),
        "parse_path": infer_parse_path(result),
        "transcript_len": len(result.get("transcript") or []),
    }


def attempt_row_model(
    *,
    row: dict[str, Any],
    model: str,
    system_prompt: str,
) -> dict[str, Any]:
    last_payload: dict[str, Any] | None = None
    timeout_errors: list[str] = []
    for attempt in range(1, MAX_ATTEMPTS_PER_TIMEOUT + 1):
        try:
            payload = run_single_attempt(row, model, system_prompt)
        except Exception as exc:
            payload = make_skip_payload(
                row=row,
                model=model,
                reason=f"{type(exc).__name__}: {exc}",
                stop_reason="runner_exception",
            )
        payload["attempt"] = attempt
        payload["retry_count"] = attempt - 1
        last_payload = payload
        if is_timeout_payload(payload) and attempt < MAX_ATTEMPTS_PER_TIMEOUT:
            timeout_errors.append(str(payload.get("error") or payload.get("stop_reason") or "timeout"))
            continue
        break
    assert last_payload is not None
    if is_timeout_payload(last_payload) and last_payload["attempt"] >= MAX_ATTEMPTS_PER_TIMEOUT:
        suffix = f" | exhausted {MAX_ATTEMPTS_PER_TIMEOUT} attempts"
        base_error = str(last_payload.get("error") or "timed out")
        if suffix not in base_error:
            last_payload["error"] = base_error + suffix
        last_payload["timeout_attempt_errors"] = timeout_errors
    return last_payload


def summarize_failure_reason(payload: dict[str, Any]) -> str:
    evaluation = payload.get("final_evaluation") or {}
    details = evaluation.get("details") or {}
    reason = details.get("failure_reason")
    if reason:
        return str(reason)
    error = payload.get("error")
    if error:
        return str(error)
    return "-"


def format_optional_number(value: Any, digits: int = 2) -> str:
    if value is None:
        return "-"
    return f"{float(value):.{digits}f}"


def render_concerns(row: dict[str, Any], payloads: dict[str, dict[str, Any]]) -> str:
    lines = [
        f"# Concerns — {row['id']}",
        "",
        "## Parse",
    ]
    for model in MODELS:
        payload = payloads[model]
        lines.append(
            f"- `{model}`: parse_path=`{payload.get('parse_path')}`; "
            f"n_exec_turns={payload.get('n_exec_turns', 0)}; error={payload.get('error') or '-'}"
        )

    lines.extend(["", "## Feasibility"])
    for model in MODELS:
        payload = payloads[model]
        lines.append(
            f"- `{model}`: feasible={payload.get('feasible')}; "
            f"reason={summarize_failure_reason(payload)}"
        )

    lines.extend(["", "## Score vs Baseline"])
    for model in MODELS:
        payload = payloads[model]
        lines.append(
            f"- `{model}`: score={format_optional_number(payload.get('score'))}; "
            f"gap_pct={format_optional_number(payload.get('gap_pct'))}; "
            f"baseline_objective={format_optional_number(payload.get('baseline_objective'))}"
        )

    lines.extend(["", "## Transcript Coherence"])
    for model in MODELS:
        payload = payloads[model]
        lines.append(
            f"- `{model}`: transcript_len={len(payload.get('transcript') or [])}; "
            f"stop_reason={payload.get('stop_reason')}; final_submission_source={payload.get('final_submission_source') or '-'}"
        )

    fixes: list[str] = []
    if any(payloads[model].get("parse_path") not in {"strict_protocol", "strict_protocol_cf"} for model in MODELS):
        fixes.append("Prompt contract is still brittle on at least one model; inspect label emission and NEXT_SUB control fields.")
    if any(not bool(payloads[model].get("feasible")) for model in MODELS):
        fixes.append("At least one model ended infeasible or skipped; inspect the final submission against the verifier-specific failure reason.")
    if any(is_timeout_payload(payloads[model]) for model in MODELS):
        fixes.append("Timeout pressure appeared on this row; reduce prompt surface area or narrow the search step requested from the model.")
    if any(looks_like_billing_error(str(payloads[model].get("error"))) for model in MODELS):
        fixes.append("A provider returned a billing or rate-limit style failure; rerun once quota or rate limits recover.")
    if any(
        payloads[model].get("score") is not None and float(payloads[model]["score"]) <= 0.0
        for model in MODELS
    ):
        fixes.append("One or more models failed to capture useful headroom; compare transcript decisions against the baseline and gold gap.")

    lines.extend(["", "## Suggested Fixes"])
    if not fixes:
        lines.append("- None.")
    else:
        for fix in fixes:
            lines.append(f"- {fix}")
    lines.append("")
    return "\n".join(lines)


def summarize_model_payloads(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    parse_paths = Counter(str(payload.get("parse_path")) for payload in payloads)
    return {
        "rows_seen": len(payloads),
        "feasible_rows": sum(1 for payload in payloads if bool(payload.get("feasible"))),
        "error_rows": sum(1 for payload in payloads if payload.get("error")),
        "timeout_rows": sum(1 for payload in payloads if is_timeout_payload(payload)),
        "parse_paths": dict(parse_paths),
        "avg_score": (
            sum(float(payload["score"]) for payload in payloads if payload.get("score") is not None)
            / max(1, sum(1 for payload in payloads if payload.get("score") is not None))
        ),
    }


def main() -> int:
    rows = load_rows(ROWS_PATH)
    row_by_id = {row["id"]: row for row in rows}
    runner_ids = load_runner_ids(RUNNER_IDS_PATH)
    missing_ids = [row_id for row_id in runner_ids if row_id not in row_by_id]
    if missing_ids:
        raise RuntimeError(f"runner ids missing from partial rows: {', '.join(missing_ids)}")

    selected_rows = [row_by_id[row_id] for row_id in runner_ids]
    system_prompt = build_system_prompt()

    attempted_rows_per_model = defaultdict(int)
    early_billing_errors = defaultdict(int)
    skip_models: dict[str, str] = {}
    payloads_by_model: dict[str, list[dict[str, Any]]] = {model: [] for model in MODELS}

    for row in selected_rows:
        row_dir = RESULTS_ROOT / row["id"]
        row_dir.mkdir(parents=True, exist_ok=True)
        write_json(row_dir / "question.json", row)

        row_payloads: dict[str, dict[str, Any]] = {}
        for model in MODELS:
            if model in skip_models:
                payload = make_skip_payload(
                    row=row,
                    model=model,
                    reason=skip_models[model],
                    stop_reason="model_skipped_after_early_api_errors",
                )
            else:
                attempted_rows_per_model[model] += 1
                payload = attempt_row_model(row=row, model=model, system_prompt=system_prompt)
                if looks_like_billing_error(str(payload.get("error"))):
                    if attempted_rows_per_model[model] <= 2:
                        early_billing_errors[model] += 1
                    if early_billing_errors[model] >= 2:
                        skip_models[model] = str(payload.get("error") or "billing or rate limit on first two rows")

            row_payloads[model] = payload
            payloads_by_model[model].append(payload)
            write_json(row_dir / f"{model}.json", payload)

        (row_dir / "concerns.md").write_text(render_concerns(row, row_payloads), encoding="utf-8")

    summary = {
        "question_ids": runner_ids,
        "models": list(MODELS),
        "attempted_rows_per_model": dict(attempted_rows_per_model),
        "early_billing_errors": dict(early_billing_errors),
        "skip_models": skip_models,
        "per_model": {
            model: summarize_model_payloads(payloads_by_model[model])
            for model in MODELS
        },
        "per_question": {
            row_id: {
                model: {
                    "parse_path": next(
                        payload["parse_path"]
                        for payload in payloads_by_model[model]
                        if payload["id"] == row_id
                    ),
                    "score": next(
                        payload["score"]
                        for payload in payloads_by_model[model]
                        if payload["id"] == row_id
                    ),
                    "feasible": next(
                        payload["feasible"]
                        for payload in payloads_by_model[model]
                        if payload["id"] == row_id
                    ),
                    "error": next(
                        payload["error"]
                        for payload in payloads_by_model[model]
                        if payload["id"] == row_id
                    ),
                }
                for model in MODELS
            }
            for row_id in runner_ids
        },
    }
    write_json(SUMMARY_PATH, summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
