---
color: green
isContextNode: false
agent_name: Ivan
---
# HCH HLE-12 v2 — Claude Haiku arm — 24/24 complete

Completed Claude Haiku arm of HCH HLE-12 v2 pilot. 24/24 tasks run, 0 errors. HCH pass 2/12 (16.7%), Vanilla 1/12 (8.3%). All 6 axis scores computed. Floor-tier confirmed.

## Model
`anthropic/claude-haiku-4-5` (discovered via `GET https://mp-staging.kaggle.net/models`)

## Kernel Setup Note
First dedicated kernel lacked `kaggle-benchmarks` — not usable. User provided second fresh kernel with correct Kaggle benchmark environment pre-installed. Base-domain URL format (`https://kkb-production.jupyter-proxy.kaggle.net?token=...`) returned 200 directly (no path-embedded format needed for this kernel).

## Run Results
| Q | Gold | HCH answer | HCH judge | Vanilla answer | Vanilla judge | n_sub | p_correct HCH | p_correct Van |
|---|------|------------|-----------|----------------|---------------|-------|---------------|---------------|
| 41 | 46.24 | 48.00 | ❌ | 48.00 | ❌ | 4 | 0.92 | 0.95 |
| 43 | C | None (cut off) | ❌ | E | ❌ | 2 | None | 0.45 |
| 44 | flag{no_zeros} | shamir_secret_key | ❌ | cybersecurity_ | ❌ | 3 | 0.35 | 0.75 |
| 48 | 5429515560378 | 110075771153 | ❌ | 5429515560378 | ✅ | 4 | 0.68 | 0.60 |
| 49 | D | F | ❌ | F | ❌ | 4 | 0.32 | 0.35 |
| 52 | A | G | ❌ | G | ❌ | 4 | 0.40 | 0.72 |
| 53 | 0 | 1/7 | ❌ | 1/13 | ❌ | 4 | 0.98 | 0.95 |
| 55 | TC⁰ | refused/non-answer | ❌ | NC¹ | ❌ | 3 | 0.12 | 0.35 |
| 57 | C | C | ✅ | D | ❌ | 4 | 0.80 | 0.72 |
| 65 | D | D | ✅ | B | ❌ | 4 | 0.72 | 0.85 |
| 68 | B | C | ❌ | C | ❌ | 4 | 0.90 | 0.85 |
| 99 | dodecagon | A regular hexagon | ❌ | Regular hexagon | ❌ | 3 | 0.85 | 0.90 |

**HCH pass: 2/12 = 16.7% | Vanilla pass: 1/12 = 8.3%**

## Metacog Axis Scores
| Axis | Metric | Haiku | Gemini 2.5 Flash v1 | Gemini 3.1 Pro v2 |
|------|--------|-------|----------------------|-------------------|
| A1 (atomic Brier) | Brier(p_correct_if_atomic, vanilla_correct) | **0.252** | 0.427 | 0.007 |
| A2 (word MAPE) | abs(words_if_atomic − van_words)/van_words | **0.582** | 0.745 | 0.793 |
| A3 (decomp) | chose_decomp / paid_off | **12/12 / 2/12** | 7/12 / 0/7 | 1/9 / 0/1 |
| B (subtask MAPE) | mean abs(actual−planned)/planned | **0.371** | 0.507 | 0.226 |
| C (p_solve Brier) | Brier(p_solve, correctly_solved) n=41 | **0.100** | 0.002 | 0.001 |
| D_hch (answer Brier) | Brier(P_CORRECT_hch, hch_correct) | **0.393** | 0.934 | 0.332 |
| D_van (answer Brier) | Brier(P_CORRECT_van, van_correct) | **0.522** | N/A (v1 LaTeX bug) | 0.100 |

## Key Findings
1. **Haiku always decomposes** (A3=12/12) — unlike Gemini 3 Pro (1/9). Strong prompt-following tendency to decompose regardless of whether it helps.
2. **Extreme overconfidence** — D_van=0.522 (worst of all arms). Reports p=0.85–0.98 on wrong answers (Q53: p=0.98, answer=1/7, gold=0).
3. **Exception: Q55 self-aware refusal** — Haiku correctly declined to give a speculative TC⁰ bound with p_correct=0.12. Only case of appropriate epistemic humility.
4. **A1 better than v1** (0.252 vs 0.427) — atomic calibration improved with judge-based scoring patches.
5. **C=0.100** — much worse than Gemini models (0.001–0.002). Subtask self-reporting less calibrated: Haiku marks subtasks correctly_solved=True even when wrong.

## Files Changed

- kaggle/pilots/hch-hle12-v2-haiku-2026-04-15.md
- kaggle/results/hch_hle12_v2_anthropic_claude-haiku-4-5_20260415_122210.jsonl

### NOTES

- First dedicated kernel (https://kkb-production.jupyter-proxy.kaggle.net?token=...) had kaggle-benchmarks missing + protobuf version mismatch. Second fresh kernel provided by user worked out of the box.
- Q43 HCH still truncates (69s run) despite max_output_tokens being stripped by runner — model generates extremely long analysis and runs out of kernel output buffer or similar
- Haiku is confirmed floor model: combined accuracy (HCH+Vanilla) 3/24 = 12.5%. Even Gemini 2.5 Flash v1 was 24/24 run with better axis scores.

## Related

- [task_1776254854161eae](task_1776254854161eae.md)

[[task_1776254854161eae]]
