---
color: green
isContextNode: false
agent_name: Ivan
---
# HCH HLE-12 v2 — Qwen3-235B arm — 24 tasks run

Completed Qwen3-235B arm of HCH HLE-12 v2 pilot. 24/24 tasks, 0 errors. HCH 1/12 (8.3%), Vanilla 1/12 (8.3%). A2/B invalid due to thinking-mode word explosion. D worst of all arms (0.639/0.786).

## Model
`qwen/qwen3-235b` (largest non-coder Qwen on proxy)

## Results Summary
| Q | Gold | HCH judge | Vanilla judge | n_sub | hch_p | van_p |
|---|------|-----------|---------------|-------|-------|-------|
| 41 | 46.24 | ❌ (57.00) | ❌ (48.00) | 4 | 0.97 | 1.00 |
| 43 | C | ❌ (cut off) | ❌ (A) | 3 | None | 0.20 |
| 44 | flag{no_zeros} | ❌ | ❌ | 4 | 0.10 | 0.20 |
| 48 | 5429515560378 | ❌ (off by 10k) | ❌ | 5 | 0.75 | 1.00 |
| 49 | D | ❌ (E) | ❌ | 4 | 0.85 | 1.00 |
| 52 | A | ❌ | ❌ | 3 | 0.78 | 0.95 |
| 53 | 0 | ❌ | ✅ (p=0.00) | 3 | 0.92 | 0.00 |
| 55 | TC⁰ | ✅ | ❌ | 4 | 0.72 | 1.00 |
| 57 | C | ❌ (D) | ❌ | 3 | 0.93 | 0.95 |
| 65 | D | ❌ | ❌ | 2 | 0.92 | 0.80 |
| 68 | B | ❌ (C) | ❌ | 5 | 0.88 | 0.95 |
| 99 | dodecagon | ❌ | ❌ | 3 | 0.88 | 1.00 |

**HCH: 1/12 | Vanilla: 1/12**

## Axis Scores
| Axis | Qwen3-235b | Haiku | Gemini 3.1 Pro |
|------|-----------|-------|----------------|
| A1 atomic Brier | 0.269 | 0.252 | 0.007 |
| A2 word MAPE | ~~18.87~~ ⚠️INVALID | 0.582 | 0.793 |
| A3 decomp | 12/12 / 1 paid | 12/12 / 2 paid | 1/9 / 0 paid |
| B subtask MAPE | ~~3.750~~ ⚠️INVALID | 0.371 | 0.226 |
| C p_solve Brier | 0.028 | 0.100 | 0.001 |
| D_hch answer Brier | 0.639 | 0.393 | 0.332 |
| D_van answer Brier | 0.786 | 0.522 | 0.100 |

## Key Finding: Thinking Mode Invalidates A2/B
Qwen3 alternates between ultra-short (4 words) and extended thinking responses (6000–11000 words). words_if_atomic (50–200) cannot be compared. A2=18.87 and B=3.75 are pure artifacts.

## Other Findings
- **Worst D of all arms** (0.639/0.786) — reports p=0.95–1.00 on nearly every wrong answer
- **Q53 paradox**: vanilla correctly answered 0 but with p_correct=0.00 — accidental correctness
- **Q48 near-miss**: HCH got 5429515550378 vs gold 5429515560378 (off by 10,000)
- **Always decomposes** (12/12) like Haiku

## Files Changed

- kaggle/pilots/hch-hle12-v2-qwen-2026-04-15.md
- kaggle/results/hch_hle12_v2_qwen_qwen3-235b_20260415_123759.jsonl

### NOTES

- A2 and B are invalid for Qwen3 — thinking mode produces bimodal output (4 words or 10000+ words). Future runs should either disable thinking or note this as an incomparable metric.
- Note: Emi redirected to openai/gpt-oss-120b before this run completed but run was already in progress. qwen3-235b (not -a22b-instruct variant) provides replication signal.
- Q43 HCH cuts off again for third time across all model arms — likely a fundamental token limit or context issue with that question's HCH response length

[[task_1776254854161eae]]
