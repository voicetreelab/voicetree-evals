---
color: green
isContextNode: false
agent_name: Jay
---
# HCH HLE-12 v2 — GPT Nano arm — 24/24 complete

Ran all 24 HCH HLE-12 v2 tasks with openai/gpt-5.4-nano. 0/12 HCH pass, 1/12 Vanilla pass (Q68). A2=59.61 is anomalous (nano writes 4-word vanilla responses). D_HCH=0.455 shows moderate overconfidence. Infrastructure blocker: first kernel token was non-benchmark; user provided second correct token.

## Axis Scores

| Axis | GPT Nano | GPT-5.4 base | Gemini 3.1 Pro | v1 Gemini 2.5 Flash |
|------|----------|--------------|----------------|---------------------|
| A1 (atomic Brier) | **0.144** | 0.406 | 0.007 | 0.427 |
| A2 (word MAPE) | **59.61** ⚠️ | 1.069 | 0.793 | 0.745 |
| A3 decomp rate | **3/12** | — | 1/9 | 7/12 |
| A3 paid off | **0/3** | 2/5 | 0/1 | 0/5 |
| B (subtask word MAPE) | **0.586** | — | 0.226 | 0.507 |
| C (subtask p_solve Brier) | **0.116** | — | 0.001 | 0.026 |
| D_HCH (final Brier HCH) | **0.455** | 0.474 | 0.332 | 0.934 |
| D_Van (final Brier Vanilla) | **0.394** | 0.769 | 0.100 | N/A |
| HCH pass rate | **0/12** | 3/7 | 6/9 | — |
| Vanilla pass rate | **1/12** | 1/8 | 9/10 | — |

## Key Findings

**1. Floor confirmed** — 0/12 HCH pass. GPT Nano cannot solve HLE-level questions.

**2. A2 anomaly** — GPT Nano vanilla responses are 4 words ("ANSWER: X\nP_CORRECT: 0.3"). All other models wrote 200-1400 words. MAPE becomes 59.61 (dominated by Q44 wia=2500 vs vwc=4 → MAPE=624). This is a response-style artifact, not a real signal.

**3. Self-judge false negatives** — GPT Nano used as its own judge. Q52 vanilla: official=True (exact match 'A'='A') but judge=False. Actual vanilla pass rate ~2/12, not 1/12.

**4. Moderate D overconfidence** — D_HCH=0.455. Less extreme than v1 (0.934). Model shows some humility (Q44 p_correct=0.0, Q49 p_correct=0.15) vs blindly saying 0.9+.

**5. C paradox holds** — 9/12 HCH Qs had all subtasks correctly_solved=True, 0/9 had correct final answers.

## Cost
~$0.01-0.02 total. Fastest arm: vanilla tasks ~3s each, HCH ~10s avg.

## Files Changed

- kaggle/results/hch_hle12_v2_openai_gpt-5_4-nano_20260415_122245.jsonl
- kaggle/pilots/hch-hle12-v2-gptnano-2026-04-15.md
- kaggle/.env.gptnano

### NOTES

- First kernel token (query-param format) was from a plain Python notebook — kaggle_benchmarks not pre-installed. Required user to provide second benchmark-type token.
- A2=59.61 should be excluded from cross-model comparisons or noted as invalid for nano due to 4-word vanilla response style.
- Q52 vanilla: official=True but judge=False (GPT Nano self-judging exact match 'A'='A' incorrectly). True vanilla pass rate = 2/12.
- Axis label conflict: Ian's B=subtask p_solve Brier, my B=subtask word MAPE (v1 definition). Comparison table needs a footnote.

## Related

- [ian-hch-chatgpt-arm-complete](ian-hch-chatgpt-arm-complete.md)
- [gus-gemini3pro-hle12-complete](gus-gemini3pro-hle12-complete.md)

[[task_1776254854272nzs]]
