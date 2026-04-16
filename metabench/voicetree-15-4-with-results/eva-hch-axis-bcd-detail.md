---
color: green
isContextNode: false
agent_name: Eva
---
# Axis B/C/D detailed analysis — subtask calibration + overconfidence

B MAPE 0.516 raw / 0.507 clean (minimal Bug2 effect). C paradox: 23/24 subtasks 'solved' yet 0/8 Qs with all-solved-subs had correct final answer — C is internal consistency only. D Brier 0.934 fully robust: all 9 valid Qs have p_correct >= 0.90 on wrong answers.

### B — Subtask Word MAPE
- Contaminated: Q43 (Bug2), Q55 (Bug2), Q49 (0 subs), Q68 (0 subs)
- Raw mean MAPE: **0.516** (9 Qs with subtasks)
- Clean mean MAPE (excl. Q43,Q49,Q55,Q68): **0.507** (7 Qs)
- Bug2 contamination impact: **0.009** — minimal; Q43/Q55 happen to have near-median MAPEs
- N valid clean: 7/12

### C — Brier(p_solve/confidence, correctly_solved)
**C measures self-consistency, not calibration vs ground truth.**

| Metric | Raw (N=9 Qs) | Clean excl. Bug2 (N=7) |
|--------|-------------|------------------------|
| p_solve Brier | 0.038 | 0.002 |
| confidence Brier | 0.022 | 0.000 |

**The C Paradox (empirical):**
- 23/24 total subtasks marked correctly_solved=True
- 8/9 Qs with subtasks: ALL subtasks correctly_solved=True
- **0/8 of those Qs had correct final answers**
- Q43 is the sole exception: 3 subs=True, 1=False, final still wrong
- Model writes text → marks subtask "solved" → Brier ≈ 0
- Clean Brier ≈ 0.000 because Bug2 removal eliminates only case with correctly_solved=False
- **Fix required**: external judge to verify correctly_solved against gold

### D — Brier(P_CORRECT_hch, hch_correct)
- Parse-fail Qs (Q43, Q49, Q68): p_correct=None → excluded. N valid = **9/12**
- All 9 valid Qs: HCH wrong, p_correct ≥ 0.90

| Q | p_correct | Brier |
|---|-----------|-------|
| 41 | 1.000 | 1.000 |
| 44 | 1.000 | 1.000 |
| 48 | 0.902 | 0.815 |
| 52 | 0.980 | 0.960 |
| 53 | 1.000 | 1.000 |
| 55 | 0.900 | 0.810 |
| 57 | 0.950 | 0.902 |
| 65 | 1.000 | 1.000 |
| 99 | 0.960 | 0.922 |

- Mean Brier D: **0.934** (raw = clean)
- Min p_correct: 0.90 — **"catastrophically overconfident" label robust across entire valid distribution**
- Not a tail effect: 100% of valid Qs show p_correct ≥ 0.90 on wrong answers

detail [[eva-hch-analysis-overview]]
