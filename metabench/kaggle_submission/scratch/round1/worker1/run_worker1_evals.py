#!/usr/bin/env python3
from __future__ import annotations

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
    slugify_model,
)
from harness.prompt import build_system_prompt
from harness.runner import run_instance

PARTIAL_PATH = KAGGLE_ROOT / "scratch" / "round1" / "worker1" / "questions.partial.jsonl"
RESULTS_ROOT = KAGGLE_ROOT / "results" / "full"
SUMMARY_PATH = KAGGLE_ROOT / "scratch" / "round1" / "worker1" / "runner-summary.json"

QUESTION_IDS = (
    "cjs_medium_seed2",
    "cjs_medium_seed5",
    "cjs_medium_seed8",
    "steiner_medium_seed2",
)
MODELS = (
    "gemini-flash-latest",
    "claude-sonnet-4.6",
    "gpt-5.4-mini",
)
MAX_ATTEMPTS = 3
API_ERROR_NEEDLES = (
    "401",
    "402",
    "429",
    "insufficient_quota",
    "quota",
    "billing",
    "credit balance",
    "payment",
    "rate limit",
    "rate_limit",
    "resource exhausted",
)


def load_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            row = json.loads(line)
            rows[str(row["id"])] = row
    return rows


def is_api_error(message: str | None) -> bool:
    text = (message or "").lower()
    return any(needle in text for needle in API_ERROR_NEEDLES)


def is_timeout_payload(payload: dict[str, Any]) -> bool:
    error_text = str(payload.get("error") or "").lower()
    if "llm cli timed out" in error_text:
        return True
    return False


def extract_gap_pct(evaluation: dict[str, Any]) -> float | None:
    if evaluation.get("mode") == "portfolio":
        return None
    raw_gap = evaluation.get("gap_pct")
    if raw_gap is None:
        return None
    return float(raw_gap)


def build_payload(model: str, row: dict[str, Any]) -> dict[str, Any]:
    system_prompt = build_system_prompt()
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
    final_gap_pct = extract_gap_pct(evaluation)
    payload = {
        "id": row["id"],
        "model": model,
        "model_slug": slugify_model(model),
        "class": row["class"],
        "difficulty": row["difficulty"],
        "seed": row["seed"],
        "gold_objective": row["gold_objective"],
        "baseline_objective": row["baseline_objective"],
        "value_cap": row["value_cap"],
        "baseline": row["instance"].get("baseline_submission"),
        **result,
        "feasible": infer_feasible(evaluation),
        "final_submission_source": submission_source,
        "final_evaluation": evaluation,
        "parse_path": infer_parse_path(result),
        "gap_pct": final_gap_pct,
    }
    return payload


def build_error_payload(model: str, row: dict[str, Any], exc: Exception) -> dict[str, Any]:
    failure = f"{type(exc).__name__}: {exc}"
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
        "baseline": row["instance"].get("baseline_submission"),
        "score": 0.0,
        "score_at_stop": 0.0,
        "score_after_cf": 0.0,
        "cf_delta": 0.0,
        "wall_s": 0.0,
        "n_exec_turns": 0,
        "stop_reason": "error",
        "transcript": [],
        "parsed": {},
        "cf_parsed": {},
        "parse_events": [],
        "error": failure,
        "feasible": False,
        "final_submission_source": "error",
        "final_evaluation": {
            "mode": "error",
            "gap_pct": None,
            "feasible": False,
            "details": {"failure_reason": failure},
            "submission": None,
        },
        "parse_path": "not_run",
        "gap_pct": None,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_existing_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def summarize_concern(payload: dict[str, Any]) -> tuple[str, str, str, str]:
    parse_path = str(payload.get("parse_path") or "unknown")
    error = str(payload.get("error") or "-")
    feasible = bool(payload.get("feasible"))
    gap_pct = payload.get("gap_pct")
    score = float(payload.get("score", 0.0))
    baseline_objective = payload.get("baseline_objective")
    details = payload.get("final_evaluation", {}).get("details", {})
    verified_objective = details.get("verified_objective", details.get("verified_makespan"))
    transcript = payload.get("transcript") or []
    turns = len(transcript)

    parse_line = f"{payload['model']}: parse_path={parse_path}; error={error}; exec_turns={payload.get('n_exec_turns', 0)}"
    feasibility_line = (
        f"{payload['model']}: feasible={feasible}; verified_objective={verified_objective}; "
        f"stop_reason={payload.get('stop_reason')}"
    )
    score_line = (
        f"{payload['model']}: score={score:.2f}; gap_pct={gap_pct}; "
        f"baseline_objective={baseline_objective}; final_submission_source={payload.get('final_submission_source')}"
    )

    coherence_note = "coherent multi-turn transcript"
    if turns == 0:
        coherence_note = "no transcript captured"
    elif error != "-" and "parse" in error.lower():
        coherence_note = "transcript ended in parse failure"
    elif error != "-" and "timed out" in error.lower():
        coherence_note = "transcript ended in timeout"
    transcript_line = f"{payload['model']}: transcript_turns={turns}; {coherence_note}"
    return parse_line, feasibility_line, score_line, transcript_line


def write_concerns(question_dir: Path, question_id: str, payloads: list[dict[str, Any]], notes: list[str]) -> None:
    parse_lines: list[str] = []
    feasibility_lines: list[str] = []
    score_lines: list[str] = []
    transcript_lines: list[str] = []
    for payload in payloads:
        parse_line, feasibility_line, score_line, transcript_line = summarize_concern(payload)
        parse_lines.append(f"- {parse_line}")
        feasibility_lines.append(f"- {feasibility_line}")
        score_lines.append(f"- {score_line}")
        transcript_lines.append(f"- {transcript_line}")

    content = [
        f"# Concerns for {question_id}",
        "",
        "## Parse",
        *parse_lines,
        "",
        "## Feasibility",
        *feasibility_lines,
        "",
        "## Score-vs-baseline",
        *score_lines,
        "",
        "## Transcript coherence",
        *transcript_lines,
        "",
        "## Suggested fixes",
    ]
    if notes:
        content.extend(f"- {note}" for note in notes)
    else:
        content.append("- No additional concerns beyond the bucketed observations above.")

    (question_dir / "concerns.md").write_text("\n".join(content) + "\n", encoding="utf-8")


def record_model_summary(model_summary: dict[str, Any], question_id: str, payload: dict[str, Any]) -> None:
    if payload.get("skipped"):
        model_summary["skipped"] += 1
        return

    model_summary["completed"] += 1
    if payload.get("feasible"):
        model_summary["feasible"] += 1
    parse_path = str(payload.get("parse_path") or "unknown")
    if parse_path in {"strict_protocol", "strict_protocol_cf"}:
        model_summary["strict_like"] += 1
    elif parse_path == "partial_rescue":
        model_summary["partial_rescue"] += 1
    elif parse_path == "judge_rescue":
        model_summary["judge_rescue"] += 1
    elif parse_path == "strict_parse_failed":
        model_summary["strict_parse_failed"] += 1
    elif parse_path == "baseline_only":
        model_summary["baseline_only"] += 1
    if payload.get("error"):
        model_summary["errors"].append(
            {
                "question_id": question_id,
                "error": payload["error"],
                "stop_reason": payload.get("stop_reason"),
            }
        )


def main() -> int:
    rows_by_id = load_rows(PARTIAL_PATH)
    missing = [question_id for question_id in QUESTION_IDS if question_id not in rows_by_id]
    if missing:
        raise SystemExit(f"missing rows in partial file: {', '.join(missing)}")

    summary: dict[str, Any] = {"question_ids": list(QUESTION_IDS), "models": {}, "questions": {}}
    model_skip_remaining: dict[str, bool] = {model: False for model in MODELS}
    model_first_two_api_errors: dict[str, list[bool]] = {model: [] for model in MODELS}

    for question_index, question_id in enumerate(QUESTION_IDS):
        row = rows_by_id[question_id]
        question_dir = RESULTS_ROOT / question_id
        question_dir.mkdir(parents=True, exist_ok=True)
        write_json(question_dir / "question.json", row)

        question_payloads: list[dict[str, Any]] = []
        question_notes: list[str] = []

        for model in MODELS:
            model_summary = summary["models"].setdefault(
                model,
                {
                    "attempted": 0,
                    "completed": 0,
                    "feasible": 0,
                    "strict_like": 0,
                    "partial_rescue": 0,
                    "judge_rescue": 0,
                    "strict_parse_failed": 0,
                    "baseline_only": 0,
                    "skipped": 0,
                    "errors": [],
                },
            )
            output_path = question_dir / f"{model}.json"
            existing_payload = load_existing_json(output_path)

            if existing_payload is not None and existing_payload.get("model") == model:
                print(f"[resume] {question_id} / {model}", flush=True)
                question_payloads.append(existing_payload)
                record_model_summary(model_summary, question_id, existing_payload)
                if question_index < 2:
                    model_first_two_api_errors[model].append(is_api_error(str(existing_payload.get("error") or "")))
                    if len(model_first_two_api_errors[model]) == 2 and all(model_first_two_api_errors[model]):
                        model_skip_remaining[model] = True
                continue

            if model_skip_remaining[model]:
                payload = {
                    "id": question_id,
                    "model": model,
                    "skipped": True,
                    "skip_reason": "model skipped after API errors on the first two rows",
                }
                write_json(output_path, payload)
                question_payloads.append(payload)
                record_model_summary(model_summary, question_id, payload)
                question_notes.append(f"{model}: skipped after API errors on the first two rows.")
                continue

            payload: dict[str, Any] | None = None
            last_timeout_payload: dict[str, Any] | None = None
            for attempt in range(1, MAX_ATTEMPTS + 1):
                model_summary["attempted"] += 1
                print(f"[run] {question_id} / {model} attempt {attempt}", flush=True)
                try:
                    candidate = build_payload(model, row)
                except Exception as exc:  # noqa: BLE001
                    candidate = build_error_payload(model, row, exc)
                candidate["attempt"] = attempt
                candidate["max_attempts"] = MAX_ATTEMPTS
                if is_timeout_payload(candidate) and attempt < MAX_ATTEMPTS:
                    last_timeout_payload = candidate
                    question_notes.append(
                        f"{model}: attempt {attempt} hit timeout semantics on {question_id}; retrying."
                    )
                    print(f"[retry] {question_id} / {model} after timeout-like error", flush=True)
                    continue
                payload = candidate
                print(
                    f"[done] {question_id} / {model}: parse={payload.get('parse_path')} "
                    f"feasible={payload.get('feasible')} stop={payload.get('stop_reason')} "
                    f"error={payload.get('error')}",
                    flush=True,
                )
                break

            if payload is None:
                payload = dict(last_timeout_payload or {})
                payload["skipped"] = True
                payload["skip_reason"] = "row/model skipped after 3 timeout-like attempts"
                question_notes.append(f"{model}: skipped on {question_id} after 3 timeout-like attempts.")

            if question_index < 2:
                model_first_two_api_errors[model].append(is_api_error(str(payload.get("error") or "")))
                if len(model_first_two_api_errors[model]) == 2 and all(model_first_two_api_errors[model]):
                    model_skip_remaining[model] = True
                    question_notes.append(f"{model}: API errored on both initial rows; remaining rows will be skipped.")

            write_json(output_path, payload)
            question_payloads.append(payload)
            record_model_summary(model_summary, question_id, payload)

        write_concerns(question_dir, question_id, question_payloads, question_notes)
        print(f"[question-done] {question_id}", flush=True)
        summary["questions"][question_id] = {
            "models": {
                payload["model"]: {
                    "parse_path": payload.get("parse_path"),
                    "feasible": payload.get("feasible"),
                    "score": payload.get("score"),
                    "gap_pct": payload.get("gap_pct"),
                    "stop_reason": payload.get("stop_reason"),
                    "error": payload.get("error"),
                    "skipped": payload.get("skipped", False),
                }
                for payload in question_payloads
            }
        }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
