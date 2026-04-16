---
color: green
isContextNode: false
agent_name: Ivy
---
# HCH HLE-12 v2 — DeepSeek R1-0528 arm — 24 tasks run

Ran all 24 HCH HLE-12 v2 tasks on deepseek-ai/deepseek-r1-0528. HCH=3/12 (25%), Vanilla=1/12 (8.3%). First model in suite where HCH beats vanilla (3×). All 6 axis values computed.

## Model
`deepseek-ai/deepseek-r1-0528` (reasoning model, strongest DeepSeek on proxy)

## Results
| Q | Gold | HCH official | Decomp | n_sub | p_correct | Van official |
|---|------|-------------|--------|-------|-----------|-------------|
| 41 | 46.24 | ✅ | Yes | 3 | 0.99 | ✅ |
| 43 | C | ❌ | Yes | 2 | 0.95 | ❌ |
| 44 | flag{no_zeros} | ❌ | Yes | 14 | 0.90 | ❌ |
| 48 | 5429515560378 | ❌ | Yes | 2 | 0.85 | ❌ |
| 49 | D | ✅ | Yes | 4 | 0.85 | ❌ |
| 52 | A | ❌ | Yes | 3 | 0.80 | ❌ |
| 53 | 0 | ❌ | No | 1 | 0.99 | ❌ |
| 55 | TC⁰ | ✅ | Yes | 3 | 0.85 | ❌ |
| 57 | C | ❌ | No | 1 | 0.80 | ❌ |
| 65 | D | ❌ | No | 1 | 0.95 | ❌ |
| 68 | B | ❌ | No | 1 | 0.95 | ❌ |
| 99 | dodecagon | ❌ | Yes | 3 | 0.90 | ❌ |

**HCH: 3/12 (25%) | Vanilla: 1/12 (8.3%) | HCH premium: 3×**

## Axis Scores
| Axis | Score | N valid |
|------|-------|---------|
| A1 atomic Brier | 0.856 | 4/12 |
| A2 word MAPE | 12.897 | 12/12 |
| A3 decomp payoff | 3/8 (37.5%) | 8 chose decomp |
| B subtask Brier | 0.013 | 38 subs |
| C p_correct Brier | 0.613 | 12/12 |
| D pass rate | HCH=0.250, Van=0.083 | 12/12 |

## Judge Bug
R1 wraps ALL responses in `<think>` blocks, breaking `_judge_answer().startswith("YES")`. `judge_pass` is always False. Used `official_pass` (regex) as primary signal throughout.

## Files Changed

- kaggle/scripts/run_deepseek.py
- kaggle/results/hch_hle12_v2_deepseek_20260415_125401.jsonl
- kaggle/pilots/hch-hle12-v2-deepseek-2026-04-15.md

### NOTES

- R1's <think> prefix breaks judge startswith(YES) check — judge_pass=False for all 24 tasks. Must use official_pass for R1 runs.
- Q68 gold may be wrong: R1's judge argues 'C' is correct for decreasing-domain modal logic, not 'B' (the gold). Worth reviewing the gold answer.
- Q44 over-decomposed into 14 subtasks (CTF crypto), took 212s — still failed.
- R1 B subtask Brier=0.013 is best in the entire suite so far. Chain-of-thought produces well-calibrated sub-task estimates.

[[task_17762548542193eb]]
