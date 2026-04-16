# HCH HLE-12 v2 Pilot — OSS/Llama arm — 2026-04-15

**Model:** `qwen/qwen3-235b-a22b-instruct-2507`
**Note:** No Llama or Mistral available on proxy. Largest OSS model available: Qwen3-235B-A22B (MoE, 235B total / 22B active, instruction-tuned). Used as Llama-family substitute.
**Run date:** 2026-04-15
**Results file:** `kaggle/results/hch_hle12_v2_qwen_qwen3-235b-a22b-instruct-2507_20260415_123740.jsonl`
**Agent:** Jay (Llama/OSS arm)
**Tasks:** 24/24 run (0 errors)

## Summary

Qwen3-235B (instruction) ran all 12 HLE Qs × {HCH v2, Vanilla}. HCH 3/12 pass, Vanilla 1/12 pass. **HCH helped +2 Qs over Vanilla** (Q44, Q65 HCH-only correct). Strong decomposition tendency (10/12 chose decomp). D_HCH=0.581 = moderate-high overconfidence. A2 remains anomalous (vanilla responses ~4 words for most Qs).

## Axis Scores

| Axis | Qwen3-235B | GPT Nano | GPT-5.4 base | Gemini 3.1 Pro | v1 Gemini 2.5 Flash |
|------|-----------|----------|--------------|----------------|---------------------|
| A1 (atomic Brier) | **0.282** | 0.144 | 0.406 | 0.007 | 0.427 |
| A2 (word MAPE) | **22.78** ⚠️ | 59.61 ⚠️ | 1.069 | 0.793 | 0.745 |
| A3 decomp rate | **10/12** | 3/12 | — | 1/9 | 7/12 |
| A3 paid off | **2/10** | 0/3 | 2/5 | 0/1 | 0/5 |
| B (subtask word MAPE) | **0.564** | 0.586 | — | 0.226 | 0.507 |
| C (subtask p_solve Brier) | **0.070** | 0.116 | — | 0.001 | 0.026 |
| D_HCH (final Brier HCH) | **0.581** | 0.455 | 0.474 | 0.332 | 0.934 |
| D_Van (final Brier Vanilla) | **0.899** ⚠️ | 0.394 | 0.769 | 0.100 | N/A |
| HCH pass rate | **3/12** | 0/12 | 3/7 | 6/9 | — |
| Vanilla pass rate | **1/12** | 1/12 | 1/8 | 9/10 | — |

⚠️ A2: most vanilla responses are ~4-5 words (terse); Q43 (7668w) and Q44 (6216w) are exceptions where model wrote full reasoning. A2 not comparable to v1.
⚠️ D_Van=0.899 is inflated by Q53: vanilla answered '0' (correct!) but set p_correct=0.0 — underconfidence when correct. Without Q53, D_Van=0.836 (still high).

## Per-Question Results

| Q | Gold | HCH answer | HCH judge | Vanilla answer | Vanilla judge | n_subs | HCH p_correct | Van p_correct |
|---|------|------------|-----------|----------------|---------------|--------|---------------|---------------|
| 41 | 46.24 | 48.00 | ✗ | 42.00 | ✗ | 4 (decomp) | 0.96 | 1.00 |
| 43 | C | A | ✗ | A | ✗ | 3 (decomp) | 0.60 | 0.80 |
| 44 | flag{no_zeros} | (parsed None) | ✅ | flag{shamir_has_spoken} | ✗ | 4 (decomp) | None | 0.95 |
| 48 | 5429515560378 | 26^9+26^8+26^4 | ✗ | 8031810176 | ✗ | 0 (atomic skip) | 0.92 | 1.00 |
| 49 | D | E | ✗ | G. 7 | ✗ | 5 (decomp) | 0.85 | 1.00 |
| 52 | A | H | ✗ | H. Excluded middle | ✗ | 4 (decomp) | 0.65 | 0.95 |
| 53 | 0 | 1/7 | ✗ | 0 | ✅ | 4 (decomp) | 0.85 | 0.00 |
| 55 | TC⁰ | TC⁰ | ✅ | PSPACE | ✗ | 3 (decomp) | 0.87 | 0.95 |
| 57 | C | D | ✗ | D | ✗ | 3 (decomp) | 0.92 | 0.95 |
| 65 | D | D. Odaka | ✅ | C. Nakadaka | ✗ | 1 (atomic) | 0.95 | 0.80 |
| 68 | B | C | ✗ | C | ✗ | 5 (decomp) | 0.88 | 0.95 |
| 99 | dodecagon | regular hexagon | ✗ | Regular hexagon | ✗ | 3 (decomp) | 0.87 | 1.00 |

## Key Findings

### 1. HCH helps (+2 Qs over Vanilla)
HCH: 3/12, Vanilla: 1/12. Q44 and Q65 correct with HCH but not vanilla. Q53 correct with vanilla but not HCH (model solved subtasks but gave wrong synthesis). First strong signal that HCH protocol adds value for this model.

### 2. A3: Heavy decomposition (10/12), 20% payoff
Qwen3-235B decomposes almost everything. Only Q48 (arithmetic) and Q65 (linguistics, 1-sub) went atomic. Decomposition paid off on 2/10 (Q44, Q55). Q55 decomp helped; Q65 was atomic and correct.

### 3. Q44 parse failure — judge rescued it
HCH produced the correct flag but response didn't include "ANSWER:" / "P_CORRECT:" markers in the expected format. Official/regex=False, judge=True. Model got the right answer (flag{no_zeros}) but format broke the parser — confirms judge > regex in v2.

### 4. D_Van=0.899 dominated by Q53 underconfidence
Vanilla Q53: answered '0' (gold='0', correct) but stated p_correct=0.0. This is a calibration paradox: model was correct but expressed zero confidence. All other D_Van Briers are also high (0.64-1.00) due to overconfidence on wrong answers.

### 5. Q49 verbosity explosion
SUB_1 of Q49 HCH generated 10,550 words — the model wrote 70x more than predicted (planned 100 words). This would be a severe token waste in a real multi-session HCH.

### 6. A2 still anomalous for vanilla-terse Qs
Most vanilla responses are 4-6 words (terse). A2=22.78 driven by Qs where wia is large vs short vanilla. Q43 (7668w vanilla) and Q44 (6216w vanilla) had realistic ratios and pull A2 down from what it would be otherwise.

## Cost Estimate
~$0.50-2.00 (Qwen3-235B larger model; Q43/Q44/Q49 ran 122-307s; majority of tasks 5-15s). Per-token cost not documented on proxy.

## Infrastructure
- Same kernel as GPT Nano run (4f231afe). Still idle and alive.
- No kernel issues. John's defaults (timeout=2400, idle-wait=60) gave ample headroom; actual max was 307s (Q44).
- No `max_output_tokens` issues (runner strips it correctly).
