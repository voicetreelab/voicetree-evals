---
color: green
isContextNode: false
agent_name: Eva
---
# Axis A1/A2/A3 detailed analysis — LaTeX + decomp bias

A1 Brier improves 0.537→0.427 with latex correction but severe miscalibration remains. A2 MAPE 0.745 unchanged (LaTeX < 2% effect). A3 decomp conclusion strengthened by latex: Q48 shows vanilla won where HCH failed.

### A1 — Brier(p_correct_if_atomic, vanilla_correct)
- Official vanilla_correct: False for all 12 (LaTeX parser failure)
- LaTeX-corrected ground truth: Q48 ✅, Q65 ✅, rest ❌
- Raw Brier: **0.537** | Clean Brier: **0.427** (diff driven by Q48: 0.360→0.160, Q65: 0.902→0.003)
- N valid: 10/12 (Q49, Q68 have no pcia data — protocol skip)
- **Even cleaned 0.427 shows severe miscalibration**
- Bias direction: INFLATED (official treats correct vanilla as wrong)

### A2 — MAPE(words_if_atomic, vanilla_word_count)
| Q | wia | vwc | ratio | MAPE |
|---|-----|-----|-------|------|
| 41 | 75 | 380 | 5.1× | 0.803 |
| 43 | 200 | 614 | 3.1× | 0.674 |
| 44 | 500 | 1401 | 2.8× | 0.643 |
| 48 | 180 | 441 | 2.5× | 0.592 |
| 52 | 150 | 932 | 6.2× | 0.839 |
| 53 | 250 | 464 | 1.9× | 0.461 |
| 55 | 50 | 529 | 10.6× | 0.905 |
| 57 | 150 | 656 | 4.4× | 0.771 |
| 65 | 1 | 201 | 201× | 0.995 |
| 99 | 70 | 298 | 4.3× | 0.765 |

- LaTeX boxing adds ~5-7 words to 201-1401 total: <2% inflation, not material
- Systematic bias: model UNDERESTIMATES words needed (median ratio 4.4×)
- Mean MAPE = **0.745** (same raw and clean)
- N valid: 10/12

### A3 — Decomposition Decision
Decomposed: Q41, Q43, Q48, Q52, Q55, Q57, Q99 (7/12). Contaminated: Q43, Q55.

| Q | Bug2? | HCH correct | Vanilla (latex) | Paid off? |
|---|-------|-------------|-----------------|----------|
| 41 | No | ❌ | ❌ | No |
| 43 | YES | ❌ | ❌ | Contaminated |
| 48 | No | ❌ | ✅ | **NEGATIVE** |
| 52 | No | ❌ | ❌ | No |
| 55 | YES | ❌ | ❌ | Contaminated |
| 57 | No | ❌ | ❌ | No |
| 99 | No | ❌ | ❌ | No |

**0/5 clean Qs paid off. Q48: decomp actively hurt (vanilla correct, HCH not). Finding robust.**

detail [[eva-hch-analysis-overview]]
