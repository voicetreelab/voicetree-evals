#!/usr/bin/env python3
"""
Score results.jsonl produced by hle_per_question.py against the Q41-100 key.

Auto-grading is intentionally strict but permissive on whitespace/case for MCQ.
For exactMatch, we do case-insensitive substring match in both directions as a
first pass — expect to manually audit borderline rows (prints "REVIEW" flag).
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

VAULT = Path(__file__).resolve().parents[1]
KEY = VAULT / "datasets" / "hle" / "hle_q41_100_answer_key.json"


def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip()).lower()


def grade_mcq(gold, pred):
    g = (gold or "").strip().upper()
    p = (pred or "").strip().upper()
    # Accept "B", "B.", "(B)", "Option B"
    m = re.search(r"\b([A-Z])\b", p)
    pl = m.group(1) if m else p
    return pl == g, False  # (correct, needs_review)


def grade_exact(gold, pred):
    g = norm(gold)
    p = norm(pred)
    if not p:
        return False, False
    if g == p:
        return True, False
    # tolerate numeric equivalence
    try:
        if abs(float(g) - float(p)) < 1e-6:
            return True, False
    except ValueError:
        pass
    # substring either way -> REVIEW
    if g in p or p in g:
        return True, True
    return False, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", type=Path, required=True)
    ap.add_argument("--key", type=Path, default=KEY)
    args = ap.parse_args()

    with open(args.key) as f:
        key = json.load(f)["questions"]

    rows = []
    with open(args.inp) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    per_arm = defaultdict(list)
    for r in rows:
        q = str(r["qnum"])
        if q not in key:
            continue
        gold = key[q]["answer"]
        qtype = key[q]["type"]
        pred = r.get("answer")
        p = r.get("p_correct")
        grader = grade_mcq if qtype == "multipleChoice" else grade_exact
        correct, review = grader(gold, pred)
        per_arm[r["arm"]].append({
            "qnum": r["qnum"], "gold": gold, "pred": pred, "type": qtype,
            "correct": correct, "review": review, "p_correct": p,
        })

    print(f"{'arm':<10} {'n':>4} {'acc':>8} {'brier':>8} {'review':>7}")
    for arm, items in per_arm.items():
        n = len(items)
        acc = sum(1 for i in items if i["correct"]) / n if n else 0
        briers = [
            ((1.0 if i["correct"] else 0.0) - (i["p_correct"] if i["p_correct"] is not None else 0.5)) ** 2
            for i in items
        ]
        brier = sum(briers) / len(briers) if briers else 0
        review = sum(1 for i in items if i["review"])
        print(f"{arm:<10} {n:>4} {acc:>8.3f} {brier:>8.3f} {review:>7}")

    print()
    print("Rows flagged REVIEW (auto-grade uncertain):")
    for arm, items in per_arm.items():
        for i in items:
            if i["review"]:
                status = "✓" if i["correct"] else "✗"
                print(f"  {arm:<8} Q{i['qnum']:<3} {status} gold={i['gold']!r} pred={i['pred']!r}")


if __name__ == "__main__":
    main()
