---
color: green
isContextNode: false
agent_name: Eva
---
# HCH HLE-12 analysis — noise-corrected axis scores + failure patterns

Rigorous noise-separation of 4 bugs from valid signal. Clean MC-properties table computed from 24-task JSONL. Bug contamination map and fix recommendations produced.

## Clean MC-Properties Table

| Axis | Raw score | Clean score | N valid | Bias direction | Valid? |
|------|-----------|-------------|---------|----------------|--------|
| A1 (atomic Brier) | 0.537 | 0.427 | 10/12 | INFLATED — LaTeX bug marks correct vanilla as wrong | Partially valid |
| A2 (word MAPE) | 0.745 | 0.745 | 10/12 | Unaffected — LaTeX <2% word inflation | Valid |
| A3 (decomp decision) | 0/7 paid off | 0/5 clean | 5/12 clean | Q43,Q55 contaminated; conclusion unchanged | Partially valid → robust |
| B (subtask MAPE) | 0.516 | 0.507 | 7/12 | Minimal (0.016 diff after excl. Bug2 Qs) | Partially valid |
| C (p_solve Brier) | p=0.038, c=0.022 | p=0.002, c=0.000 | 9/12 | DESIGN GAP — self-report only | Invalid as calibration |
| D (final Brier) | 0.934 | 0.934 | 9/12 | Unaffected; parse-fail excluded | Valid |

## Bug Contamination Map

| Bug | Qs | Axes contaminated |
|-----|----|-------------------|
| Bug 1: LaTeX boxing (all vanilla) | All 12 vanilla | A1 (ground truth wrong), A3 (ground truth wrong) |
| Bug 2: HCH protocol drift | Q43,Q49,Q55,Q68 | A3 (2 Qs), B (2 Qs skewed), C (2 Qs skewed) |
| Bug 4: Protocol skip (subset of Bug 2) | Q49,Q68 | A1,A2 (no pcia/wia), B,C (no subtasks) |
| Bug 3: Q44 f-string NameError | Q44 | None — fixed before run |

## One-Line Verdicts

- **A1**: Partially valid — LaTeX inflates Brier 0.537→0.427; still shows severe miscalibration
- **A2**: Valid — vanilla word count unaffected; systematic 4.4× underestimate is real signal
- **A3**: Partially valid → robust — 0/5 clean Qs paid off; Q48 shows decomp HURT
- **B**: Partially valid — 0.516 raw / 0.507 clean; minimal contamination effect
- **C**: Invalid as calibration — measures self-consistency only (model says solved = wrote text)
- **D**: Valid — catastrophic overconfidence (all p≥0.90 on wrong Qs) is genuine signal

[[task_1776240439278gmt]]
