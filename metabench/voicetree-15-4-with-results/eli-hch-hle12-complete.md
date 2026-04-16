---
color: green
isContextNode: false
agent_name: Eli
---
# HCH HLE-12 worker — 24/24 run, 4 bugs found, pilot note complete

All 24 tasks (12 HCH v2 + 12 Vanilla) executed via Option A bridge. Official: 0/12 both arms. LaTeX-corrected: Vanilla 2/12. 4 bugs surfaced. Metacog axis data collected. Pilot note written at kaggle/pilots/hch-hle12-2026-04-15.md.

## Run Summary
| Arm | Tasks | Official pass | LaTeX-corrected pass | Cost | Elapsed |
|-----|-------|--------------|---------------------|------|---------|
| HCH | 12 | 0/12 (0%) | 0/12 (0%) | ~$0.037 | 587s |
| Vanilla | 12 | 0/12 (0%) | 2/12 (16.7%) | ~$0.027 | 528s |
| Total | 24 | 0/24 | 2/24 | ~$0.064 | ~18.6 min |

## Metacog Axes
| Axis | Value |
|------|-------|
| A1 (atomic p_correct Brier) | 0.537 |
| A2 (atomic word MAPE) | 0.745 |
| A3 decomp paid off | 0/7 |
| B subtask word MAPE | 0.516 |
| C p_solve Brier | 0.026 |
| D HCH final Brier | 0.934 |

## 4 Bugs
1. **LaTeX boxing** (vanilla ALL, HCH 4/12): `$\boxed{X}$` defeats ANSWER: parser — fix: explicit format instruction
2. **HCH protocol drift** (Q43,Q49,Q55,Q68): model drops PLAN/EXECUTE on long Qs — fix: stronger INTEGRATE instruction
3. **f-string NameError Q44** (`flag{no_zeros}` → `{no_zeros}` evaluated): fixed → `flag{{no_zeros}}`
4. **Protocol skip** (Q49,Q68): no SUBTASKS/SUB blocks at all on complex Qs

## Files Changed

- kaggle/examples/hch_hle12/q44_hch.py
- kaggle/examples/hch_hle12/q44_vanilla.py
- kaggle/pilots/hch-hle12-2026-04-15.md
- kaggle/results/hch_hle12_run_20260415_072810.jsonl

### NOTES

- Format non-compliance (LaTeX boxing) is the primary measurement blocker for vanilla arm — ALL 12 vanilla answers parsed as None. Same bug as MetaCoach pilot.
- HCH arm: 4/12 also had parse failures (Q43, Q49, Q55, Q68) on complex long-form questions
- Axis C (0.026 Brier) looks great but is misleading: model marks subtasks solved=True for completing text, not for answer correctness
- Q44 f-string bug: flag{no_zeros} in f-string caused NameError — fixed to flag{{no_zeros}}. Re-ran successfully.
- Decomposition never paid off (A3: 0/7) and model is catastrophically overconfident (Axis D HCH Brier=0.934)
- LaTeX-aware extraction from run.json: vanilla got Q48 and Q65 correct (correct answers embedded in boxed notation)

[[task_1776236551225qja]]
