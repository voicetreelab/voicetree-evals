#!/usr/bin/env python3
"""Dev-time (class, difficulty, seed) validator CLI.

Runs the full forward pipeline on one instance so Factory-A Codex workers can
prove each (class, difficulty, seed) is well-posed before scaling to 210 rows:

    generator -> render_nl -> Gemini 2.5 Flash -> parse BEST_GUESS ->
    verifier(instance, submission) -> (gap_pct, feasible, details) ->
    print PASS/FAIL + score + wall.

The transcript is saved to `tests/fixtures/{class}_{difficulty}_seed{seed}.txt`
for later inspection.

Example:
    python metabench/kaggle_submission/scripts/verify_pipeline.py \
        --class cjs --difficulty medium --seed 1

Requires GOOGLE_API_KEY or GEMINI_API_KEY in the environment, or a readable
`.env` file at one of:
  - $HOME/.gemini/.env
  - <repo>/hch/metagame/.env
  - <kaggle_submission>/.env
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
KAGGLE_ROOT = SCRIPT_DIR.parent
if str(KAGGLE_ROOT) not in sys.path:
    sys.path.insert(0, str(KAGGLE_ROOT))

from generators import CLASS_TO_GENERATOR  # noqa: E402
from harness.protocol import _parse_object_loose, parse_best_guess  # noqa: E402
from harness.render_nl import render_nl  # noqa: E402
from verifiers import CLASS_TO_BEST_GUESS_SCHEMA, CLASS_TO_VERIFIER  # noqa: E402

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TIME_PENALTY = 0.01
DOTENV_CANDIDATES = (
    Path.home() / ".gemini" / ".env",
    KAGGLE_ROOT.parent / "hch" / "metagame" / ".env",
    KAGGLE_ROOT / ".env",
)


def load_api_key() -> str:
    from dotenv import load_dotenv

    for path in DOTENV_CANDIDATES:
        if path.exists():
            load_dotenv(path, override=False)
            break
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "Missing GOOGLE_API_KEY or GEMINI_API_KEY. Set env or create a .env "
            f"at one of: {[str(p) for p in DOTENV_CANDIDATES]}"
        )
    return key


def build_system_prompt() -> str:
    return (
        "You are solving a single optimization problem. Each problem is worth "
        "up to 100 points; your gap to the optimum reduces value linearly (1 "
        "point per percent of gap, floored at 0). Do not call tools. Do not "
        "write code, pseudocode, or solver sketches. Reason only from the "
        "prompt. At the end of your response, emit exactly one labelled line "
        "named BEST_GUESS whose value is a valid JSON object matching the "
        "schema shown in the user message. No other labelled fields are "
        "required for this validator run."
    )


def build_user_prompt(cls: str, instance_nl: str, schema: str | None) -> str:
    schema_block = ""
    if schema:
        schema_block = (
            f"\n\nBEST_GUESS JSON schema for `{cls}`:\n"
            f"```json\n{schema}\n```"
        )
    return (
        "OUTPUT CONTRACT (read this first):\n"
        "Your final response MUST end with a single line that begins with the "
        "literal token `BEST_GUESS:` followed by a valid JSON object matching "
        "the schema below. The label is mandatory — do not omit it. Do not wrap "
        "the JSON in markdown code fences. Do not emit any other labelled "
        "fields (no PLAN_STATE, no DECISION, no NEXT_SUB). Free-form reasoning "
        "before the BEST_GUESS line is fine.\n\n"
        "Example shape (pseudocode):\n"
        "    ... your reasoning ...\n"
        "    BEST_GUESS: {\"key\": ...}\n\n"
        f"PROBLEM:\n{instance_nl}"
        f"{schema_block}\n\n"
        "Emit `BEST_GUESS: {...}` as the last non-empty line of your reply. "
        "The JSON must be valid and complete."
    )


def call_gemini(
    *,
    model: str,
    system: str,
    user: str,
    api_key: str,
    timeout_s: float,
    thinking_budget: int | None,
) -> tuple[str, float, dict[str, Any]]:
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions.model_construct(
            timeout=int((timeout_s + 5.0) * 1000)
        ),
    )
    config_kwargs: dict[str, Any] = {
        "system_instruction": system,
        "temperature": 0.0,
    }
    if thinking_budget is not None:
        config_kwargs["thinking_config"] = types.ThinkingConfig(
            thinking_budget=thinking_budget
        )
    config = types.GenerateContentConfig(**config_kwargs)
    t0 = time.monotonic()
    response = client.models.generate_content(
        model=model,
        contents=user,
        config=config,
    )
    wall = time.monotonic() - t0
    text = (response.text or "").strip()
    usage = getattr(response, "usage_metadata", None)
    meta = {
        "input_tokens": getattr(usage, "prompt_token_count", None),
        "output_tokens": getattr(usage, "candidates_token_count", None),
        "total_tokens": getattr(usage, "total_token_count", None),
        "thinking_tokens": getattr(usage, "thoughts_token_count", None),
    }
    return text, wall, meta


def compute_score(
    gap_pct: float,
    wall_s: float,
    time_penalty: float = DEFAULT_TIME_PENALTY,
) -> float:
    return max(0.0, 100.0 - gap_pct) - time_penalty * wall_s


def _fallback_last_json_object(text: str) -> dict[str, Any] | None:
    """Find the last balanced top-level {...} in the raw text and parse it.

    Used when the model emits valid JSON but forgets the BEST_GUESS label.
    Handles JSON inside ```json ... ``` fences as well.
    """
    candidates: list[str] = []
    depth = 0
    start: int | None = None
    for index, char in enumerate(text):
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    candidates.append(text[start : index + 1])
                    start = None
    for chunk in reversed(candidates):
        parsed = _parse_object_loose(chunk)
        if isinstance(parsed, dict):
            return parsed
    return None


def summarize_instance_refs(instance: dict[str, Any]) -> str:
    keys = (
        "gold_objective",
        "baseline_objective",
        "optimal_length",
        "baseline_length",
        "baseline_gap_pct",
    )
    bits = [f"{k}={instance[k]}" for k in keys if k in instance]
    return ", ".join(bits) if bits else "(no baseline/gold keys surfaced)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="verify_pipeline",
        description=(
            "Dev-time validator: generate instance -> Gemini 2.5 Flash -> parse "
            "BEST_GUESS -> verify -> print PASS/FAIL + score. Used by Factory-A "
            "Codex agents to confirm each (class, difficulty, seed) is well-posed."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Registered classes (from generators/): "
            + ", ".join(sorted(CLASS_TO_GENERATOR))
            + "\nClasses with verifier: "
            + ", ".join(sorted(CLASS_TO_VERIFIER))
        ),
    )
    parser.add_argument(
        "--class",
        dest="cls",
        required=True,
        choices=sorted(CLASS_TO_GENERATOR),
        help="Problem class (from generators registry).",
    )
    parser.add_argument(
        "--difficulty",
        default="medium",
        help="Difficulty level understood by the generator (default: medium).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Instance seed (default: 1).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Gemini model id (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=120.0,
        help="LLM call timeout in seconds (default: 120).",
    )
    parser.add_argument(
        "--thinking-budget",
        type=int,
        default=0,
        help=(
            "Gemini thinking token budget. 0 = no thinking (fast, cheap, good "
            "enough for parseability). Use -1 for unconstrained / model default. "
            "Default: 0."
        ),
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=KAGGLE_ROOT / "tests" / "fixtures",
        help="Where to write the transcript fixture.",
    )
    parser.add_argument(
        "--no-fixture",
        action="store_true",
        help="Skip writing the transcript fixture.",
    )
    parser.add_argument(
        "--print-submission",
        action="store_true",
        help="Print parsed BEST_GUESS JSON after the verdict.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.cls not in CLASS_TO_VERIFIER:
        print(f"[FAIL] No verifier registered for class {args.cls!r}")
        return 2

    print(f"[gen ] class={args.cls} difficulty={args.difficulty} seed={args.seed}")
    t_gen = time.monotonic()
    try:
        instance = CLASS_TO_GENERATOR[args.cls](args.seed, args.difficulty)
    except Exception as exc:
        print(f"[FAIL] generator raised: {exc!r}")
        return 1
    gen_wall = time.monotonic() - t_gen
    print(f"       generated in {gen_wall:.1f}s ({summarize_instance_refs(instance)})")

    instance_nl = render_nl(instance, args.cls)
    schema = CLASS_TO_BEST_GUESS_SCHEMA.get(args.cls)
    system = build_system_prompt()
    user = build_user_prompt(args.cls, instance_nl, schema)

    print(f"[llm ] {args.model} calling (timeout={args.timeout_s:.0f}s)...")
    try:
        api_key = load_api_key()
        raw, llm_wall, meta = call_gemini(
            model=args.model,
            system=system,
            user=user,
            api_key=api_key,
            timeout_s=args.timeout_s,
            thinking_budget=(None if args.thinking_budget < 0 else args.thinking_budget),
        )
    except Exception as exc:
        print(f"[FAIL] LLM call failed: {exc!r}")
        return 1
    print(
        f"       llm_wall={llm_wall:.1f}s out_chars={len(raw)} "
        f"in_tok={meta.get('input_tokens')} out_tok={meta.get('output_tokens')}"
    )

    submission = parse_best_guess(raw)
    parse_method = "labelled"
    if submission is None:
        submission = _fallback_last_json_object(raw)
        if submission is not None:
            parse_method = "fallback_last_json"
            print("[warn] BEST_GUESS label missing; used last top-level JSON object as fallback")
    if submission is None:
        print("[FAIL] Could not parse BEST_GUESS or any JSON object from model output.")
        _write_fixture(
            args,
            instance=instance,
            raw=raw,
            verdict="parse_fail",
            submission=None,
            details=None,
            llm_wall=llm_wall,
            score=None,
            gap_pct=None,
            feasible=False,
        )
        return 1

    verify_fn = CLASS_TO_VERIFIER[args.cls]
    try:
        gap_pct, feasible, details = verify_fn(instance, submission)
    except Exception as exc:
        print(f"[FAIL] verifier raised: {exc!r}")
        _write_fixture(
            args,
            instance=instance,
            raw=raw,
            verdict="verifier_exception",
            submission=submission,
            details={"exception": repr(exc)},
            llm_wall=llm_wall,
            score=None,
            gap_pct=None,
            feasible=False,
        )
        return 1

    score = compute_score(gap_pct, llm_wall)
    verdict = "PASS" if feasible else "FAIL"
    print(
        f"[vrfy] {verdict} score={score:.2f} feasible={feasible} "
        f"gap_pct={gap_pct:.2f} wall={llm_wall:.1f}s parse={parse_method}"
    )
    if not feasible and isinstance(details, dict):
        print(f"       failure_reason={details.get('failure_reason')}")
    if args.print_submission:
        print("[sub ] " + json.dumps(submission, indent=2, sort_keys=True, default=str))

    _write_fixture(
        args,
        instance=instance,
        raw=raw,
        verdict=verdict,
        submission=submission,
        details=details,
        llm_wall=llm_wall,
        score=score,
        gap_pct=gap_pct,
        feasible=feasible,
    )
    return 0 if feasible else 1


def _write_fixture(
    args: argparse.Namespace,
    *,
    instance: dict[str, Any],
    raw: str,
    verdict: str,
    submission: dict[str, Any] | None,
    details: dict[str, Any] | None,
    llm_wall: float,
    score: float | None,
    gap_pct: float | None,
    feasible: bool,
) -> None:
    if args.no_fixture:
        return
    args.fixtures_dir.mkdir(parents=True, exist_ok=True)
    path = args.fixtures_dir / f"{args.cls}_{args.difficulty}_seed{args.seed}.txt"

    instance_keys_to_dump = {
        k: v for k, v in instance.items() if k != "problem_statement"
    }
    lines = [
        f"class: {args.cls}",
        f"difficulty: {args.difficulty}",
        f"seed: {args.seed}",
        f"model: {args.model}",
        f"verdict: {verdict}",
        f"feasible: {feasible}",
        f"score: {score}",
        f"gap_pct: {gap_pct}",
        f"llm_wall_s: {llm_wall:.3f}",
        "",
        "--- instance (problem_statement omitted) ---",
        json.dumps(instance_keys_to_dump, indent=2, sort_keys=True, default=str),
        "",
        "--- raw model output ---",
        raw,
        "",
        "--- parsed submission ---",
        (
            json.dumps(submission, indent=2, sort_keys=True, default=str)
            if submission is not None
            else "<unparseable>"
        ),
        "",
        "--- verifier details ---",
        (
            json.dumps(details, indent=2, sort_keys=True, default=str)
            if details is not None
            else "<no details>"
        ),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[fix ] wrote {path}")


if __name__ == "__main__":
    sys.exit(main())
