---
color: green
isContextNode: false
agent_name: Emi
---
# HCH HLE-12 spike — end-to-end complete, MC-properties table delivered to Ben

Handover suborchestrator (Emi) completed. Eli ran 24/24 tasks; Eva produced noise-corrected axis analysis; final MC-properties table sent to Ben. 4 bugs surfaced, 3 high-ROI fixes identified.

## Outcome
24/24 HCH HLE-12 tasks executed. Full MC-properties analysis delivered to Ben.

## Final MC-Properties Table (noise-corrected)
| Axis | Raw | Clean | N valid | Validity |
|------|-----|-------|---------|----------|
| A1 atomic Brier | 0.537 | 0.427 | 10/12 | Partially valid |
| A2 word MAPE | 0.745 | 0.745 | 10/12 | Valid |
| A3 decomp decision | 0/7 paid off | 0/5 clean | 5/12 | Partially valid → robust |
| B subtask MAPE | 0.516 | 0.507 | 7/12 | Partially valid |
| C p_solve Brier | 0.038 | 0.002 | 9/12 | INVALID as calibration |
| D HCH Brier | 0.934 | 0.934 | 9/12 | Valid |

## Headline Findings
1. Vanilla beat HCH (LaTeX-corrected 2/12 vs 0/12) — decomposition never helped, Q48 shows it hurt
2. Axis D (0.934) = catastrophic overconfidence — most alarming, fully robust
3. Axis A2 (0.745 MAPE) = cleanest signal — word estimates 4.4× too low, uncontaminated
4. Axis C = design gap, not a finding — self-report measures consistency not calibration

## 3 High-ROI Fixes
1. Anti-LaTeX format instruction + parser extension (Bug 1) — biggest single measurement impact
2. Strengthen STEP 3 INTEGRATE constraint (Bug 2) — cuts HCH parse-fail 33%→~0%
3. External per-subtask judge (Axis C design gap) — makes C a real calibration axis

## Agent chain
Bob (suborch) → Eli (24-task runner) → Emi (handover suborch) → Eva (analysis worker) → Ben (parent, receives report)

## Files Changed

- kaggle/pilots/hch-hle12-2026-04-15.md
- kaggle/results/hch_hle12_run_20260415_072810.jsonl
- kaggle/examples/hch_hle12/q44_hch.py
- kaggle/examples/hch_hle12/q44_vanilla.py

### NOTES

- Axis C (0.026/0.038 Brier) looks like calibration success but is a design gap — correctly_solved is self-report only
- LaTeX boxing affects ALL vanilla answers — the 0/12 official vanilla score is a parser artifact, real accuracy is 2/12
- n=12 with single model/seed — statistically non-representative; findings are directional only
- Depth budget: Emi=3, Eli=2 (ran as child of Bob), Eva=2 (child of Emi)

[[task_1776238764431kq6]]
