# HCH HLE-12 v2 — DeepSeek R1-0528 pilot (2026-04-15)

**Model:** `deepseek-ai/deepseek-r1-0528`
**Purpose:** Open-source reference arm. Strongest available DeepSeek via proxy. Reasoning model (chain-of-thought).

## Run metadata
- Date: 2026-04-15
- Tasks: 24 (12 HLE × {HCH v2, Vanilla})
- Kernel: Same dedicated Kaggle notebook as Flash-Lite arm (model swapped in-place)
- Results: `kaggle/results/hch_hle12_v2_deepseek_20260415_125401.jsonl`
- Task timeout: 2400s | idle-wait: 60s | sleep-between: 15s
- Runner: `kaggle/scripts/run_deepseek.py`

## Critical bug: R1 `<think>` prefix breaks judge `.startswith("YES")`
DeepSeek R1 wraps ALL responses in `<think>...</think>` blocks, including judge calls.
The `_judge_answer` function checks `response.startswith("YES")` — this fails for R1 since
the response starts with `<think>`. `judge_pass` is **always False** for this model.

**Primary correctness signal used**: `official_pass` (regex) from judge_notes.
This is reliable for standard answer formats; LaTeX bug is patched in v2.

## Raw results table

| Q | Gold | HCH official | HCH decomp | n_sub | p_correct | Vanilla official | Elapsed HCH |
|---|------|-------------|------------|-------|-----------|-----------------|-------------|
| 41 | 46.24 | ✅ | Yes | 3 | 0.99 | ✅ | 72s |
| 43 | C | ❌ | Yes | 2 | 0.95 | ❌ | 85s |
| 44 | flag{no_zeros} | ❌ | Yes | 14 | 0.90 | ❌ | 212s |
| 48 | 5429515560378 | ❌ | Yes | 2 | 0.85 | ❌ | 136s |
| 49 | D | ✅ | Yes | 4 | 0.85 | ❌ | 160s |
| 52 | A | ❌ | Yes | 3 | 0.80 | ❌ | 66s |
| 53 | 0 | ❌ | No | 1 | 0.99 | ❌ | 37s |
| 55 | TC⁰ | ✅ | Yes | 3 | 0.85 | ❌ | 44s |
| 57 | C | ❌ | No | 1 | 0.80 | ❌ | 41s |
| 65 | D | ❌ | No | 1 | 0.95 | ❌ | 29s |
| 68 | B | ❌ | No | 1 | 0.95 | ❌ | 38s |
| 99 | dodecagon | ❌ | Yes | 3 | 0.90 | ❌ | 83s |

**HCH official pass: 3/12 (25.0%) | Vanilla official pass: 1/12 (8.3%)**
**HCH premium: 3×**

## Axis scores (official_pass as primary)

| Axis | Score | N valid | Notes |
|------|-------|---------|-------|
| A1 atomic Brier | 0.856 | 4/12 | Only 4 Qs took atomic path; all wrong → high brier |
| A2 word MAPE | 12.897 | 12/12 | R1 `<think>` chains produce massive output (some 5000+ words) |
| A3 decomp payoff | 3/8 (37.5%) | 8 chose decomp | HCH works! Decomp Qs: 41,43,44,48,49,52,55,99 |
| B subtask Brier | 0.013 | 38 subs | Best calibration in suite — R1's p_solve very accurate |
| C p_correct Brier | 0.613 | 12/12 | Overconfident but less so than Flash-Lite (0.737) |
| D pass rate | HCH=0.250, Van=0.083 | 12/12 | **First model where HCH outperforms vanilla 3×** |

## Key findings

### 1. HCH shows positive effect for R1 (first in suite)
Flash-Lite: HCH=8.3% = Vanilla=8.3% (no benefit). R1: HCH=25% vs Vanilla=8.3% (3× benefit).
R1's strong reasoning capability lets it correctly execute the decompose-integrate pipeline.
Q41, Q49, Q55 all passed via HCH arm; only Q41 passed vanilla.

### 2. R1 heavily prefers decomposition (8/12 Qs)
R1 decomposed 8/12 questions, vs Flash-Lite 6/12. R1's chain-of-thought naturally produces
subtask structure. Q44 decomposed into 14 subtasks (CTF crypto challenge — over-decomposed).

### 3. Q44 over-decomposition (14 subtasks, 212s)
CTF challenge (find flag with no zeros) caused 14-subtask decomposition (3.5 min, longest task).
Still failed — R1 cannot solve the CTF crypto correctly via decomposition.

### 4. R1 judge challenges Q68 gold answer
For Q68 (modal logic, decreasing domains), R1's judge `<think>` block argues that the gold
answer "B" is incorrect and "C" (converse Barcan formula holds) is the right answer for
decreasing-domain Kripke semantics. This may be a gold answer error worth flagging.

### 5. Q99 "decagon" vs "dodecagon" (gold = dodecagon, both arms wrong)
Both HCH and Vanilla answered "regular decagon" (10 sides). Gold is "dodecagon" (12 sides).
R1 was consistently wrong on this geometry question.

### 6. Subtask calibration best in suite (B=0.013)
R1 provides extremely well-calibrated p_solve estimates for subtasks. All 38 reported subtasks
had known outcomes. This is a strong positive signal for the B axis.

## Comparison table

| Metric | Flash-Lite v2 | DeepSeek R1-0528 |
|--------|--------------|-----------------|
| D HCH pass | 0.083 (1/12) | **0.250 (3/12)** |
| D Van pass | 0.083 (1/12) | 0.083 (1/12) |
| HCH premium | 1× (no benefit) | **3× (clear benefit)** |
| A3 decomp payoff | 0/6 | 3/8 (37.5%) |
| B sub Brier | 0.033 | **0.013** |
| C Brier | 0.737 | 0.613 |
| Cost (est.) | ~$0.05–0.08 | ~$0.20–0.40 |
