# HCH HLE-12 v2 Pilot — GPT Nano arm — 2026-04-15

**Model:** `openai/gpt-5.4-nano`
**Run date:** 2026-04-15
**Results file:** `kaggle/results/hch_hle12_v2_openai_gpt-5_4-nano_20260415_122245.jsonl`
**Agent:** Jay (GPT Nano arm worker)
**Tasks:** 24/24 run (0 errors)

## Summary

GPT Nano ran all 12 HLE Qs × {HCH v2, Vanilla}. HCH 0/12 pass, Vanilla 1/12 pass (Q68 judge). Model outputs are extremely terse (vanilla ~4 words), which makes A2 (word MAPE) anomalously large. D_HCH=0.455 shows moderate overconfidence — less extreme than v1 Gemini 2.5 Flash (0.934) but still overconfident.

## Setup notes

Initial dedicated kernel token pointed to a plain Python Kaggle notebook (no `kaggle_benchmarks`). User provided a second token from the benchmark notebook, which worked. Env saved to `kaggle/.env.gptnano`.

## Axis Scores

| Axis | GPT Nano | GPT-5.4 base | Gemini 3.1 Pro | v1 Gemini 2.5 Flash |
|------|----------|--------------|----------------|---------------------|
| A1 (atomic Brier) | **0.144** | 0.406 | 0.007 | 0.427 |
| A2 (word MAPE) | **59.61** ⚠️ | 1.069 | 0.793 | 0.745 |
| A3 decomp rate | **3/12** | — | 1/9 | 7/12 |
| A3 decomp paid off | **0/3** | 2/5 | 0/1 | 0/5 |
| B (subtask word MAPE) | **0.586** | 0.063† | 0.226 | 0.507 |
| C (subtask p_solve Brier) | **0.116** | — | 0.001 | 0.026 |
| D_HCH (final Brier HCH) | **0.455** | 0.474† | 0.332 | 0.934 |
| D_Van (final Brier Vanilla) | **0.394** | 0.769† | 0.100 | N/A |
| HCH pass rate | **0/12** | 3/7 | 6/9 | — |
| Vanilla pass rate | **1/12** | 1/8 | 9/10 | — |

† Ian's axis labels differ: his B=subtask p_solve Brier, his C=final p_correct Brier. Cross-reference carefully.
⚠️ A2 is extreme because GPT Nano's vanilla responses are ~4 words (terse style); v1 models wrote 200-1400 words.

## Per-Question Results

| Q | Gold | HCH answer | HCH judge | Vanilla answer | Vanilla judge | n_subs | HCH p_correct | Van p_correct |
|---|------|------------|-----------|----------------|---------------|--------|---------------|---------------|
| 41 | 46.24 | 48.00 | ✗ | 69.16 | ✗ | 1 (atomic) | 0.88 | 1.00 |
| 43 | C | E | ✗ | E | ✗ | 2 (decomp) | 0.40 | 0.83 |
| 44 | flag{no_zeros} | krjvekdavc}kfi | ✗ | flag{shamir_secret_sharing} | ✗ | 2 (decomp) | 0.86 | 0.00 |
| 48 | 5429515560378 | 5429503679432 | ✗ | 5.556e+17 | ✗ | 1 (atomic) | 0.55 | 0.90 |
| 49 | D | H | ✗ | J | ✗ | 1 (atomic) | 0.15 | 0.58 |
| 52 | A | D. Uniqueness... | ✗ | A | ✗† | 1 (atomic) | 0.66 | 0.20 |
| 53 | 0 | 1/13 | ✗ | 1/6 | ✗ | 1 (atomic) | 0.97 | 0.17 |
| 55 | TC⁰ | P/poly | ✗ | Unknown/Not specified | ✗ | 1 (atomic) | 0.25 | 0.00 |
| 57 | C | D | ✗ | D | ✗ | 1 (atomic) | 0.74 | 0.78 |
| 65 | D | A. Heiban | ✗ | B | ✗ | 1 (atomic) | 0.75 | 0.92 |
| 68 | B | C | ✗ | B | ✅ | 1 (atomic) | 0.78 | 0.74 |
| 99 | dodecagon | A regular decagon | ✗ | regular hexagon | ✗ | 3 (decomp) | 0.55 | 0.55 |

†Q52 vanilla: official=True (exact match 'A'='A') but judge=False — GPT Nano judge false negative. Actual vanilla correct=True for Q52.

## Key Findings

### 1. Near-zero accuracy (0/12 HCH, 1/12 Vanilla)
GPT Nano cannot solve any HLE-level question. This confirms the floor reference point: HLE is far above GPT Nano's capability.

### 2. A2 anomaly — nano's terse vanilla style
GPT Nano vanilla responses are ~4 words ("ANSWER: X\nP_CORRECT: 0.3"). All other models in this benchmark wrote 200-1400 word responses. This makes A2 = 59.61 (vs 0.745 for v1). A2 is effectively meaningless for nano: the model predicts 1-2500 words for atomic work but produces 4-word answers. This is a response-style artifact, not miscalibration.

### 3. Self-judging creates false negatives
Q52 vanilla: gold='A', answer='A', official=True, judge=False. GPT Nano as judge cannot correctly assess its own (simple!) exact match. This means judge pass rate is slightly underreported (1/12 official vanilla vs true ~2/12).

### 4. Moderate D overconfidence (0.455 HCH, 0.394 Vanilla)
GPT Nano is less catastrophically overconfident than v1 Gemini 2.5 Flash (D=0.934). It still says 0.55-0.97 for wrong answers, but also says 0.0 for Q44 (self-aware it can't do crypto CTF). Some humility visible in p_correct.

### 5. C paradox holds
9/12 HCH tasks had all subtasks marked correctly_solved=True. None of those 9 had correct final answers. GPT Nano marks subtasks "solved" regardless of actual correctness.

### 6. Decomp rate low (3/12), never paid off
GPT Nano rarely decomposes (3/12 = 25%) vs v1 Gemini Flash (7/12 = 58%). None of the 3 decompositions produced correct answers.

## Cost Estimate
~$0.01-0.02 total (GPT Nano is extremely cheap; 24 tasks × ~1500 avg tokens × ~$0.15/1M input = ~$0.005 input, similar for output). Fastest runner: vanilla tasks ~3s each.

## Infrastructure notes
- First kernel token (query-param format) was from a plain Python notebook — no `kaggle_benchmarks` pre-installed. Required user to provide a second benchmark-type notebook token.
- No `max_output_tokens` issues — runner regex strips it correctly.
- No kernel contention (dedicated kernel, sole user).
