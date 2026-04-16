---
color: green
isContextNode: false
agent_name: Jay
---
# HCH HLE-12 v2 — Qwen3-235B (OSS/Llama sub) arm — 24 tasks run

Ran 24 HCH HLE-12 v2 tasks with qwen/qwen3-235b-a22b-instruct-2507 (no Llama/Mistral on proxy; Qwen3-235B is largest OSS available). HCH 3/12 pass, Vanilla 1/12. HCH +2 over Vanilla. A3: 10/12 decomposed, 2/10 paid off. D_HCH=0.581.

## Model
`qwen/qwen3-235b-a22b-instruct-2507` — No Llama or Mistral on proxy. Qwen3-235B (MoE 235B total/22B active) is the largest/strongest OSS model available.

## Axis Scores

| Axis | Qwen3-235B | GPT Nano | GPT-5.4 | Gemini 3.1 Pro | v1 Flash |
|------|-----------|----------|---------|----------------|----------|
| A1 | 0.282 | 0.144 | 0.406 | 0.007 | 0.427 |
| A2 | 22.78 ⚠️ | 59.61 ⚠️ | 1.069 | 0.793 | 0.745 |
| A3 decomp | 10/12 | 3/12 | — | 1/9 | 7/12 |
| A3 paid off | 2/10 | 0/3 | 2/5 | 0/1 | 0/5 |
| B (sub MAPE) | 0.564 | 0.586 | — | 0.226 | 0.507 |
| C (p_solve) | 0.070 | 0.116 | — | 0.001 | 0.026 |
| D_HCH | 0.581 | 0.455 | 0.474 | 0.332 | 0.934 |
| D_Van | 0.899 ⚠️ | 0.394 | 0.769 | 0.100 | N/A |
| HCH pass | 3/12 | 0/12 | 3/7 | 6/9 | — |
| Vanilla pass | 1/12 | 1/12 | 1/8 | 9/10 | — |

## Key findings
- **HCH helps**: 3/12 vs 1/12 vanilla — first clear HCH advantage in this benchmark
- **Q44 parse failure**: model got flag{no_zeros} correct but no ANSWER:/P_CORRECT: markers; judge rescued it
- **Q49 verbosity**: SUB_1 wrote 10,550 words (planned 100) — 70× overshoot
- **D_Van=0.899** driven by Q53 underconfidence (correct answer, p_correct=0.0) + general overconfidence
- **A2 anomalous**: still dominated by vanilla terse responses

## Files Changed

- kaggle/results/hch_hle12_v2_qwen_qwen3-235b-a22b-instruct-2507_20260415_123740.jsonl
- kaggle/pilots/hch-hle12-v2-llama-2026-04-15.md

### NOTES

- No Llama or Mistral models on proxy. Available OSS: deepseek, gemma, qwen, gpt-oss. Chose Qwen3-235B as largest/most capable.
- Q44 HCH: p_correct=None (parse fail) excluded from D_HCH. Judge caught correct answer.
- D_Van=0.899 is inflated: Q53 vanilla p_correct=0.0 but was correct (underconfidence). Without Q53, D_Van=0.836.

[[task_1776254854272nzs]]
