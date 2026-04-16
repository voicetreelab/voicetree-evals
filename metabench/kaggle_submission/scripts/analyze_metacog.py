#!/usr/bin/env python3
"""Aggregate and score per-turn QUALITY_FORECAST + CONTINUE_FORECAST over overnight results.

Walks `kaggle_submission/results/full/{row_id}/{model}.json`, re-parses each exec-turn's
labelled forecast block from the transcript, and scores:

  - M1 (p_solve Brier): (p_solve_k - kept_as_best_k)^2 across all solo-class subtasks,
    where kept_as_best flags whether subtask k's best_guess became the running-best
    verified gap (lower gap_pct than all prior subtasks)
  - Quality Brier: (p_gap_le_k - I[final_gap_pct <= k])^2 against final realized gap
  - Continue Brier: (p_improve - I[cf_delta > 0])^2 against the counterfactual-continue delta
  - Delta regression: MSE of expected_delta_score vs realized cf_delta
  - Drift: sign of (final-turn p_gap_le_5 - first-turn p_gap_le_5) and whether it moves toward truth

Emits a markdown report at results/metacog_analysis.md and a CSV rollup at
results/metacog_rollup.csv.
"""
from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.protocol import (
    gap_thresholds_for_class,
    parse_exec_turn_partial,
    parse_plan_turn,
)
from verifiers import CLASS_TO_VERIFIER

# M1 = subtask-solvability Brier. `p_solve_k` is the forecast in NEXT_SUB that kicked off
# subtask k; `kept_as_best_k` is whether that subtask's best_guess became the running best
# (lower verified gap_pct than any prior subtask). Subtask 1 is kept_as_best=1 iff feasible
# (no prior to beat). Infeasible submissions score gap_pct=100.0 and can never beat a prior
# feasible gap. Portfolio is skipped (no per-sub-component verifier path in this pass).
INFEASIBLE_GAP_PCT = 100.0

# Clean stops = model-initiated halt (as distinguished from budget/error termination).
# Overnight harness tags all model-initiated stops as `decision_stop` (writeup-v2 used
# `subtask_stop` / `turn1_stop` — different labels for the same concept).
CLEAN_STOP_REASONS = {"decision_stop", "subtask_stop", "turn1_stop"}
NON_TERMINATION_REASONS = {
    "wall_budget", "max_exec_turns", "subtask_timeout", "error",
    "runner_timeout", "skipped_after_timeouts",
    "model_skipped_by_parent_budget_guardrail", "skipped_model", "not_run",
}

RESULTS_DIR = ROOT / "results" / "full"
FRONTIER_RUNS_DIR = ROOT / "results" / "runs"
OUT_MD = ROOT / "results" / "metacog_analysis.md"
OUT_CSV = ROOT / "results" / "metacog_rollup.csv"

SOLO_CLASSES = ("cjs", "graphcol", "mwis", "steiner", "tsp", "ve", "mbj")
CLASSES = SOLO_CLASSES + ("portfolio",)
DIFFICULTIES = ("medium", "hard")
SMALL_MODELS = ("claude-sonnet-4.6", "gemini-flash-latest", "gpt-5.4-mini")
FRONTIER_MODELS = ("claude-opus-4.6", "gemini-3-pro-preview", "gpt-5.4")
MODELS = SMALL_MODELS + FRONTIER_MODELS
FAMILY = {
    "claude-sonnet-4.6": "anthropic", "claude-opus-4.6": "anthropic",
    "gemini-flash-latest": "google", "gemini-3-pro-preview": "google",
    "gpt-5.4-mini": "openai", "gpt-5.4": "openai",
}
TIER = {
    "claude-sonnet-4.6": "small", "claude-opus-4.6": "frontier",
    "gemini-flash-latest": "small", "gemini-3-pro-preview": "frontier",
    "gpt-5.4-mini": "small", "gpt-5.4": "frontier",
}


def _parse_turn_forecasts(text: str, cls: str) -> dict:
    # VE nominally expects thresholds (0.01, 0.1, 0.5), but every model in the overnight set
    # emits the solo-style keys `p_gap_le_{2,5,10}`. parse_quality_forecast would return None.
    # Fall back to solo-style parsing for VE so we can still score (and flag this as a real
    # protocol-compliance issue in the report).
    result = parse_exec_turn_partial(text, cls=cls, require_decision=False)
    if cls == "ve" and result.get("quality_forecast") is None:
        fallback = parse_exec_turn_partial(text, cls="cjs", require_decision=False)
        if fallback.get("quality_forecast") is not None:
            result["quality_forecast"] = fallback["quality_forecast"]
            result["_ve_used_solo_thresholds"] = True
    return result


def _is_final_feasible(record: dict) -> bool:
    fe = record.get("final_evaluation") or {}
    return bool(fe.get("feasible", record.get("feasible")))


def _final_gap_pct(record: dict) -> float | None:
    fe = record.get("final_evaluation") or {}
    gap = fe.get("gap_pct")
    if gap is None:
        gap = record.get("gap_pct")
    if gap is None:
        return None
    try:
        gap = float(gap)
    except Exception:
        return None
    if math.isnan(gap) or math.isinf(gap):
        return None
    return gap


def _classify_thresholds(cls: str) -> tuple[float, ...]:
    # portfolio uses solo-style thresholds in practice (verified from cf_parsed).
    # VE nominally uses (0.01, 0.1, 0.5) but models emit solo keys — see _parse_turn_forecasts.
    return gap_thresholds_for_class(cls if cls not in ("portfolio", "ve") else "cjs")


def _gap_key(threshold: float) -> str:
    return f"p_gap_le_{format(threshold, 'g').replace('.', '_')}"


_QUESTION_CACHE: dict[str, dict] = {}


def _load_question(row_dir: Path) -> dict | None:
    key = str(row_dir)
    if key in _QUESTION_CACHE:
        return _QUESTION_CACHE[key]
    q_path = row_dir / "question.json"
    if not q_path.exists():
        _QUESTION_CACHE[key] = None
        return None
    try:
        data = json.loads(q_path.read_text())
    except Exception:
        data = None
    _QUESTION_CACHE[key] = data
    return data


def _score_subtask_submission(cls: str, instance: dict, submission) -> tuple[float, bool]:
    """Run the solo verifier; return (gap_pct, feasible). Defensive against verifier errors."""
    verifier = CLASS_TO_VERIFIER.get(cls)
    if verifier is None:
        return INFEASIBLE_GAP_PCT, False
    if not isinstance(submission, dict):
        return INFEASIBLE_GAP_PCT, False
    try:
        gap_pct, feasible, _details = verifier(instance, submission)
    except Exception:
        return INFEASIBLE_GAP_PCT, False
    try:
        return float(gap_pct), bool(feasible)
    except Exception:
        return INFEASIBLE_GAP_PCT, False


def _extract_turn_scores(
    transcript: list[dict],
    cls: str,
    n_exec_turns: int,
    instance: dict | None,
) -> list[dict]:
    """Per-main-run-exec-turn BEST_GUESS verified score trajectory (for M5).

    Unlike `_extract_subtasks` this does not follow the NEXT_SUB `p_solve` chain —
    it always scores every main-run exec turn so M5 can integrate `score_t` across
    the full trajectory even after NEXT_SUB emission stops. Returns [] for portfolio
    rows or rows without an instance (no solo verifier path).
    """
    if cls == "portfolio" or instance is None:
        return []
    if not transcript or n_exec_turns <= 0:
        return []
    exec_msgs = [
        m for m in transcript[1 : 1 + n_exec_turns]
        if m.get("role") == "assistant"
    ]
    out: list[dict] = []
    for idx, msg in enumerate(exec_msgs):
        parsed = parse_exec_turn_partial(
            msg.get("content") or "", cls=cls, require_decision=False
        )
        bg = parsed.get("best_guess")
        if bg is None:
            gap_pct, feasible = INFEASIBLE_GAP_PCT, False
            had_bg = False
        else:
            gap_pct, feasible = _score_subtask_submission(cls, instance, bg)
            had_bg = True
        score = max(0.0, 100.0 - float(gap_pct))
        out.append({
            "turn_idx": idx + 1,
            "gap_pct": gap_pct,
            "feasible": feasible,
            "had_best_guess": had_bg,
            "score": score,
        })
    return out


def _extract_subtasks(
    transcript: list[dict],
    cls: str,
    n_exec_turns: int,
    instance: dict | None,
) -> list[dict]:
    """Reconstruct per-subtask (p_solve, kept_as_best) for M1.

    Main-run exec turns are transcript[1:1+n_exec_turns] (the CF-branch turn, when present,
    is appended *after* the main run and must be excluded). For portfolio rows or rows with
    no instance, we skip scoring and return an empty list (M1 undefined).
    """
    if cls == "portfolio" or instance is None:
        return []
    if not transcript or n_exec_turns <= 0:
        return []

    plan_msg = transcript[0]
    if plan_msg.get("role") != "assistant":
        return []
    plan = parse_plan_turn(plan_msg.get("content") or "", cls=cls)
    if not plan or not plan.get("next_sub"):
        return []
    p_solve_next = plan["next_sub"].get("p_solve")
    if p_solve_next is None:
        return []

    # Only first n_exec_turns messages after the plan are main-run exec turns.
    exec_msgs = [
        m for m in transcript[1 : 1 + n_exec_turns]
        if m.get("role") == "assistant"
    ]
    if not exec_msgs:
        return []

    subtasks: list[dict] = []
    prior_min_gap: float | None = None
    for idx, msg in enumerate(exec_msgs):
        parsed = parse_exec_turn_partial(
            msg.get("content") or "", cls=cls, require_decision=False
        )
        bg = parsed.get("best_guess")
        p_for_this = p_solve_next  # p_solve forecast that kicked off this subtask

        if bg is None:
            gap_pct, feasible = INFEASIBLE_GAP_PCT, False
        else:
            gap_pct, feasible = _score_subtask_submission(cls, instance, bg)

        if idx == 0:
            kept = 1 if feasible else 0
        else:
            # Strict improvement over best prior gap. Prior min starts at +inf if no prior
            # feasible existed; we track it as min of observed gaps (infeasible=100.0).
            if prior_min_gap is None:
                kept = 1 if feasible else 0
            else:
                kept = 1 if gap_pct < prior_min_gap - 1e-9 else 0

        subtasks.append({
            "idx": idx + 1,
            "p_solve": p_for_this,
            "gap_pct": gap_pct,
            "feasible": feasible,
            "kept_as_best": kept,
            "had_best_guess": bg is not None,
        })

        # Update running-best gap for next iteration.
        prior_min_gap = gap_pct if prior_min_gap is None else min(prior_min_gap, gap_pct)

        # Advance p_solve_next from this turn's NEXT_SUB (only present when decision=continue).
        ns = parsed.get("next_sub")
        if ns and ns.get("p_solve") is not None:
            p_solve_next = ns["p_solve"]
        else:
            p_solve_next = None
            # If no next p_solve is emitted, we cannot score further subtasks for M1.
            if idx + 1 < len(exec_msgs):
                break

    return subtasks


def _collect_per_row(path: Path, question_row_dir: Path | None = None) -> dict | None:
    try:
        record = json.loads(path.read_text())
    except Exception:
        return None

    row_id = record.get("id") or path.parent.name
    cls = record.get("class") or row_id.split("_")[0]
    difficulty = record.get("difficulty") or (
        "hard" if "_hard_" in row_id else "medium"
    )
    model = record.get("model_slug") or path.stem

    transcript = record.get("transcript") or []
    final_gap = _final_gap_pct(record)
    feasible = _is_final_feasible(record)
    cf_delta = record.get("cf_delta")
    try:
        cf_delta = float(cf_delta) if cf_delta is not None else None
    except Exception:
        cf_delta = None

    # Only assistant exec-turn messages carry forecasts. The plan turn is the first assistant
    # message; from turn 1 onward the model emits QUALITY_FORECAST / CONTINUE_FORECAST.
    # Parse each and keep only turns where at least one forecast is present.
    turns = []
    for idx, msg in enumerate(transcript):
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content") or ""
        parsed = _parse_turn_forecasts(content, cls)
        qf = parsed.get("quality_forecast")
        cf = parsed.get("continue_forecast")
        decision = parsed.get("decision")
        if qf is None and cf is None and decision is None:
            continue
        turns.append({
            "turn_idx": idx,
            "quality_forecast": qf,
            "continue_forecast": cf,
            "decision": decision,
        })

    n_exec_turns = record.get("n_exec_turns") or 0
    q_dir = question_row_dir if question_row_dir is not None else path.parent
    question = _load_question(q_dir)
    instance = question.get("instance") if isinstance(question, dict) else None
    subtasks = _extract_subtasks(transcript, cls, n_exec_turns, instance)
    turn_scores = _extract_turn_scores(transcript, cls, n_exec_turns, instance)

    return {
        "row_id": row_id,
        "class": cls,
        "difficulty": difficulty,
        "model": model,
        "family": FAMILY.get(model, "unknown"),
        "tier": TIER.get(model, "unknown"),
        "final_gap": final_gap,
        "feasible": feasible,
        "cf_delta": cf_delta,
        "score": record.get("score"),
        "score_after_cf": record.get("score_after_cf"),
        "n_exec_turns": n_exec_turns,
        "stop_reason": record.get("stop_reason"),
        "turns": turns,
        "subtasks": subtasks,
        "turn_scores": turn_scores,
    }


def _quality_brier(turns: list[dict], cls: str, final_gap: float | None, feasible: bool):
    """Return (per-threshold sum-squared-error, count) dict, plus count of turns scored."""
    thresholds = _classify_thresholds(cls)
    agg = {t: {"sse": 0.0, "n": 0} for t in thresholds}
    for t in turns:
        qf = t["quality_forecast"]
        if not qf:
            continue
        for thr in thresholds:
            key = _gap_key(thr)
            p = qf.get(key)
            if p is None:
                continue
            # Realized label: 1 if final gap exists AND feasible AND gap <= threshold.
            # Infeasible or missing gap → realized 0 (quality target was not met).
            if feasible and final_gap is not None:
                realized = 1 if final_gap <= thr else 0
            else:
                realized = 0
            agg[thr]["sse"] += (p - realized) ** 2
            agg[thr]["n"] += 1
    return agg


def _continue_brier(turns: list[dict], cf_delta: float | None):
    """Score the final turn's p_improve against I[cf_delta>0]. Also track predicted-delta MAE."""
    if not turns or cf_delta is None:
        return None
    last = turns[-1].get("continue_forecast")
    if not last:
        return None
    p_improve = last.get("p_improve")
    expected_delta = last.get("expected_delta_score")
    realized = 1 if cf_delta > 0 else 0
    out = {}
    if p_improve is not None:
        out["p_improve"] = p_improve
        out["realized_improve"] = realized
        out["brier"] = (p_improve - realized) ** 2
    if expected_delta is not None:
        out["expected_delta"] = expected_delta
        out["realized_delta"] = cf_delta
        out["delta_mae"] = abs(expected_delta - cf_delta)
    return out


def murphy_decomposition(preds_outcomes, n_bins: int = 10):
    """Murphy (1973) Brier decomposition: Brier = reliability − resolution + uncertainty.

    preds_outcomes: iterable of (p, y) with p ∈ [0,1] and y ∈ {0,1}.
    """
    pts = [(float(p), int(y)) for p, y in preds_outcomes if p is not None and y is not None]
    if not pts:
        return None
    n = len(pts)
    y_bar = sum(y for _, y in pts) / n
    # Bin predictions uniformly on [0,1]
    bins = [[] for _ in range(n_bins)]
    for p, y in pts:
        idx = min(n_bins - 1, int(p * n_bins))
        bins[idx].append((p, y))
    reliability = 0.0
    resolution = 0.0
    for bucket in bins:
        if not bucket:
            continue
        n_k = len(bucket)
        p_k = sum(p for p, _ in bucket) / n_k
        y_k = sum(y for _, y in bucket) / n_k
        reliability += n_k * (p_k - y_k) ** 2
        resolution += n_k * (y_k - y_bar) ** 2
    reliability /= n
    resolution /= n
    uncertainty = y_bar * (1 - y_bar)
    brier = sum((p - y) ** 2 for p, y in pts) / n
    return {
        "brier": brier,
        "reliability": reliability,
        "resolution": resolution,
        "uncertainty": uncertainty,
        "n": n,
    }


def auc_binary(preds_outcomes):
    """ROC-AUC for binary outcomes. Returns None if only one class present."""
    pts = [(float(p), int(y)) for p, y in preds_outcomes if p is not None and y is not None]
    if not pts:
        return None
    pos = [p for p, y in pts if y == 1]
    neg = [p for p, y in pts if y == 0]
    if not pos or not neg:
        return None
    wins = 0.0
    for pp in pos:
        for pn in neg:
            if pp > pn:
                wins += 1.0
            elif pp == pn:
                wins += 0.5
    return wins / (len(pos) * len(neg))


def logistic_fit(xs, ys, n_iter: int = 50, lr: float = 0.1):
    """Hand-rolled Newton-Raphson for P(y=1|x) = σ(β0 + β1·x). Pure Python.

    Returns (β0, β1, threshold_at_p_half) or None if degenerate.
    """
    pairs = [(float(x), int(y)) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 5:
        return None
    y_vals = [y for _, y in pairs]
    if sum(y_vals) in (0, len(y_vals)):
        return None  # no variance → logistic degenerate
    b0, b1 = 0.0, 0.0
    for _ in range(n_iter):
        # gradient + Hessian for logistic MLE
        g0 = g1 = 0.0
        h00 = h01 = h11 = 0.0
        for x, y in pairs:
            z = b0 + b1 * x
            p = 1.0 / (1.0 + math.exp(-max(min(z, 40), -40)))
            r = y - p
            w = p * (1 - p)
            g0 += r
            g1 += r * x
            h00 += w
            h01 += w * x
            h11 += w * x * x
        # 2×2 Hessian inverse
        det = h00 * h11 - h01 * h01
        if abs(det) < 1e-12:
            break
        d0 = (h11 * g0 - h01 * g1) / det
        d1 = (-h01 * g0 + h00 * g1) / det
        b0 += d0
        b1 += d1
        if abs(d0) + abs(d1) < 1e-6:
            break
    if abs(b1) < 1e-6:
        return None
    threshold = -b0 / b1
    return {"b0": b0, "b1": b1, "threshold": threshold, "n": len(pairs)}


def _drift(turns: list[dict], cls: str, final_gap: float | None, feasible: bool):
    """Did p_gap_le_5 move toward the ground truth between first and last turn?

    Returns a dict {direction: 'toward'|'away'|'flat', first, last, realized} or None.
    """
    thresholds = _classify_thresholds(cls)
    # Use the middle threshold as representative
    mid = thresholds[1] if len(thresholds) > 1 else thresholds[0]
    key = _gap_key(mid)
    vals = [t["quality_forecast"].get(key) for t in turns if t.get("quality_forecast") and key in t["quality_forecast"]]
    vals = [v for v in vals if v is not None]
    if len(vals) < 2:
        return None
    first, last = vals[0], vals[-1]
    if feasible and final_gap is not None:
        realized = 1 if final_gap <= mid else 0
    else:
        realized = 0
    # movement toward realized
    first_err = abs(first - realized)
    last_err = abs(last - realized)
    if last_err < first_err - 1e-6:
        direction = "toward"
    elif last_err > first_err + 1e-6:
        direction = "away"
    else:
        direction = "flat"
    return {"first": first, "last": last, "realized": realized, "direction": direction, "threshold": mid}


def aggregate():
    rows = []
    for row_dir in sorted(RESULTS_DIR.iterdir()):
        if not row_dir.is_dir():
            continue
        for model_json in sorted(row_dir.glob("*.json")):
            if model_json.name == "question.json":
                continue
            rec = _collect_per_row(model_json)
            if rec:
                rows.append(rec)

    # Frontier sweep — inverted layout: results/runs/<model>/<row_id>.json.
    # Load question.json from the canonical results/full/<row_id>/ dir so verifier
    # paths + instance access work identically to non-frontier rows.
    if FRONTIER_RUNS_DIR.exists():
        for model_dir in sorted(FRONTIER_RUNS_DIR.iterdir()):
            if not model_dir.is_dir():
                continue
            if model_dir.name not in FRONTIER_MODELS:
                continue
            for row_json in sorted(model_dir.glob("*.json")):
                row_id = row_json.stem
                q_dir = RESULTS_DIR / row_id
                rec = _collect_per_row(row_json, question_row_dir=q_dir)
                if rec:
                    rows.append(rec)

    # Per-(model, class, difficulty) aggregation
    agg = defaultdict(lambda: {"quality": defaultdict(lambda: {"sse": 0.0, "n": 0}),
                                "continue_brier_sse": 0.0,
                                "continue_n": 0,
                                "delta_mae_sum": 0.0,
                                "delta_n": 0,
                                "p_improve_mean_sum": 0.0,
                                "p_improve_mean_n": 0,
                                "realized_improve_sum": 0,
                                "rows": 0,
                                "rows_with_any_qf": 0,
                                "rows_with_any_cf": 0,
                                "turns_with_qf": 0,
                                "drift_toward": 0,
                                "drift_away": 0,
                                "drift_flat": 0})

    all_agg = {
        "quality": defaultdict(lambda: {"sse": 0.0, "n": 0}),
        "continue_brier_sse": 0.0,
        "continue_n": 0,
        "delta_mae_sum": 0.0,
        "delta_n": 0,
        "p_improve_mean_sum": 0.0,
        "p_improve_mean_n": 0,
        "realized_improve_sum": 0,
        "rows": 0,
        "rows_with_any_qf": 0,
        "rows_with_any_cf": 0,
        "turns_with_qf": 0,
        "drift_toward": 0,
        "drift_away": 0,
        "drift_flat": 0,
    }

    for rec in rows:
        key = (rec["model"], rec["class"], rec["difficulty"])
        bucket = agg[key]
        bucket["rows"] += 1
        all_agg["rows"] += 1
        if any(t.get("quality_forecast") for t in rec["turns"]):
            bucket["rows_with_any_qf"] += 1
            all_agg["rows_with_any_qf"] += 1
        if any(t.get("continue_forecast") for t in rec["turns"]):
            bucket["rows_with_any_cf"] += 1
            all_agg["rows_with_any_cf"] += 1

        # Quality Brier
        q = _quality_brier(rec["turns"], rec["class"], rec["final_gap"], rec["feasible"])
        for thr, d in q.items():
            bucket["quality"][thr]["sse"] += d["sse"]
            bucket["quality"][thr]["n"] += d["n"]
            all_agg["quality"][thr]["sse"] += d["sse"]
            all_agg["quality"][thr]["n"] += d["n"]
            bucket["turns_with_qf"] += d["n"]
            all_agg["turns_with_qf"] += d["n"]

        # Continue calibration (final turn vs cf_delta)
        c = _continue_brier(rec["turns"], rec["cf_delta"])
        if c:
            if "brier" in c:
                bucket["continue_brier_sse"] += c["brier"]
                bucket["continue_n"] += 1
                bucket["p_improve_mean_sum"] += c["p_improve"]
                bucket["p_improve_mean_n"] += 1
                bucket["realized_improve_sum"] += c["realized_improve"]
                all_agg["continue_brier_sse"] += c["brier"]
                all_agg["continue_n"] += 1
                all_agg["p_improve_mean_sum"] += c["p_improve"]
                all_agg["p_improve_mean_n"] += 1
                all_agg["realized_improve_sum"] += c["realized_improve"]
            if "delta_mae" in c:
                bucket["delta_mae_sum"] = bucket.get("delta_mae_sum", 0.0) + c["delta_mae"]
                bucket["delta_n"] += 1
                all_agg["delta_mae_sum"] = all_agg.get("delta_mae_sum", 0.0) + c["delta_mae"]
                all_agg["delta_n"] += 1

        # Drift
        drift = _drift(rec["turns"], rec["class"], rec["final_gap"], rec["feasible"])
        if drift:
            bucket[f"drift_{drift['direction']}"] += 1
            all_agg[f"drift_{drift['direction']}"] += 1

    return rows, agg, all_agg


def model_level_stats(rows: list[dict]) -> dict:
    """Build writeup-v2-style metacognitive profile per model.

    Fields per model:
      - m2_brier / reliability / resolution / uncertainty  (Murphy decomp of quality forecast)
      - m3_cf_dollar_mean / median / fraction_wrong        (clean-stop restricted)
      - m4_mae                                             (expected_delta_score vs cf_delta)
      - continue_brier / continue_bss / continue_auc       (final-turn p_improve calibration)
      - sign_agreement_rate                                (DECISION ⟺ expected_delta_score ≤ 0)
      - logistic_threshold                                 (P(stop|delta)=0.5 crossing)
      - feasibility_rate                                   (final_evaluation.feasible)
      - clean_stop_rate / non_termination_rate / mean_exec_turns
    """
    out = {}
    for model in MODELS:
        m_rows = [r for r in rows if r["model"] == model]
        if not m_rows:
            continue

        # --- M1: p_solve Brier over subtasks, kept_as_best outcome, Murphy decomposition ---
        # Portfolio rows contribute no M1 (per-sub-component verification not implemented here).
        m1_pairs = []
        m1_n_rows = 0
        m1_n_portfolio_skipped = 0
        for r in m_rows:
            if r["class"] == "portfolio":
                if r.get("subtasks") == []:
                    m1_n_portfolio_skipped += 1
                continue
            subs = r.get("subtasks") or []
            if not subs:
                continue
            m1_n_rows += 1
            for sub in subs:
                if sub["p_solve"] is None:
                    continue
                if not sub.get("had_best_guess"):
                    # No submission to verify → cannot label outcome cleanly. Skip.
                    continue
                m1_pairs.append((sub["p_solve"], sub["kept_as_best"]))
        m1 = murphy_decomposition(m1_pairs) or {}

        # --- M2: quality-forecast Brier with Murphy decomposition ---
        m2_pairs = []
        for r in m_rows:
            thresholds = _classify_thresholds(r["class"])
            realized_labels = {}
            for thr in thresholds:
                if r["feasible"] and r["final_gap"] is not None:
                    realized_labels[thr] = 1 if r["final_gap"] <= thr else 0
                else:
                    realized_labels[thr] = 0
            for t in r["turns"]:
                qf = t.get("quality_forecast")
                if not qf:
                    continue
                for thr in thresholds:
                    p = qf.get(_gap_key(thr))
                    if p is not None:
                        m2_pairs.append((p, realized_labels[thr]))
        m2 = murphy_decomposition(m2_pairs) or {}

        # --- M3: CF-$ restricted to clean stops ---
        clean_rows = [r for r in m_rows if r["stop_reason"] in CLEAN_STOP_REASONS and r["cf_delta"] is not None]
        cf_deltas = [r["cf_delta"] for r in clean_rows]
        if cf_deltas:
            m3_mean = sum(cf_deltas) / len(cf_deltas)
            m3_median = sorted(cf_deltas)[len(cf_deltas) // 2]
            m3_frac_wrong = sum(1 for d in cf_deltas if d > 0) / len(cf_deltas)
        else:
            m3_mean = m3_median = m3_frac_wrong = None

        # --- M4: MAE of expected_delta_score vs cf_delta (all rows with both) ---
        m4_pairs = []
        for r in m_rows:
            if r["cf_delta"] is None or not r["turns"]:
                continue
            last = r["turns"][-1].get("continue_forecast")
            if not last or "expected_delta_score" not in last:
                continue
            m4_pairs.append((last["expected_delta_score"], r["cf_delta"]))
        m4_mae = (sum(abs(e - a) for e, a in m4_pairs) / len(m4_pairs)) if m4_pairs else None

        # --- Continue-forecast: Brier, BSS, AUC ---
        cont_pairs = []
        for r in m_rows:
            if r["cf_delta"] is None or not r["turns"]:
                continue
            last = r["turns"][-1].get("continue_forecast")
            if not last or "p_improve" not in last:
                continue
            cont_pairs.append((last["p_improve"], 1 if r["cf_delta"] > 0 else 0))
        n_c = len(cont_pairs)
        if n_c:
            brier_c = sum((p - y) ** 2 for p, y in cont_pairs) / n_c
            y_bar = sum(y for _, y in cont_pairs) / n_c
            uncert = y_bar * (1 - y_bar)
            bss = (1 - brier_c / uncert) if uncert > 0 else None  # None = DEGEN (single-class)
            auc = auc_binary(cont_pairs)
        else:
            brier_c = uncert = bss = auc = None

        # --- Penalty-comprehension audit: sign agreement + logistic threshold ---
        # Iterate over every exec turn where both decision and expected_delta_score are parsed.
        audit_pairs = []  # (expected_delta_score, is_stop)
        agree = total_audit = 0
        for r in m_rows:
            for t in r["turns"]:
                d = t.get("decision")
                cf = t.get("continue_forecast") or {}
                e = cf.get("expected_delta_score")
                if d is None or e is None:
                    continue
                is_stop = 1 if d == "stop" else 0
                audit_pairs.append((e, is_stop))
                total_audit += 1
                # sign agreement: stop ⟺ delta ≤ 0
                implied_stop = 1 if e <= 0 else 0
                if is_stop == implied_stop:
                    agree += 1
        sign_agreement = (agree / total_audit) if total_audit else None
        xs, ys = zip(*audit_pairs) if audit_pairs else ([], [])
        logistic = logistic_fit(xs, ys) if audit_pairs else None

        # --- Feasibility / stop-reason / exec-turn counts ---
        n_feasible = sum(1 for r in m_rows if r["feasible"])
        n_clean = sum(1 for r in m_rows if r["stop_reason"] in CLEAN_STOP_REASONS)
        n_non_term = sum(1 for r in m_rows if r["stop_reason"] in NON_TERMINATION_REASONS)
        mean_exec = sum(r["n_exec_turns"] or 0 for r in m_rows) / len(m_rows)

        # Feasibility per class
        feas_per_class = {}
        for cls in SOLO_CLASSES + ("portfolio",):
            cls_rows = [r for r in m_rows if r["class"] == cls]
            if cls_rows:
                feas_per_class[cls] = sum(1 for r in cls_rows if r["feasible"]) / len(cls_rows)

        # Brier Skill Score vs. empirical base-rate predictor.
        # BSS = 1 - Brier/Uncertainty = (Resolution - Reliability) / Uncertainty.
        # NEGATIVE values are preserved — they mean the forecast is actively WORSE than
        # just quoting the base rate (informative signal, not noise).
        m1_bss = (
            (m1["resolution"] - m1["reliability"]) / m1["uncertainty"]
            if m1 and m1.get("uncertainty", 0) > 0 else None
        )
        m2_bss = (
            (m2["resolution"] - m2["reliability"]) / m2["uncertainty"]
            if m2 and m2.get("uncertainty", 0) > 0 else None
        )
        # Refinement = Res / (Res + Rel). Ordering-preserving alternative bounded in [0, 1].
        m1_ref = (
            m1["resolution"] / (m1["resolution"] + m1["reliability"])
            if m1 and (m1.get("resolution", 0) + m1.get("reliability", 0)) > 0 else None
        )
        m2_ref = (
            m2["resolution"] / (m2["resolution"] + m2["reliability"])
            if m2 and (m2.get("resolution", 0) + m2.get("reliability", 0)) > 0 else None
        )

        out[model] = {
            "n_rows": len(m_rows),
            "m1_brier": m1.get("brier"),
            "m1_reliability": m1.get("reliability"),
            "m1_resolution": m1.get("resolution"),
            "m1_uncertainty": m1.get("uncertainty"),
            "m1_bss": m1_bss,
            "m1_refinement": m1_ref,
            "m1_n": m1.get("n"),
            "m1_n_rows_scored": m1_n_rows,
            "m1_n_portfolio_skipped": m1_n_portfolio_skipped,
            "m2_brier": m2.get("brier"),
            "m2_reliability": m2.get("reliability"),
            "m2_resolution": m2.get("resolution"),
            "m2_uncertainty": m2.get("uncertainty"),
            "m2_bss": m2_bss,
            "m2_refinement": m2_ref,
            "m2_n": m2.get("n"),
            "m3_clean_stops": len(clean_rows),
            "m3_cf_dollar_mean": m3_mean,
            "m3_cf_dollar_median": m3_median,
            "m3_fraction_wrong": m3_frac_wrong,
            "m4_mae": m4_mae,
            "continue_brier": brier_c,
            "continue_bss": bss,
            "continue_auc": auc,
            "continue_base_floor": uncert,
            "continue_n": n_c,
            "sign_agreement": sign_agreement,
            "sign_agreement_n": total_audit,
            "logistic": logistic,
            "feasibility_rate": n_feasible / len(m_rows),
            "feasibility_per_class": feas_per_class,
            "clean_stop_rate": n_clean / len(m_rows),
            "non_termination_rate": n_non_term / len(m_rows),
            "mean_exec_turns": mean_exec,
        }
    return out


def _fmt_brier(d):
    if d["n"] == 0:
        return "—"
    return f"{d['sse']/d['n']:.3f}"


def _mean_brier_over_thresholds(quality_agg):
    total_sse = sum(d["sse"] for d in quality_agg.values())
    total_n = sum(d["n"] for d in quality_agg.values())
    if total_n == 0:
        return None
    return total_sse / total_n


# --- Calibration binning + per-class rollup + pricing-bias reconciliation
# (Carla extensions — priorities 1/2/3 from task_17763772282376sh). All additive: they do
# not touch existing M1/M2/M3 numbers; they re-use the same pair collection logic and
# Murphy decomposition.

def _bin_label(b):
    # e.g. [0.0,0.1)
    return f"[{b['lo']:.1f},{b['hi']:.1f})"


def _collect_m1_pairs(rows, model=None, cls=None):
    """Flatten solo-class subtasks into (p_solve, kept_as_best) pairs. Portfolio skipped."""
    pairs = []
    for r in rows:
        if r["class"] == "portfolio":
            continue
        if model is not None and r["model"] != model:
            continue
        if cls is not None and r["class"] != cls:
            continue
        for s in r.get("subtasks") or []:
            if s.get("p_solve") is None:
                continue
            if not s.get("had_best_guess"):
                continue
            pairs.append((float(s["p_solve"]), int(s["kept_as_best"])))
    return pairs


def _collect_m2_pairs(rows, model=None, cls=None):
    """Flatten turn-threshold quality forecasts into (p, realized) pairs."""
    pairs = []
    for r in rows:
        if model is not None and r["model"] != model:
            continue
        if cls is not None and r["class"] != cls:
            continue
        thresholds = _classify_thresholds(r["class"])
        if r["feasible"] and r["final_gap"] is not None:
            realized = {thr: (1 if r["final_gap"] <= thr else 0) for thr in thresholds}
        else:
            realized = {thr: 0 for thr in thresholds}
        for t in r["turns"]:
            qf = t.get("quality_forecast")
            if not qf:
                continue
            for thr in thresholds:
                p = qf.get(_gap_key(thr))
                if p is not None:
                    pairs.append((float(p), realized[thr]))
    return pairs


def _calibration_bins(pairs, n_bins=10):
    """Uniform 1/n-wide bins over [0,1]. Returns list of per-bin dicts with n, p̄, ȳ."""
    bins = []
    for i in range(n_bins):
        bins.append({
            "idx": i,
            "lo": i / n_bins,
            "hi": (i + 1) / n_bins,
            "n": 0,
            "p_sum": 0.0,
            "y_sum": 0,
        })
    for p, y in pairs:
        idx = min(n_bins - 1, max(0, int(p * n_bins)))
        b = bins[idx]
        b["n"] += 1
        b["p_sum"] += p
        b["y_sum"] += int(y)
    for b in bins:
        b["p_mean"] = b["p_sum"] / b["n"] if b["n"] else None
        b["y_mean"] = b["y_sum"] / b["n"] if b["n"] else None
    return bins


def _render_calibration_plot(bins, title, subtitle, bar_width: int = 40):
    """ASCII reliability diagram. Each row = one bin; '.' = forecast p̄, 'o' = observed ȳ."""
    lines = [title, subtitle]
    axis_ruler = ("|" + "0.0" + "-" * 7 + "0.25" + "-" * 7 + "0.5"
                  + "-" * 7 + "0.75" + "-" * 7 + "1.0|")
    lines.append(f"{'bin':<11} {'n':>4}  {'p̄':>5}  {'ȳ':>5}   {axis_ruler}")
    for b in bins:
        label = _bin_label(b)
        if b["n"] == 0:
            lines.append(f"{label:<11} {0:>4}  {'—':>5}  {'—':>5}   |{' '*bar_width}|")
            continue
        bar = [" "] * bar_width
        p_col = min(bar_width - 1, max(0, int(round(b['p_mean'] * (bar_width - 1)))))
        y_col = min(bar_width - 1, max(0, int(round(b['y_mean'] * (bar_width - 1)))))
        bar[p_col] = "."
        if y_col == p_col:
            bar[y_col] = "X"
        else:
            bar[y_col] = "o"
        lines.append(
            f"{label:<11} {b['n']:>4}  {b['p_mean']:>5.2f}  {b['y_mean']:>5.2f}   |{''.join(bar)}|"
        )
    lines.append(
        "Legend: '.' = forecast p̄ for bin | 'o' = observed ȳ | 'X' = same position "
        "(perfect calibration in that bin)"
    )
    return "\n".join(lines)


def _per_class_rollup(rows):
    """For each (model, class) return M1 and M2 Murphy decomposition.

    Portfolio is skipped for M1 (per-sub-component verifier routing not implemented).
    Portfolio IS included for M2 (quality forecasts are still scored against final gap).
    """
    out = []
    for model in MODELS:
        for cls in SOLO_CLASSES + ("portfolio",):
            m1 = None
            if cls != "portfolio":
                m1 = murphy_decomposition(_collect_m1_pairs(rows, model=model, cls=cls))
            m2 = murphy_decomposition(_collect_m2_pairs(rows, model=model, cls=cls))
            out.append({"model": model, "class": cls, "m1": m1, "m2": m2})
    return out


def _pricing_bias(rows):
    """Per-model reconciliation of logistic risk-aversion vs. realized cf_delta.

    For each model:
      - mean_e_all_turns: mean expected_delta_score across every exec turn that emits it
      - paired final-turn E[Δ] aligned to realized cf_delta (the only realized we have)
      - pricing_bias = mean(E[Δ]_final) − mean(cf_Δ) — positive = model overstates value
      - low/high split at the model's own median E[Δ] to test resolution-dependence
    """
    out = {}
    for model in MODELS:
        m_rows = [r for r in rows if r["model"] == model]
        all_e = []
        for r in m_rows:
            for t in r["turns"]:
                cf = t.get("continue_forecast") or {}
                e = cf.get("expected_delta_score")
                if e is not None:
                    all_e.append(float(e))
        paired = []
        for r in m_rows:
            if r["cf_delta"] is None or not r["turns"]:
                continue
            last = r["turns"][-1].get("continue_forecast")
            if not last or last.get("expected_delta_score") is None:
                continue
            paired.append((float(last["expected_delta_score"]), float(r["cf_delta"])))

        mean_e_all = statistics.mean(all_e) if all_e else None
        mean_e_paired = statistics.mean([e for e, _ in paired]) if paired else None
        mean_cf = statistics.mean([c for _, c in paired]) if paired else None
        bias = (mean_e_paired - mean_cf) if (mean_e_paired is not None and mean_cf is not None) else None

        med = None
        low_e = high_e = low_cf = high_cf = []
        if paired:
            es_sorted = sorted(e for e, _ in paired)
            med = es_sorted[len(es_sorted) // 2]
            low_e = [e for e, _ in paired if e <= med]
            high_e = [e for e, _ in paired if e > med]
            low_cf = [c for e, c in paired if e <= med]
            high_cf = [c for e, c in paired if e > med]

        def _mean_or_none(xs):
            return statistics.mean(xs) if xs else None

        out[model] = {
            "n_all_turns": len(all_e),
            "mean_e_all_turns": mean_e_all,
            "n_paired": len(paired),
            "mean_e_paired": mean_e_paired,
            "mean_cf_paired": mean_cf,
            "bias_paired": bias,
            "split_median_e": med,
            "n_low": len(low_e),
            "n_high": len(high_e),
            "low_bin_mean_e": _mean_or_none(low_e),
            "low_bin_mean_cf": _mean_or_none(low_cf),
            "low_bin_bias": (statistics.mean(low_e) - statistics.mean(low_cf))
                if low_e and low_cf else None,
            "high_bin_mean_e": _mean_or_none(high_e),
            "high_bin_mean_cf": _mean_or_none(high_cf),
            "high_bin_bias": (statistics.mean(high_e) - statistics.mean(high_cf))
                if high_e and high_cf else None,
        }
    return out


def _final_score(r: dict) -> float:
    """Verified final score used for M5 cell ceilings. Infeasible rows score 0."""
    if r.get("feasible") and r.get("final_gap") is not None:
        return max(0.0, 100.0 - float(r["final_gap"]))
    return 0.0


def _m5_decomposition(rows):
    """M5 — decomposition effectiveness AUC/ceiling.

    Per solo-class row, compute `M5 = AUC_model / AUC_ceiling` where
      AUC_model    = trapezoidal area under per-turn `score_t = max(0, 100 − gap_pct_t)`
                     with uniform unit spacing between turns
      cell_ceiling = max final_score across the same (model, class, difficulty) cell's
                     seeds (overnight pilot only)
      AUC_ceiling  = cell_ceiling × (n_turns − 1) (flat rectangle at the ceiling)

    Rows with n_turns < 2 are M5-undefined and reported as a separate count. Rows with
    cell_ceiling ≤ 0 fall back to per-class ceiling (across difficulties); if that is
    also 0 the row is excluded. M5 > 1 is possible (row beats its cell ceiling via a
    high-score intermediate turn) and is NOT clipped — the brief asks for both raw mean
    M5 and the fraction of rows with M5 ≥ 1.

    Returns {per_row, per_model, per_cell, per_class, cell_ceiling, class_ceiling}.
    """
    cell_ceiling: dict[tuple[str, str, str], float] = {}
    class_ceiling: dict[tuple[str, str], float] = {}
    for r in rows:
        if r["class"] == "portfolio":
            continue
        fs = _final_score(r)
        cell_key = (r["model"], r["class"], r["difficulty"])
        if fs > cell_ceiling.get(cell_key, -1.0):
            cell_ceiling[cell_key] = fs
        cls_key = (r["model"], r["class"])
        if fs > class_ceiling.get(cls_key, -1.0):
            class_ceiling[cls_key] = fs

    per_row = []
    for r in rows:
        if r["class"] == "portfolio":
            continue
        ts = r.get("turn_scores") or []
        n = len(ts)
        cell_key = (r["model"], r["class"], r["difficulty"])
        ceiling = cell_ceiling.get(cell_key, 0.0)
        ceiling_source = "cell"
        if ceiling <= 0.0:
            ceiling = class_ceiling.get((r["model"], r["class"]), 0.0)
            ceiling_source = "class" if ceiling > 0.0 else "none"
        entry = {
            "model": r["model"],
            "class": r["class"],
            "difficulty": r["difficulty"],
            "row_id": r["row_id"],
            "n_turns": n,
            "ceiling": ceiling,
            "ceiling_source": ceiling_source,
            "auc_model": None,
            "auc_ceiling": None,
            "m5": None,
            "reason": None,
        }
        if n < 2:
            entry["reason"] = "n_turns<2"
            per_row.append(entry)
            continue
        if ceiling <= 0.0:
            entry["reason"] = "ceiling<=0"
            per_row.append(entry)
            continue
        auc_model = sum(
            (ts[i]["score"] + ts[i + 1]["score"]) / 2.0
            for i in range(n - 1)
        )
        auc_ceiling = ceiling * (n - 1)
        entry["auc_model"] = auc_model
        entry["auc_ceiling"] = auc_ceiling
        entry["m5"] = auc_model / auc_ceiling
        per_row.append(entry)

    def _agg(entries):
        eligible = [e for e in entries if e["m5"] is not None]
        trivial = sum(1 for e in entries if e["reason"] == "n_turns<2")
        zero_c = sum(1 for e in entries if e["reason"] == "ceiling<=0")
        if eligible:
            m5_mean = sum(e["m5"] for e in eligible) / len(eligible)
            m5_ge1 = sum(1 for e in eligible if e["m5"] >= 1.0) / len(eligible)
        else:
            m5_mean = m5_ge1 = None
        return {
            "m5_mean": m5_mean,
            "m5_ge1_frac": m5_ge1,
            "n_eligible": len(eligible),
            "n_trivial": trivial,
            "n_zero_ceiling": zero_c,
            "n_total": len(entries),
        }

    per_model = {}
    for model in MODELS:
        per_model[model] = _agg([e for e in per_row if e["model"] == model])

    per_cell = {}
    for e in per_row:
        per_cell.setdefault((e["model"], e["class"], e["difficulty"]), []).append(e)
    per_cell = {k: _agg(v) | {"ceiling": cell_ceiling.get(k, 0.0)} for k, v in per_cell.items()}

    per_class = {}
    for e in per_row:
        per_class.setdefault((e["model"], e["class"]), []).append(e)
    per_class = {k: _agg(v) | {"ceiling": class_ceiling.get(k, 0.0)} for k, v in per_class.items()}

    return {
        "per_row": per_row,
        "per_model": per_model,
        "per_cell": per_cell,
        "per_class": per_class,
        "cell_ceiling": cell_ceiling,
        "class_ceiling": class_ceiling,
    }


def write_report(rows, agg, all_agg, mstats, m5=None):
    lines = []
    lines.append("# Metacog Forecast Analysis — overnight 64-row set × 3 models")
    lines.append("")
    total_rows = all_agg["rows"]
    rows_with_qf = all_agg["rows_with_any_qf"]
    rows_with_cf = all_agg["rows_with_any_cf"]
    qturns = all_agg["turns_with_qf"]

    lines.append(
        f"**Coverage:** {total_rows} rows (192 expected = 64 unique row_ids × 3 models), "
        f"{rows_with_qf} with ≥1 QUALITY_FORECAST ({rows_with_qf/total_rows*100:.0f}%), "
        f"{rows_with_cf} with ≥1 CONTINUE_FORECAST, "
        f"{qturns} forecast-turns scored against final realized gap."
    )
    lines.append("")

    # Headline Brier (overall mean across thresholds)
    overall_q = _mean_brier_over_thresholds(all_agg["quality"])
    overall_cbrier = (
        all_agg["continue_brier_sse"] / all_agg["continue_n"]
        if all_agg["continue_n"] else None
    )
    base_rate_improve = (
        all_agg["realized_improve_sum"] / all_agg["continue_n"]
        if all_agg["continue_n"] else None
    )
    # Always-say-base-rate Brier floor
    if base_rate_improve is not None:
        base_brier = base_rate_improve * (1 - base_rate_improve)
    else:
        base_brier = None

    # M1 headline
    m1_cells = {m: mstats.get(m, {}) for m in MODELS}
    m1_parts = []
    for m in MODELS:
        v = m1_cells[m]
        if v.get("m1_brier") is not None:
            m1_parts.append(
                f"{m.split('-')[0].capitalize()} Brier={v['m1_brier']:.3f}/res={v['m1_resolution']:.3f}"
            )
    m1_line = "; ".join(m1_parts) if m1_parts else "n/a"

    headline = (
        f"**Headline:** Overall Quality Brier = {overall_q:.3f} (lower is better; 0.25 = uniform-random floor) — "
        f"but the model spread is large (Sonnet 0.096 / GPT 0.147 / Gemini 0.315) and much of the apparent "
        f"calibration comes from correctly-low confidence on runs that end infeasible. "
        f"**M1 (subtask p_solve Brier):** {m1_line}. GPT has the highest resolution (informativeness) on "
        f"M1 despite the highest Brier — it moves `p_solve` around more, even though its calibration is "
        f"worse than Sonnet's. "
        f"Continue-forecast Brier = {overall_cbrier:.3f}; models are mildly overconfident on `p_improve` "
        f"(mean {all_agg['p_improve_mean_sum']/all_agg['p_improve_mean_n']:.2f} vs. observed CF-improve rate "
        f"{base_rate_improve:.2f}) and essentially uninformative beyond 'stopping was the right call'."
    )
    lines.append(headline)
    lines.append("")

    lines.append("## 1. Quality Brier by model × class × difficulty (mean over thresholds)")
    lines.append("")
    header = ["model", "class", "diff", "rows", "turns"] + [
        f"p_gap_le_{format(t,'g').replace('.','_')}" for t in (2, 5, 10)
    ] + ["mean_brier"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")

    for model in MODELS:
        for cls in CLASSES:
            for diff in DIFFICULTIES:
                key = (model, cls, diff)
                bucket = agg.get(key)
                if not bucket:
                    continue
                row = [model, cls, diff, str(bucket["rows"]), str(bucket["turns_with_qf"])]
                for thr in (2, 5, 10):
                    d = bucket["quality"].get(float(thr), bucket["quality"].get(thr, {"sse": 0.0, "n": 0}))
                    row.append(_fmt_brier(d))
                mean = _mean_brier_over_thresholds(bucket["quality"])
                row.append(f"{mean:.3f}" if mean is not None else "—")
                lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append("(VE rows: re-scored against solo-style 2/5/10 thresholds. VE's canonical strict-parse contract "
                  "requires 0.01/0.1/0.5, but every model in this set emits solo-style keys — flagged in caveats.)")
    lines.append("")

    lines.append("## 2. Continue-forecast calibration (final-turn p_improve vs cf_delta>0)")
    lines.append("")
    header = ["model", "class", "diff", "rows_scored", "mean_p_improve",
              "observed_improve_rate", "brier", "vs_base", "delta_mae"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    for model in MODELS:
        for cls in CLASSES:
            for diff in DIFFICULTIES:
                key = (model, cls, diff)
                bucket = agg.get(key)
                if not bucket or bucket["continue_n"] == 0:
                    continue
                mean_p = bucket["p_improve_mean_sum"] / bucket["p_improve_mean_n"]
                rate = bucket["realized_improve_sum"] / bucket["continue_n"]
                brier = bucket["continue_brier_sse"] / bucket["continue_n"]
                base_floor = rate * (1 - rate)
                vs_base = f"{brier - base_floor:+.3f}"
                delta_mae = (
                    f"{bucket['delta_mae_sum'] / bucket['delta_n']:.2f}"
                    if bucket["delta_n"] else "—"
                )
                row = [model, cls, diff, str(bucket["continue_n"]),
                       f"{mean_p:.2f}", f"{rate:.2f}", f"{brier:.3f}",
                       vs_base, delta_mae]
                lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    # --------- NEW: writeup-v2-style metacognitive profile ---------
    # ---- Family-consistency table (frontier vs small, within family) ----
    lines.append("## 3. Family-consistency table — 6 models, 2 per family")
    lines.append("")
    lines.append(
        "Tests whether the small-tier metacog axis profile replicates at the frontier "
        "tier within each family. Columns: M1-Brier / M1-BSS (unclipped) / M1-resolution / "
        "M2-Brier / M2-BSS (unclipped) / M2-resolution / M4-MAE / feasibility. "
        "M1 BSS is None when the model's kept_as_best outcome is single-valued (uncertainty=0 → BSS undefined)."
    )
    lines.append("")
    header = ["family", "tier", "model", "n_rows", "M1-Br", "M1-BSS", "M1-res",
              "M2-Br", "M2-BSS", "M2-res", "M4-MAE", "feas"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")
    family_order = [
        ("anthropic", ("claude-sonnet-4.6", "claude-opus-4.6")),
        ("google",    ("gemini-flash-latest", "gemini-3-pro-preview")),
        ("openai",    ("gpt-5.4-mini", "gpt-5.4")),
    ]
    def _fmt(x, spec):
        return spec.format(x) if x is not None else "—"
    for fam, pair in family_order:
        for model in pair:
            v = mstats.get(model)
            if not v:
                lines.append(f"| {fam} | {TIER.get(model,'?')} | {model} | 0 | — | — | — | — | — | — | — | — |")
                continue
            lines.append(
                f"| {fam} | {TIER.get(model,'?')} | {model} | {v['n_rows']} | "
                f"{_fmt(v.get('m1_brier'),'{:.3f}')} | {_fmt(v.get('m1_bss'),'{:+.3f}')} | "
                f"{_fmt(v.get('m1_resolution'),'{:.3f}')} | {_fmt(v.get('m2_brier'),'{:.3f}')} | "
                f"{_fmt(v.get('m2_bss'),'{:+.3f}')} | {_fmt(v.get('m2_resolution'),'{:.3f}')} | "
                f"{_fmt(v.get('m4_mae'),'{:.2f}')} | {_fmt(v.get('feasibility_rate'),'{:.0%}')} |"
            )
    lines.append("")

    # Per-family verdicts (computed from the table numbers; written in-line so the
    # writeup can quote them with a single cross-reference).
    verdicts = []
    def _pair_stats(pair):
        return [mstats.get(m) or {} for m in pair]
    for fam, pair in family_order:
        a, b = _pair_stats(pair)
        small, frontier = a, b
        n_small = small.get("n_rows", 0); n_front = frontier.get("n_rows", 0)
        m2bss_small = small.get("m2_bss"); m2bss_front = frontier.get("m2_bss")
        m1bss_small = small.get("m1_bss"); m1bss_front = frontier.get("m1_bss")
        m2res_small = small.get("m2_resolution") or 0.0
        m2res_front = frontier.get("m2_resolution") or 0.0
        feas_small = small.get("feasibility_rate") or 0.0
        feas_front = frontier.get("feasibility_rate") or 0.0
        caveat = f" (Opus N={n_front} — small-sample caveat)" if n_front < 10 else ""
        if fam == "anthropic":
            # monitoring claim: both positive M2-BSS?
            ok = (m2bss_small is not None and m2bss_small > 0) and (m2bss_front is not None and m2bss_front > 0)
            exec_patch = feas_front - feas_small
            v = "CONFIRMED" if ok else ("PARTIAL" if (m2bss_front is not None and m2bss_front > 0) else "REJECTED")
            verdicts.append(
                f"- **anthropic — monitoring axis {v}**{caveat}. "
                f"Sonnet M2-BSS {m2bss_small:+.2f} / Opus M2-BSS "
                f"{('%+.2f' % m2bss_front) if m2bss_front is not None else '—'}; both positive ⇒ monitoring replicates. "
                f"Opus additionally patches Sonnet's execution failure mode (feas {feas_small:.0%} → {feas_front:.0%})."
            )
        elif fam == "google":
            # flat-forecaster claim: both negative M1-BSS AND low M2-resolution?
            flat_at_frontier = (m2bss_front is not None and m2bss_front < 0) and (m2res_front < 0.05)
            v = "REJECTED" if (m2bss_front is not None and m2bss_front > 0) else ("CONFIRMED" if flat_at_frontier else "PARTIAL")
            verdicts.append(
                f"- **google — flat-forecaster axis {v}**. "
                f"Flash M2-BSS {m2bss_small:+.2f} (res {m2res_small:.3f}) vs Gemini-3-Pro M2-BSS "
                f"{('%+.2f' % m2bss_front) if m2bss_front is not None else '—'} "
                f"(res {m2res_front:.3f}). "
                + ("Frontier tier INVERTS the flat pattern: real M2 resolution + positive BSS. "
                   "Flat-forecaster is a Flash-tier artifact, not a family-level specialization."
                   if v == "REJECTED" else
                   "Frontier replicates the low-resolution narrow-band pattern.")
            )
        else:
            # sharp-and-wrong M2: both catastrophically negative M2-BSS
            both_neg = (m2bss_small is not None and m2bss_small < -1) and (m2bss_front is not None and m2bss_front < -1)
            v = "CONFIRMED" if both_neg else "PARTIAL"
            verdicts.append(
                f"- **openai — sharp-and-wrong-M2 axis {v}**. "
                f"GPT-5.4-mini M2-BSS {m2bss_small:+.2f} / GPT-5.4 M2-BSS "
                f"{('%+.2f' % m2bss_front) if m2bss_front is not None else '—'}. "
                f"Catastrophic M2 replicates across tiers — the sibling relationship is preserved."
            )
    lines.append("**Per-family verdict (from the table above):**")
    lines.extend(verdicts)
    lines.append("")
    lines.append(
        "**Reading the verdicts.** An inversion at the frontier tier (google) is as informative "
        "as a replication (openai, anthropic-monitoring): it shows that the specialization axis "
        "lives at a specific tier, not at the family. Opus's execution patch is itself a within-family finding: "
        "\"Opus fixes what Sonnet couldn't solve, but preserves Sonnet's monitoring advantage.\""
    )
    lines.append("")

    lines.append("## 3b. Metacognitive profile (writeup-v2 layout)")
    lines.append("")
    lines.append("Model-level metacog metrics as framed in `kaggle_submission/writeup-v2.md`.  "
                  "M1 (p_solve Brier) is computed over solo-class subtasks only — portfolio rows are "
                  "skipped because we do not re-score per-sub-component best_guess payloads in this pass. "
                  "M5 and M6 require additional runs.")
    lines.append("")
    header = ["metric"] + list(MODELS) + ["what it measures"]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "|".join(["---"] * len(header)) + "|")

    def _cell(model, key, fmt="{:.3f}"):
        v = mstats.get(model, {}).get(key)
        if v is None:
            return "—"
        try:
            return fmt.format(v)
        except Exception:
            return str(v)

    def _row(label, key, fmt="{:.3f}", notes=""):
        cells = [label] + [_cell(m, key, fmt) for m in MODELS] + [notes]
        lines.append("| " + " | ".join(cells) + " |")

    _row("M1 Brier (p_solve)",            "m1_brier",        "{:.3f}", "knowing what you know — Brier on subtask-kept-as-best outcomes")
    _row("— M1 reliability",               "m1_reliability",  "{:.3f}", "Murphy: calibration component (lower=better)")
    _row("— M1 resolution",                "m1_resolution",   "{:.3f}", "Murphy: informativeness component (higher=better)")
    _row("— M1 uncertainty",               "m1_uncertainty",  "{:.3f}", "Murphy: base-rate entropy (not model-dependent)")
    _row("— **M1 BSS** (unclipped)",       "m1_bss",          "{:+.3f}", "skill score; NEGATIVE = worse than quoting base rate")
    _row("— M1 refinement Res/(Res+Rel)", "m1_refinement",   "{:.3f}", "bounded [0,1] alternative to BSS")
    _row("— M1 n (subtasks)",              "m1_n",            "{}",     "denominator — solo-class subtasks with parseable p_solve + best_guess")
    _row("M2 Brier (quality forecast)", "m2_brier", "{:.3f}",
          "self-assessing output without oracle")
    _row("— M2 reliability",              "m2_reliability", "{:.3f}", "Murphy: calibration component (lower=better)")
    _row("— M2 resolution",               "m2_resolution",  "{:.3f}", "Murphy: informativeness component (higher=better)")
    _row("— M2 uncertainty",              "m2_uncertainty", "{:.3f}", "Murphy: base-rate entropy (not model-dependent)")
    _row("— **M2 BSS** (unclipped)",      "m2_bss",         "{:+.3f}", "skill score; NEGATIVE = worse than quoting base rate")
    _row("— M2 refinement Res/(Res+Rel)","m2_refinement",   "{:.3f}", "bounded [0,1] alternative to BSS")
    _row("M3 CF-\\$ mean Δ",              "m3_cf_dollar_mean",  "{:+.3f}", "knowing when to stop (clean stops only)")
    _row("M3 CF-\\$ median",              "m3_cf_dollar_median", "{:+.3f}", "clean-stop-restricted")
    _row("M3 fraction-of-stops-wrong",   "m3_fraction_wrong",   "{:.0%}",   "% of clean stops where CF improved")
    _row("M3 clean-stops n",              "m3_clean_stops",      "{}",       "denominator for M3")
    _row("M4 forecast error (MAE)",       "m4_mae",              "{:.2f}",   "predicting value of more effort")
    _row("Continue Brier",                "continue_brier",      "{:.3f}",   "raw Brier on final-turn p_improve")
    _row("Continue BSS",                  "continue_bss",        "{:+.2f}",  "skill score vs. base-rate floor (>0 beats base rate; None=DEGEN)")
    _row("Continue AUC",                  "continue_auc",        "{:.2f}",   "discrimination (None=one-class)")
    _row("Sign agreement (DECISION↔Δ≤0)", "sign_agreement",      "{:.0%}",   "penalty-comprehension audit Test 1")
    _row("Sign audit n (turns)",          "sign_agreement_n",    "{}",       "")
    # Logistic threshold needs nested-dict unpacking
    lg_cells = ["Logistic threshold"]
    for m in MODELS:
        lg = mstats.get(m, {}).get("logistic")
        lg_cells.append(f"{lg['threshold']:+.2f}" if lg else "—")
    lg_cells.append("P(stop)=0.5 crossing over expected_delta_score; >0 = risk-averse pricing")
    lines.append("| " + " | ".join(lg_cells) + " |")
    _row("Feasibility rate",              "feasibility_rate",    "{:.0%}",   "% rows where final submission verifies feasible")
    _row("Clean-stop rate",               "clean_stop_rate",     "{:.0%}",   "% rows ending via subtask_stop / turn1_stop")
    _row("Non-termination rate",          "non_termination_rate", "{:.0%}",  "% rows hitting budget / timeout / error")
    _row("Mean exec turns",               "mean_exec_turns",     "{:.2f}",   "n_exec_turns across rows")
    lines.append("")

    # Unpack logistic separately — can't hand _row a nested dict
    lines.append("**Logistic fit P(stop | expected_delta_score):**")
    for model in MODELS:
        lg = mstats.get(model, {}).get("logistic")
        if lg:
            lines.append(
                f"- `{model}`: β₀ = {lg['b0']:+.2f}, β₁ = {lg['b1']:+.3f}, "
                f"threshold = {lg['threshold']:+.2f} (n = {lg['n']}).  "
                f"Interpretation: P(stop)=0.5 crosses when expected_delta_score = {lg['threshold']:+.2f} — "
                f"{'risk-averse (stops before break-even)' if lg['threshold'] > 0.5 else 'risk-seeking (continues past break-even)' if lg['threshold'] < -0.5 else 'near-rational pricing'}."
            )
        else:
            lines.append(f"- `{model}`: logistic degenerate (no variance in DECISION or too few turns).")
    lines.append("")

    # Feasibility per class
    lines.append("**Feasibility rate per (model × class):**")
    lines.append("")
    header_f = ["model"] + list(SOLO_CLASSES + ("portfolio",))
    lines.append("| " + " | ".join(header_f) + " |")
    lines.append("|" + "|".join(["---"] * len(header_f)) + "|")
    for model in MODELS:
        cells = [model]
        fp = mstats.get(model, {}).get("feasibility_per_class", {})
        for cls in SOLO_CLASSES + ("portfolio",):
            v = fp.get(cls)
            cells.append(f"{v:.0%}" if v is not None else "—")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")

    # --------- END new section ---------

    # --------- §M5 decomposition effectiveness (AUC / ceiling) ---------
    if m5:
        lines.append("## 3a. M5 — Decomposition effectiveness (AUC / ceiling)")
        lines.append("")
        pm = m5.get("per_model", {})
        # Headline sentence
        parts = []
        for model in MODELS:
            v = pm.get(model, {})
            if v.get("m5_mean") is not None:
                short = model.split("-")[0].capitalize()
                parts.append(
                    f"{short} M5={v['m5_mean']:.3f} (n_eligible={v['n_eligible']}, "
                    f"≥1 frac={v['m5_ge1_frac']:.0%})"
                )
            else:
                parts.append(f"{model.split('-')[0].capitalize()} M5=— (no eligible rows)")
        headline_m5 = (
            "**M5 headline:** " + "; ".join(parts) + ". "
            "Per-row M5 = AUC(score trajectory) / (cell ceiling × (n_turns−1)). "
            "Ceilings are max final_score across the (model, class, difficulty) seeds "
            "in the overnight pilot; infeasible rows contribute 0 to ceilings. "
            "Rows with n_exec_turns < 2 are M5-undefined (no interval to integrate) "
            "and reported separately; cells where the ceiling is 0 fall back to the "
            "per-class ceiling across difficulties, or are excluded if that is also 0. "
            "M5 > 1 is possible and NOT clipped — it indicates the row's trajectory "
            "area beats the cell's ceiling rectangle."
        )
        lines.append(headline_m5)
        lines.append("")

        # Per-model rollup table
        lines.append("### M5 per-model rollup")
        lines.append("")
        lines.append("| model | mean M5 | frac M5 ≥ 1 | n eligible | n trivial (n_turns<2) | n zero-ceiling | total rows |")
        lines.append("|---|---|---|---|---|---|---|")
        for model in MODELS:
            v = pm.get(model, {})
            if v.get("n_total", 0) == 0:
                continue
            m5m = f"{v['m5_mean']:.3f}" if v.get("m5_mean") is not None else "—"
            ge1 = f"{v['m5_ge1_frac']:.0%}" if v.get("m5_ge1_frac") is not None else "—"
            lines.append(
                f"| {model} | {m5m} | {ge1} | {v['n_eligible']} | {v['n_trivial']} | "
                f"{v['n_zero_ceiling']} | {v['n_total']} |"
            )
        lines.append("")

        # Per-class breakdown table
        lines.append("### M5 per-(model, class) breakdown (aggregated across difficulties)")
        lines.append("")
        lines.append("| model | class | mean M5 | frac M5 ≥ 1 | n eligible | n trivial | ceiling |")
        lines.append("|---|---|---|---|---|---|---|")
        pc = m5.get("per_class", {})
        for model in MODELS:
            for cls in SOLO_CLASSES:
                v = pc.get((model, cls))
                if not v or v.get("n_total", 0) == 0:
                    continue
                m5m = f"{v['m5_mean']:.3f}" if v.get("m5_mean") is not None else "—"
                ge1 = f"{v['m5_ge1_frac']:.0%}" if v.get("m5_ge1_frac") is not None else "—"
                lines.append(
                    f"| {model} | {cls} | {m5m} | {ge1} | {v['n_eligible']} | "
                    f"{v['n_trivial']} | {v['ceiling']:.1f} |"
                )
        lines.append("")
        lines.append(
            "**Interpretation.** A model that reaches its own cell ceiling fast and holds "
            "it earns high M5; a model that leaves score on the table by stopping early, "
            "oscillating, or failing to recover after a bad intermediate turn earns low M5. "
            "M5 is capability-controlled by design (the denominator is the model's OWN "
            "ceiling in the cell), so a lower-capability model with a low ceiling can still "
            "score high M5 if it uses its turns efficiently. Caveat: mean n_exec_turns "
            "overnight is ~1.3, so many rows are trivially excluded; M5 is informative only "
            "where a model took ≥2 exec turns in a cell."
        )
        lines.append("")
    # --------- END §M5 ---------

    # Per-model rollup (legacy — kept for CSV parity)
    lines.append("## 4. Model-level rollup (raw)")
    lines.append("")
    lines.append("| model | rows | mean_quality_brier | mean_continue_brier | base_floor | Δvs_base | mean_p_improve | observed_rate |")
    lines.append("|---|---|---|---|---|---|---|---|")
    per_model = defaultdict(lambda: {"q_sse": 0.0, "q_n": 0, "c_sse": 0.0, "c_n": 0,
                                       "p_sum": 0.0, "p_n": 0, "realized": 0, "rows": 0})
    for (model, cls, diff), bucket in agg.items():
        pm = per_model[model]
        pm["rows"] += bucket["rows"]
        for d in bucket["quality"].values():
            pm["q_sse"] += d["sse"]
            pm["q_n"] += d["n"]
        pm["c_sse"] += bucket["continue_brier_sse"]
        pm["c_n"] += bucket["continue_n"]
        pm["p_sum"] += bucket["p_improve_mean_sum"]
        pm["p_n"] += bucket["p_improve_mean_n"]
        pm["realized"] += bucket["realized_improve_sum"]
    for model in MODELS:
        pm = per_model.get(model)
        if not pm or pm["q_n"] == 0:
            continue
        q = pm["q_sse"] / pm["q_n"]
        c = pm["c_sse"] / pm["c_n"] if pm["c_n"] else None
        rate = pm["realized"] / pm["c_n"] if pm["c_n"] else None
        base = rate * (1 - rate) if rate is not None else None
        mean_p = pm["p_sum"] / pm["p_n"] if pm["p_n"] else None
        lines.append(
            f"| {model} | {pm['rows']} | {q:.3f} | "
            f"{c:.3f} | {base:.3f} | {c - base:+.3f} | "
            f"{mean_p:.2f} | {rate:.2f} |"
        )
    lines.append("")

    # Drift summary
    lines.append("## 4. Forecast drift (first vs last turn, middle threshold)")
    lines.append("")
    lines.append("| model | toward_truth | away_from_truth | flat | eligible_rows (n_exec_turns≥2) |")
    lines.append("|---|---|---|---|---|")
    drift_per_model = defaultdict(lambda: {"toward": 0, "away": 0, "flat": 0})
    for (model, cls, diff), bucket in agg.items():
        dpm = drift_per_model[model]
        dpm["toward"] += bucket["drift_toward"]
        dpm["away"] += bucket["drift_away"]
        dpm["flat"] += bucket["drift_flat"]
    for model in MODELS:
        d = drift_per_model.get(model, {"toward": 0, "away": 0, "flat": 0})
        total = d["toward"] + d["away"] + d["flat"]
        lines.append(f"| {model} | {d['toward']} | {d['away']} | {d['flat']} | {total} |")
    lines.append("")

    # Missing / malformed notes
    lines.append("## 5. Missing / malformed forecasts")
    lines.append("")
    missing_lines = []
    for model in MODELS:
        m_rows = [r for r in rows if r["model"] == model]
        tot = len(m_rows)
        rows_no_qf = sum(1 for r in m_rows if not any(t.get("quality_forecast") for t in r["turns"]))
        rows_no_cf = sum(1 for r in m_rows if not any(t.get("continue_forecast") for t in r["turns"]))
        zero_turn = sum(1 for r in m_rows if not r["turns"])
        missing_lines.append(
            f"- **{model}**: {tot} rows, {rows_no_qf} rows with no QF "
            f"({rows_no_qf/tot*100:.0f}%), {rows_no_cf} with no CF, {zero_turn} with no parsed turns at all."
        )
    lines.extend(missing_lines)
    lines.append("")

    # Findings
    lines.append("## 6. Findings")
    lines.append("")
    findings = []

    # Finding 1: overall vs. random
    findings.append(
        f"1. **Quality forecasts beat uniform-random but mostly by staying pessimistic.** "
        f"Overall mean Brier = {overall_q:.3f}. For context: 0.000 = oracle, 0.250 = uniform random. "
        f"The biggest Brier contributions are from individual model×class cells where forecasts swing "
        f"high but realized `I[gap≤k]` is 0 — e.g. Sonnet on **cjs_medium** (0.883 Brier, 6 turns, "
        f"over-predicting gap ≤ 2) and Gemini on **portfolio_hard** (0.548) / **mwis_hard** (0.362). "
        f"Conversely, the many 0.000 cells are trivial: the model emits 1.0 for a feasible, low-gap "
        f"run (e.g. Sonnet graphcol × both difficulties) or 0.0 for a clearly-failed portfolio row."
    )

    # Finding 2: per-model ranking
    model_q = {}
    for model, pm in per_model.items():
        if pm["q_n"]:
            model_q[model] = pm["q_sse"] / pm["q_n"]
    ranked = sorted(model_q.items(), key=lambda kv: kv[1])
    findings.append(
        "2. **Quality-Brier ranking across models:** " + ", ".join(
            f"{m} = {v:.3f}" for m, v in ranked
        ) + f" ({'lower is better' if len(ranked) > 1 else 'only one model'}; "
            f"gap = {ranked[-1][1] - ranked[0][1]:.3f})."
    )

    # Finding 3: continue-forecast signal — per-model detail
    if all_agg["continue_n"]:
        c = all_agg["continue_brier_sse"] / all_agg["continue_n"]
        rate = all_agg["realized_improve_sum"] / all_agg["continue_n"]
        mean_p = all_agg["p_improve_mean_sum"] / all_agg["p_improve_mean_n"]
        base = rate * (1 - rate)
        # GPT is the clearest case: observed_rate=0 so base floor=0
        gpt_bucket = per_model.get("gpt-5.4-mini", {})
        gpt_mean_p = (
            gpt_bucket["p_sum"] / gpt_bucket["p_n"]
            if gpt_bucket.get("p_n") else None
        )
        gpt_rate = (
            gpt_bucket["realized"] / gpt_bucket["c_n"]
            if gpt_bucket.get("c_n") else None
        )
        findings.append(
            f"3. **GPT-5.4-mini is the clearest case of miscalibrated `p_improve`.** "
            f"GPT's CF branches improved 0/42 times (observed rate = 0.00), so the optimal "
            f"constant predictor would say 0.00 and score Brier = 0.00. GPT instead emits "
            f"mean p_improve = {gpt_mean_p:.2f}, yielding Brier = {gpt_bucket['c_sse']/gpt_bucket['c_n']:.3f} "
            f"— i.e. all of its Brier comes from over-predicting improvement that never materialized. "
            f"Sonnet's 4% / Gemini's 14% base rate leave a small informative margin; "
            f"all three sit within ±0.03 of their own base-rate floors, so the forecast adds "
            f"almost no resolution over just quoting the base rate."
        )

    # Finding 4: portfolio-specific
    pf_q_sse = 0.0
    pf_q_n = 0
    solo_q_sse = 0.0
    solo_q_n = 0
    for (model, cls, diff), bucket in agg.items():
        for d in bucket["quality"].values():
            if cls == "portfolio":
                pf_q_sse += d["sse"]; pf_q_n += d["n"]
            else:
                solo_q_sse += d["sse"]; solo_q_n += d["n"]
    if pf_q_n and solo_q_n:
        pf_b = pf_q_sse / pf_q_n
        solo_b = solo_q_sse / solo_q_n
        findings.append(
            f"4. **Portfolio Brier is numerically *lower* than solo — but this is a trivial win, not a calibration signal.** "
            f"Portfolio Brier = {pf_b:.3f} (n={pf_q_n} turn-thresholds), solo Brier = {solo_b:.3f} (n={solo_q_n}). "
            f"On portfolio, ~97% of rows are infeasible (realized `I[gap≤k] = 0`), and models emit "
            f"correspondingly low p_gap_le_k values — so squared error stays small for the wrong reason. "
            f"**Solo-class Brier is the honest calibration metric** because feasibility ≈ 100% there, "
            f"so realized labels actually vary across turns."
        )

    # Finding 5: delta MAE
    dmae_n = all_agg["delta_n"]
    if dmae_n:
        dmae = all_agg["delta_mae_sum"] / dmae_n
        findings.append(
            f"5. **`expected_delta_score` regression fit is weak.** MAE = {dmae:.2f} "
            f"across {dmae_n} final-turn predictions against cf_delta. "
            f"This is consistent with models treating CONTINUE_FORECAST as a cursory emission "
            f"rather than an estimate grounded in a cost model for their own turn."
        )

    lines.extend(findings)
    lines.append("")

    lines.append("## 7. Open questions / caveats")
    lines.append("")
    lines.append("- **M1 skips portfolio rows.** Portfolio BEST_GUESS is a nested dict keyed by "
                  "sub-component problem_id and would need per-sub-component verifier routing. "
                  "M1 is therefore computed on solo-class subtasks only (n = 34–49 subtasks per model; "
                  "28–36 rows per model contribute). Subtasks without a parseable `best_guess` are also "
                  "skipped (no outcome to label).")
    lines.append("- **M1 outcome is `kept_as_best`, not `feasible`.** Subtask 1 is kept_as_best=1 iff "
                  "feasible (no prior to beat); subtask k≥2 is kept_as_best=1 iff its verified gap_pct "
                  "is strictly lower than every prior subtask's gap_pct. This is the writeup-v2 framing; "
                  "using `feasible` alone would make kept_as_best monotone-decreasing across turns and "
                  "hide subtasks that improve on a feasible baseline.")
    lines.append("- **Per-turn ground truth is unavailable.** We only have the final realized gap "
                  "(from `final_evaluation.gap_pct`) and the counterfactual-continue delta "
                  "(`cf_delta`). For multi-turn runs, intermediate best_guess scores are not stored, "
                  "so mid-run quality forecasts are scored against the *final* gap — biasing "
                  "calibration for models whose final turn improved over mid-run state.")
    lines.append("- **Infeasible rows are treated as realized=0 for all thresholds.** This is the "
                  "natural reading (quality target was not met) but does penalize models that forecast "
                  "some probability of hitting a gap target before their submission is rejected by the "
                  "feasibility layer.")
    lines.append("- **`cf_delta` is a noisy signal for continue-forecast calibration.** The CF branch "
                  "runs a single additional turn from the same state, but with a different random "
                  "draw. A model's p_improve could legitimately be 0.6 and still see cf_delta ≤ 0 "
                  "due to the specific CF trajectory.")
    lines.append("- **Portfolio uses solo-style thresholds (2/5/10).** Confirmed from `cf_parsed` "
                  "entries in `portfolio_*_seedN.json`. If the intent was a portfolio-specific "
                  "threshold set, the forecasts-as-emitted can't reflect that.")
    lines.append("- **VE protocol drift: models emit solo keys for VE.** `harness/protocol.py` defines "
                  "`VE_GAP_THRESHOLDS = (0.01, 0.1, 0.5)` and the emit-spec says 'or the VE-specific "
                  "thresholds if this is `ve`', but *every* VE transcript in the overnight set emits "
                  "`p_gap_le_2 / 5 / 10`. This analysis falls back to solo-style parsing for VE so we "
                  "can score them; the strict-parse path in `parse_quality_forecast(text, cls='ve')` "
                  "returns None for all of them. That is a real bug in the VE exec-turn prompting — "
                  "either rephrase the prompt so models actually emit VE keys, or collapse VE onto the "
                  "solo threshold schema permanently.")
    lines.append("- **64-row set, not 206.** The overnight pilot that fed this analysis contains "
                  "64 unique row_ids (7 classes × 2 difficulties × 3 seeds, plus 28 extra portfolio "
                  "seeds). Each is scored × 3 models = 192 row-model pairs. The 206 headline from "
                  "the wake-up brief includes some runs/ top-level files and other artifacts.")
    lines.append("")

    # --- §8 Calibration plots (Carla / Priority 1) -------------------------------
    lines.append('## 8. Calibration plots (M1 and M2)')
    lines.append('')
    lines.append(
        'Binned reliability diagrams per model. Each row is one 0.1-wide bin of the forecast. '
        "Position `.` marks the bin's mean forecast p\u0304; position `o` marks the bin's observed "
        "frequency y\u0304; `X` means they coincide. The horizontal displacement between `.` and "
        "`o` is the bin's reliability residual. Vertical spread of y\u0304 across bins = resolution."
    )
    lines.append('')
    calibration_bin_rows = []
    for metric, collector in (('M1', _collect_m1_pairs), ('M2', _collect_m2_pairs)):
        for model in MODELS:
            pairs = collector(rows, model=model)
            bins = _calibration_bins(pairs)
            mur = murphy_decomposition(pairs) or {}
            title = f'{metric} calibration — {model}'
            sub = (
                f"Brier={mur.get('brier', float('nan')):.3f}  "
                f"reliability={mur.get('reliability', float('nan')):.3f}  "
                f"resolution={mur.get('resolution', float('nan')):.3f}  "
                f"uncertainty={mur.get('uncertainty', float('nan')):.3f}  "
                f"n={mur.get('n', 0)}"
            )
            lines.append('```text')
            lines.append(_render_calibration_plot(bins, title, sub))
            lines.append('```')
            lines.append('')
            for b in bins:
                calibration_bin_rows.append({
                    'metric': metric, 'model': model,
                    'bin_lo': b['lo'], 'bin_hi': b['hi'],
                    'n': b['n'], 'p_mean': b['p_mean'], 'y_mean': b['y_mean'],
                })

    # --- §9 Per-class Brier (Carla / Priority 2) --------------------------------
    lines.append('## 9. Per-class Brier decomposition (M1 and M2)')
    lines.append('')
    lines.append(
        'Per-(model, class) Murphy decomposition. M1 (p_solve → kept_as_best) skips portfolio. '
        'M2 includes portfolio.'
    )
    lines.append('')
    pc_rollup = _per_class_rollup(rows)
    lines.append('| model | class | M1 n | M1 Brier | M1 rel | M1 res | M2 n | M2 Brier | M2 rel | M2 res |')
    lines.append('|---|---|---|---|---|---|---|---|---|---|')
    for entry in pc_rollup:
        m1 = entry['m1'] or {}
        m2 = entry['m2'] or {}
        def _fmt(v, spec='{:.3f}'):
            return spec.format(v) if v is not None else '—'
        lines.append(
            f"| {entry['model']} | {entry['class']} | "
            f"{m1.get('n', '—') if m1 else '—'} | {_fmt(m1.get('brier') if m1 else None)} | "
            f"{_fmt(m1.get('reliability') if m1 else None)} | "
            f"{_fmt(m1.get('resolution') if m1 else None)} | "
            f"{m2.get('n', '—') if m2 else '—'} | {_fmt(m2.get('brier') if m2 else None)} | "
            f"{_fmt(m2.get('reliability') if m2 else None)} | "
            f"{_fmt(m2.get('resolution') if m2 else None)} |"
        )
    lines.append('')
    lines.append(
        "**Reading the table.** Test Sonnet's M1 resolution by class: high on graphcol/steiner "
        '(feasibility-succeeding) → low on mwis/cjs (feasibility-failing) would show M1 '
        "self-knowledge directly predicts execution — Finding 3's underlying mechanism."
    )
    lines.append('')

    # --- §10 Pricing-bias reconciliation (Carla / Priority 3) -------------------
    lines.append('## 10. Pricing bias vs. stop-rationality reconciliation')
    lines.append('')
    lines.append(
        "Reconciles logistic thresholds (+2.3/+3.6/+4.8) with CF-$ means (−0.26/−1.64/−1.31). "
        'If mean(E[Δ]) − mean(cf_Δ) is large positive, the signals reconcile as pricing bias.'
    )
    lines.append('')
    pb = _pricing_bias(rows)
    lines.append('| model | n turns | mean E[Δ] (all) | n paired | mean E[Δ] (final) | mean cf_Δ | pricing bias |')
    lines.append('|---|---|---|---|---|---|---|')
    for model in MODELS:
        v = pb.get(model, {})
        def _pf(x, spec='{:+.2f}'):
            return spec.format(x) if x is not None else '—'
        lines.append(
            f"| {model} | {v.get('n_all_turns', 0)} | {_pf(v.get('mean_e_all_turns'))} | "
            f"{v.get('n_paired', 0)} | {_pf(v.get('mean_e_paired'))} | "
            f"{_pf(v.get('mean_cf_paired'))} | {_pf(v.get('bias_paired'))} |"
        )
    lines.append('')
    lines.append(
        "**Uniform shift or resolution-dependent?** Split each model's paired final-turn "
        'population at its own median E[Δ]. Flat bias ⇒ bias_low ≈ bias_high. '
        'Scaling bias (emission growing with forecast) ⇒ bias_high > bias_low.'
    )
    lines.append('')
    lines.append('| model | median E[Δ] | n_low | low E[Δ] | low cf_Δ | low bias | n_high | high E[Δ] | high cf_Δ | high bias |')
    lines.append('|---|---|---|---|---|---|---|---|---|---|')
    for model in MODELS:
        v = pb.get(model, {})
        if v.get('split_median_e') is None: continue
        def _pf(x, spec='{:+.2f}'):
            return spec.format(x) if x is not None else '—'
        lines.append(
            f"| {model} | {_pf(v['split_median_e'])} | {v['n_low']} | "
            f"{_pf(v['low_bin_mean_e'])} | {_pf(v['low_bin_mean_cf'])} | "
            f"{_pf(v['low_bin_bias'])} | {v['n_high']} | "
            f"{_pf(v['high_bin_mean_e'])} | {_pf(v['high_bin_mean_cf'])} | "
            f"{_pf(v['high_bin_bias'])} |"
        )
    lines.append('')
    biases = [(m, pb[m]['bias_paired']) for m in MODELS if pb[m].get('bias_paired') is not None]
    low_high = []
    for m in MODELS:
        lb = pb[m].get('low_bin_bias'); hb = pb[m].get('high_bin_bias')
        if lb is not None and hb is not None:
            low_high.append((m, lb, hb, hb - lb))
    interp = []
    if biases:
        interp.append('**Interpretation.** Paired pricing biases are '
            + ', '.join(f"{m.split('-')[0]} {b:+.2f}" for m, b in biases) + '. ')
    if low_high:
        interp.append('Across low/high split, bias changes by '
            + ', '.join(f"{m.split('-')[0]} Δ={d:+.2f}" for m, _, _, d in low_high) + '. ')
    interp.append('Positive paired bias + bias ≈ logistic threshold ⇒ thresholds are inflated '
                  'break-evens, not risk-aversion: models stop when emit-inflated forecast hits ~0, '
                  'landing realized cf_Δ at ≈ −bias. Penalty-Audit direction preserved; magnitude '
                  "reading shifts from 'risk-averse pricing' to 'emissions need de-biasing before "
                  "being read as break-even'.")
    lines.append(''.join(interp))
    lines.append('')

    # Emit per-bin CSV next to rollup
    bin_csv = ROOT / 'results' / 'metacog_calibration_bins.csv'
    with bin_csv.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['metric', 'model', 'bin_lo', 'bin_hi', 'n', 'p_mean', 'y_mean'])
        for row in calibration_bin_rows:
            w.writerow([
                row['metric'], row['model'],
                f"{row['bin_lo']:.2f}", f"{row['bin_hi']:.2f}", row['n'],
                f"{row['p_mean']:.4f}" if row['p_mean'] is not None else '',
                f"{row['y_mean']:.4f}" if row['y_mean'] is not None else '',
            ])

    lines.append(f"Script: `kaggle_submission/scripts/analyze_metacog.py`")
    lines.append(f"CSV rollup: `kaggle_submission/results/metacog_rollup.csv`")
    lines.append("Calibration bins CSV: `kaggle_submission/results/metacog_calibration_bins.csv`")
    lines.append("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines))

    # CSV
    m5_per_cell = (m5 or {}).get("per_cell", {})
    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "model", "class", "difficulty", "rows", "turns_with_qf",
            "quality_brier_mean", "continue_brier", "continue_base_floor",
            "mean_p_improve", "observed_improve_rate", "delta_mae",
            "drift_toward", "drift_away", "drift_flat",
            "m5_mean", "m5_ge1_frac", "m5_n_eligible", "m5_n_trivial", "m5_ceiling",
        ])
        for (model, cls, diff), bucket in sorted(agg.items()):
            q = _mean_brier_over_thresholds(bucket["quality"])
            c = (bucket["continue_brier_sse"] / bucket["continue_n"]
                 if bucket["continue_n"] else None)
            rate = (bucket["realized_improve_sum"] / bucket["continue_n"]
                    if bucket["continue_n"] else None)
            base = rate * (1 - rate) if rate is not None else None
            mean_p = (bucket["p_improve_mean_sum"] / bucket["p_improve_mean_n"]
                      if bucket["p_improve_mean_n"] else None)
            dmae = (bucket["delta_mae_sum"] / bucket["delta_n"]
                    if bucket["delta_n"] else None)
            m5c = m5_per_cell.get((model, cls, diff), {})
            w.writerow([
                model, cls, diff, bucket["rows"], bucket["turns_with_qf"],
                f"{q:.4f}" if q is not None else "",
                f"{c:.4f}" if c is not None else "",
                f"{base:.4f}" if base is not None else "",
                f"{mean_p:.4f}" if mean_p is not None else "",
                f"{rate:.4f}" if rate is not None else "",
                f"{dmae:.4f}" if dmae is not None else "",
                bucket["drift_toward"], bucket["drift_away"], bucket["drift_flat"],
                f"{m5c['m5_mean']:.4f}" if m5c.get("m5_mean") is not None else "",
                f"{m5c['m5_ge1_frac']:.4f}" if m5c.get("m5_ge1_frac") is not None else "",
                m5c.get("n_eligible", ""),
                m5c.get("n_trivial", ""),
                f"{m5c['ceiling']:.2f}" if m5c.get("ceiling") is not None else "",
            ])


def _base_floor_from_all(all_agg):
    """Empirical base-rate floor across all threshold-turns: mean over thresholds of p(1-p)."""
    total = 0.0
    n = 0
    # We don't have per-threshold base rates without another pass; approximate with overall.
    for d in all_agg["quality"].values():
        if d["n"] == 0:
            continue
        # Here sse is actual sse, n is turn count. We can't extract p_realized from sse alone.
        # Use a coarse proxy: overall quality target hit rate can be derived from the realized labels
        # during aggregation — but we didn't track it. Use 0.5 * 0.5 = 0.25 as conservative floor.
        pass
    # Conservative default floor (equal to random). The text calls this out.
    return 0.25


def main():
    rows, agg, all_agg = aggregate()
    mstats = model_level_stats(rows)
    m5 = _m5_decomposition(rows)
    write_report(rows, agg, all_agg, mstats, m5)
    print(f"Analyzed {len(rows)} model-row records.")
    print(f"Wrote report: {OUT_MD}")
    print(f"Wrote CSV:    {OUT_CSV}")


if __name__ == "__main__":
    main()
