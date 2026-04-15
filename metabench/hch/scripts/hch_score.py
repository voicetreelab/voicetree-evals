#!/usr/bin/env python3
"""
Score an HCH in-context JSONL produced by hch_in_context.py.

Per-question report:
  - subtask count
  - mean p_solve (planned)
  - mean confidence (executed)
  - predicted vs actual tokens (per-subtask MAPE based on actual_chars proxy
    when the run-level usage block is unavailable; otherwise scales char
    fractions by total_tokens to estimate per-subtask actual tokens)
  - Brier of p_solve vs self-reported `solved`

Aggregate row at the bottom.

NOTE: end-to-end accuracy grading is intentionally NOT done here — the answer
key is encrypted. This script only reports HCH-primitive metrics that don't
require gold answers.
"""
import argparse
import json
from pathlib import Path
from statistics import mean


def safe_mean(xs):
    xs = [x for x in xs if x is not None]
    return mean(xs) if xs else None


def brier(predictions_outcomes):
    """predictions_outcomes: list of (p, outcome_bool). Returns mean Brier."""
    items = [(p, o) for p, o in predictions_outcomes
             if p is not None and o is not None]
    if not items:
        return None
    return sum((p - (1.0 if o else 0.0)) ** 2 for p, o in items) / len(items)


def per_sub_token_mape(subtasks, sub_execs, total_tokens, total_chars):
    """For each subtask with both an estimate and an executed actual_chars,
    compute |est - actual| / max(actual, 1).

    actual tokens estimate = total_tokens * (sub_chars / total_chars).
    Falls back to actual_chars/4 (rough chars-per-token proxy) if total_tokens
    unavailable.
    """
    if not subtasks or not sub_execs:
        return None
    ex_by_id = {e["id"]: e for e in sub_execs}
    errors = []
    chars_per_tok = 4.0  # crude default
    for s in subtasks:
        sid = s.get("id")
        est = s.get("token_estimate")
        ex = ex_by_id.get(sid)
        if est is None or ex is None or ex.get("actual_chars") in (None,):
            continue
        ac = ex["actual_chars"]
        if total_tokens and total_chars and total_chars > 0:
            actual_tok = total_tokens * (ac / total_chars)
        else:
            actual_tok = ac / chars_per_tok
        if actual_tok <= 0:
            continue
        errors.append(abs(est - actual_tok) / actual_tok)
    if not errors:
        return None
    return sum(errors) / len(errors)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", type=Path, required=True)
    args = ap.parse_args()

    rows = []
    with open(args.inp) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    print(f"{'qnum':>5} {'subs':>5} {'p_solvē':>9} {'conf̄':>7} "
          f"{'tok':>7} {'tokMAPE':>8} {'Brier':>7} {'p_corr':>7} {'rc':>4}")

    all_pred_outcomes = []
    all_mape = []
    for r in sorted(rows, key=lambda x: x.get("qnum", -1)):
        subs = r.get("subtasks") or []
        execs = r.get("sub_executions") or []
        n = len(subs)
        p_solve_mean = safe_mean([s.get("p_solve") for s in subs])
        conf_mean = safe_mean([e.get("confidence") for e in execs])
        total_chars = sum(
            (e.get("actual_chars") or 0) for e in execs
        )
        total_tokens = r.get("total_tokens")

        # Per-subtask Brier of p_solve vs self-reported solved
        pairs = []
        ex_by_id = {e["id"]: e for e in execs}
        for s in subs:
            sid = s.get("id")
            ex = ex_by_id.get(sid)
            if ex is None:
                continue
            pairs.append((s.get("p_solve"), ex.get("solved")))
        b = brier(pairs)
        all_pred_outcomes.extend(pairs)

        mape = per_sub_token_mape(subs, execs, total_tokens, total_chars)
        if mape is not None:
            all_mape.append(mape)

        p_corr = r.get("p_correct")
        cells = [
            f"{r.get('qnum'):>5}",
            f"{n:>5}",
            f"{p_solve_mean:>9.3f}" if p_solve_mean is not None else f"{'-':>9}",
            f"{conf_mean:>7.3f}" if conf_mean is not None else f"{'-':>7}",
            f"{(total_tokens or 0):>7}",
            f"{mape:>8.2f}" if mape is not None else f"{'-':>8}",
            f"{b:>7.3f}" if b is not None else f"{'-':>7}",
            f"{p_corr:>7.2f}" if p_corr is not None else f"{'-':>7}",
            f"{r.get('returncode'):>4}",
        ]
        print(" ".join(cells))

    print()
    overall_brier = brier(all_pred_outcomes)
    overall_mape = (sum(all_mape) / len(all_mape)) if all_mape else None
    print(f"Overall p_solve Brier (n={len(all_pred_outcomes)}): "
          f"{overall_brier if overall_brier is None else f'{overall_brier:.3f}'}")
    print(f"Overall token MAPE (n={len(all_mape)} questions): "
          f"{overall_mape if overall_mape is None else f'{overall_mape:.2f}'}")


if __name__ == "__main__":
    main()
