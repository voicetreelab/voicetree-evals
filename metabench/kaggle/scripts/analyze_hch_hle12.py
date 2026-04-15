#!/usr/bin/env python3
"""Analyze HCH HLE-12 run results and compute all 6 metacog axes.

Usage (from kaggle/ directory):
  python scripts/analyze_hch_hle12.py results/hch_hle12_run_*.jsonl

Reads one or more .jsonl result files (produced by run_hch_hle12.py) and:
  - Parses per-Q HCH + vanilla judge notes
  - Computes all 6 metacog axes (A1, A2, A3, B, C, D)
  - Prints per-Q table and per-axis aggregates
  - Optionally writes the pilot note to pilots/hch-hle12-2026-04-15.md
"""

import json
import re
import sys
from pathlib import Path

PILOT_NOTE_PATH = Path(__file__).resolve().parents[1] / "pilots" / "hch-hle12-2026-04-15.md"

QNUMS = [41, 43, 44, 48, 49, 52, 53, 55, 57, 65, 68, 99]

# ── Note parsers ─────────────────────────────────────────────────────────────

_ATOMIC_NOTE_RE = re.compile(
    r"ATOMIC: words_if_atomic=(\S+), p_correct_if_atomic=(\S+)"
)
_DECOMP_NOTE_RE = re.compile(
    r"DECOMP: n_subtasks=(\d+), chose_decomp=(True|False)"
)
_SUB_NOTE_RE = re.compile(
    r"SUB_(\d+): p_solve=(\S+), words_to_produce=(\S+), "
    r"correctly_solved=(\S+), confidence=(\S+), actual_words=(\S+)"
)
_AXISD_HCH_RE = re.compile(
    r"Axis D Q\d+ HCH: answer=(.+?), p_correct=(\S+), correct=(\S+), gold="
)
_VANILLA_NOTE_RE = re.compile(
    r"Vanilla Q\d+: answer=(.+?), p_correct=(\S+), correct=(\S+), gold=\S+, word_count=(\d+)"
)


def _float_or_none(s):
    if s in (None, "None", "none", ""):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _bool_or_none(s):
    if s in (None, "None"):
        return None
    if isinstance(s, bool):
        return s
    if isinstance(s, str):
        if s.lower() == "true":
            return True
        if s.lower() == "false":
            return False
    return None


def parse_hch_notes(notes):
    """Extract structured data from HCH task judge notes."""
    atomic = {"words_if_atomic": None, "p_correct_if_atomic": None}
    decomp = {"n_subtasks": None, "chose_decomp": None}
    subs = []
    axis_d = {"answer": None, "p_correct": None, "correct": None}

    for note in (notes or []):
        m = _ATOMIC_NOTE_RE.search(note)
        if m:
            atomic["words_if_atomic"] = _float_or_none(m.group(1))
            atomic["p_correct_if_atomic"] = _float_or_none(m.group(2))

        m = _DECOMP_NOTE_RE.search(note)
        if m:
            decomp["n_subtasks"] = int(m.group(1))
            decomp["chose_decomp"] = m.group(2) == "True"

        m = _SUB_NOTE_RE.search(note)
        if m:
            subs.append({
                "sid": int(m.group(1)),
                "p_solve": _float_or_none(m.group(2)),
                "words_to_produce": _float_or_none(m.group(3)),
                "correctly_solved": _bool_or_none(m.group(4)),
                "confidence": _float_or_none(m.group(5)),
                "actual_words": _float_or_none(m.group(6)),
            })

        m = _AXISD_HCH_RE.search(note)
        if m:
            axis_d["answer"] = m.group(1).strip("'\"")
            axis_d["p_correct"] = _float_or_none(m.group(2))
            axis_d["correct"] = _bool_or_none(m.group(3))

    return {"atomic": atomic, "decomp": decomp, "subs": subs, "axis_d": axis_d}


def parse_vanilla_notes(notes):
    """Extract structured data from vanilla task judge notes."""
    result = {"answer": None, "p_correct": None, "correct": None, "word_count": None}
    for note in (notes or []):
        m = _VANILLA_NOTE_RE.search(note)
        if m:
            result["answer"] = m.group(1).strip("'\"")
            result["p_correct"] = _float_or_none(m.group(2))
            result["correct"] = _bool_or_none(m.group(3))
            result["word_count"] = int(m.group(4))
    return result


def brier(p, actual):
    """Brier score: (p - actual)^2. Lower = better calibration."""
    if p is None or actual is None:
        return None
    return (p - (1.0 if actual else 0.0)) ** 2


def load_results(paths):
    """Load all jsonl result files into a dict keyed by task_name."""
    results = {}
    for path in paths:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    name = r.get("task_name") or r.get("task_file", "").replace(".py", "")
                    if name:
                        results[name] = r
                except Exception:
                    pass
    return results


def compute_axes(qnum, hch_result, vanilla_result):
    """Compute all 6 metacog axes for one question."""
    hch_notes = parse_hch_notes(hch_result.get("judge_notes") or [])
    van_notes = parse_vanilla_notes(vanilla_result.get("judge_notes") or [])

    hch_correct = hch_result.get("passed")
    van_correct = vanilla_result.get("passed")

    atomic = hch_notes["atomic"]
    decomp = hch_notes["decomp"]
    subs = hch_notes["subs"]

    # Axis A1: Brier(p_correct_if_atomic, vanilla_actual_correct)
    a1 = brier(atomic["p_correct_if_atomic"], van_correct)

    # Axis A2: |words_if_atomic - vanilla_word_count| / max(1, vanilla_word_count)
    wia = atomic["words_if_atomic"]
    vwc = van_notes.get("word_count")
    a2 = abs(wia - vwc) / max(1, vwc) if (wia is not None and vwc is not None) else None

    # Axis A3: decompose decision quality
    chose_decomp = decomp.get("chose_decomp")
    decomp_paid_off = (hch_correct and not van_correct) if (
        hch_correct is not None and van_correct is not None
    ) else None

    # Axis B: per-subtask word MAPE
    b_maes = []
    for sub in subs:
        w_pred = sub.get("words_to_produce")
        w_act = sub.get("actual_words")
        if w_pred is not None and w_act is not None:
            b_maes.append(abs(w_pred - w_act) / max(1, w_act))
    axis_b_mape = (sum(b_maes) / len(b_maes)) if b_maes else None

    # Axis C: per-subtask Brier (p_solve + confidence)
    c_p_solve_briers = []
    c_conf_briers = []
    for sub in subs:
        cs = sub.get("correctly_solved")
        p_s = sub.get("p_solve")
        conf = sub.get("confidence")
        if p_s is not None and cs is not None:
            c_p_solve_briers.append(brier(p_s, cs))
        if conf is not None and cs is not None:
            c_conf_briers.append(brier(conf, cs))
    axis_c_p_solve = (
        sum(c_p_solve_briers) / len(c_p_solve_briers) if c_p_solve_briers else None
    )
    axis_c_conf = (
        sum(c_conf_briers) / len(c_conf_briers) if c_conf_briers else None
    )

    # Axis D: final answer calibration
    hch_p_correct = hch_notes["axis_d"]["p_correct"] or (
        hch_result.get("judge_notes") and None
    )
    # Also try to read p_correct from HCH notes directly if axis_d parse failed
    if hch_p_correct is None:
        for note in (hch_result.get("judge_notes") or []):
            m = re.search(r"p_correct=([\d.]+)", note)
            if m:
                hch_p_correct = float(m.group(1))
                break
    van_p_correct = van_notes.get("p_correct")

    axis_d_hch = brier(hch_p_correct, hch_correct)
    axis_d_van = brier(van_p_correct, van_correct)

    return {
        "qnum": qnum,
        "hch_correct": hch_correct,
        "van_correct": van_correct,
        "hch_answer": hch_notes["axis_d"].get("answer"),
        "van_answer": van_notes.get("answer"),
        "n_subtasks": decomp.get("n_subtasks"),
        "chose_decomp": chose_decomp,
        "decomp_paid_off": decomp_paid_off,
        "words_if_atomic": atomic.get("words_if_atomic"),
        "p_correct_if_atomic": atomic.get("p_correct_if_atomic"),
        "van_word_count": vwc,
        "hch_p_correct": hch_p_correct,
        "van_p_correct": van_p_correct,
        "axis_a1": a1,
        "axis_a2": a2,
        "axis_a3_chose_decomp": chose_decomp,
        "axis_a3_paid_off": decomp_paid_off,
        "axis_b_mape": axis_b_mape,
        "axis_c_p_solve_brier": axis_c_p_solve,
        "axis_c_conf_brier": axis_c_conf,
        "axis_d_hch_brier": axis_d_hch,
        "axis_d_van_brier": axis_d_van,
        "subs": subs,
    }


def fmt(v, decimals=3):
    if v is None:
        return "None"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:.{decimals}f}"
    return str(v)


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_hch_hle12.py results/hch_hle12_run_*.jsonl", file=sys.stderr)
        return 1

    paths = [Path(p) for p in sys.argv[1:]]
    results = load_results(paths)
    print(f"[analyze] loaded {len(results)} task results", file=sys.stderr)

    rows = []
    for qnum in QNUMS:
        hch_key = f"hch_hle12_q{qnum}_hch"
        van_key = f"hch_hle12_q{qnum}_vanilla"
        hch_r = results.get(hch_key, {})
        van_r = results.get(van_key, {})
        if not hch_r and not van_r:
            print(f"[analyze] Q{qnum}: no results found", file=sys.stderr)
            rows.append({"qnum": qnum, "missing": True})
            continue
        axes = compute_axes(qnum, hch_r, van_r)
        rows.append(axes)

    # ── Per-Q table ──────────────────────────────────────────────────────────
    print("\n## Per-Q Results\n")
    headers = [
        "Q", "gold", "hch_ans", "hch_ok", "van_ans", "van_ok",
        "n_sub", "decomp", "A1_brier", "A2_mape", "B_mape", "C_brier", "D_hch", "D_van"
    ]
    # Gold answers for display
    GOLDS = {41:"46.24",43:"C",44:"flag{no_zeros}",48:"5429515560378",49:"D",
              52:"A",53:"0",55:"TC⁰",57:"C",65:"D",68:"B",99:"dodecagon"}

    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["-" * max(3, len(h)) for h in headers]) + "|")
    for row in rows:
        qnum = row["qnum"]
        if row.get("missing"):
            print(f"| {qnum} | — | MISSING | — | MISSING | — | — | — | — | — | — | — | — | — |")
            continue
        gold = GOLDS.get(qnum, "?")
        print(
            f"| {qnum} | {gold} "
            f"| {(row['hch_answer'] or '?')[:12]} "
            f"| {fmt(row['hch_correct'])} "
            f"| {(row['van_answer'] or '?')[:12]} "
            f"| {fmt(row['van_correct'])} "
            f"| {row['n_subtasks']} "
            f"| {fmt(row['chose_decomp'])} "
            f"| {fmt(row['axis_a1'])} "
            f"| {fmt(row['axis_a2'])} "
            f"| {fmt(row['axis_b_mape'])} "
            f"| {fmt(row['axis_c_p_solve_brier'])} "
            f"| {fmt(row['axis_d_hch_brier'])} "
            f"| {fmt(row['axis_d_van_brier'])} |"
        )

    # ── Aggregate axes ────────────────────────────────────────────────────────
    complete = [r for r in rows if not r.get("missing")]
    print("\n## Aggregate Axes (mean over complete questions)\n")

    def mean(vals):
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else None

    a1s = [r["axis_a1"] for r in complete]
    a2s = [r["axis_a2"] for r in complete]
    b_mapes = [r["axis_b_mape"] for r in complete]
    c_p_solve = [r["axis_c_p_solve_brier"] for r in complete]
    c_conf = [r["axis_c_conf_brier"] for r in complete]
    d_hch = [r["axis_d_hch_brier"] for r in complete]
    d_van = [r["axis_d_van_brier"] for r in complete]

    print(f"Axis A1 (atomic p_correct Brier, lower=better): {fmt(mean(a1s))}")
    print(f"Axis A2 (atomic word MAPE, lower=better):        {fmt(mean(a2s))}")
    chose_decomp_qs = [r for r in complete if r["chose_decomp"]]
    paid_off = [r for r in chose_decomp_qs if r["decomp_paid_off"]]
    print(f"Axis A3 (decompose decisions): chose_decomp={len(chose_decomp_qs)}/{len(complete)}, "
          f"paid_off={len(paid_off)}/{len(chose_decomp_qs) or 1}")
    print(f"Axis B  (subtask word MAPE, lower=better):       {fmt(mean(b_mapes))}")
    print(f"Axis C  (p_solve Brier, lower=better):           {fmt(mean(c_p_solve))}")
    print(f"Axis C  (confidence Brier, lower=better):        {fmt(mean(c_conf))}")
    print(f"Axis D  HCH (p_correct Brier, lower=better):    {fmt(mean(d_hch))}")
    print(f"Axis D  Vanilla (p_correct Brier, lower=better): {fmt(mean(d_van))}")

    # ── Headline findings ─────────────────────────────────────────────────────
    hch_acc = mean([1.0 if r.get("hch_correct") else 0.0 for r in complete])
    van_acc = mean([1.0 if r.get("van_correct") else 0.0 for r in complete])
    print(f"\n## Headline Findings\n")
    print(f"HCH accuracy:     {hch_acc:.1%} ({sum(1 for r in complete if r['hch_correct'])}/{len(complete)})")
    print(f"Vanilla accuracy: {van_acc:.1%} ({sum(1 for r in complete if r['van_correct'])}/{len(complete)})")
    print(f"HCH beat vanilla: {hch_acc > van_acc}")
    print(f"Mean Axis A1 Brier (atomic p_correct): {fmt(mean(a1s))} (0=perfect, 1=worst)")
    print(f"Mean Axis D HCH Brier (final p_correct): {fmt(mean(d_hch))}")
    print(f"Mean Axis D Van Brier (final p_correct): {fmt(mean(d_van))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
