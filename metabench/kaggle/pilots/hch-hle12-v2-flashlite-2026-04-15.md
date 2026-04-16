# HCH HLE-12 v2 — Gemini Flash-Lite pilot (2026-04-15)

**Model:** `google/gemini-2.5-flash-lite`
**Purpose:** Floor/weak-tier reference in Gemini family. One tier below v1's gemini-2.5-flash. Capability curve lower bound.

## Run metadata
- Date: 2026-04-15
- Tasks: 24 (12 HLE questions × {HCH v2, Vanilla} arms)
- Kernel: Dedicated Kaggle notebook (fresh session, session credentials)
- Results file: `kaggle/results/hch_hle12_v2_flashlite_20260415_123434.jsonl`
- Task timeout: 90s (sufficient for most Qs; Q43/Q44/Q49/Q68 were close or hit limit)
- Runner: `kaggle/scripts/run_flashlite.py`

## Setup notes (for future runners)
- Fresh Kaggle notebooks do NOT have `kaggle_benchmarks` pre-installed; if they do, they likely
  lack the SESSION credentials — the static `MODEL_PROXY_API_KEY` in `.env` is IP-locked and
  only works from specific notebooks.
- **Correct approach**: restart kernel to fresh state, then swap `kbench.llm.model` in-place
  on the notebook-initialized `llm` object. Do NOT evict `kaggle_benchmarks` modules.
- `?token=` URL format (old-style) returned 200 but a different notebook was actually used.

## Raw results table

| Q | Gold | HCH answer | HCH judge | Vanilla answer | Vanilla judge | n_sub | chose_decomp | p_correct HCH |
|---|------|------------|-----------|----------------|---------------|-------|--------------|---------------|
| 41 | 46.24 | 60.00 | ❌ | None | ❌ | 0 | No | 0.98 |
| 43 | C | None | ❌ | None | ❌ | 0 | No | — |
| 44 | flag{no_zeros} | ksmiiy_s_fgnwz | ❌ | kbqgcwueksld_o | ❌ | 0 | No | 0.90 |
| 48 | 5429515560378 | 5429515560378 | ✅ | 5437547370554 | ❌ | 0 | No | 1.00 |
| 49 | D | None | ❌ | None | ✅ | 5 | Yes | — |
| 52 | A | B | ❌ | None | ❌ | 0 | No | 0.85 |
| 53 | 0 | 1/13 | ❌ | None | ❌ | 3 | Yes | 0.95 |
| 55 | TC⁰ | (verbose) | ❌ | P | ❌ | 3 | Yes | 0.99 |
| 57 | C | D | ❌ | None | ❌ | 2 | Yes | 0.85 |
| 65 | D | C | ❌ | None | ❌ | 1 | No | 0.95 |
| 68 | B | C | ❌ | None | ❌ | 5 | Yes | 0.90 |
| 99 | dodecagon | A regular hexagon | ❌ | triangle | ❌ | 4 | Yes | 0.75 |

**HCH pass: 1/12 (8.3%) | Vanilla pass: 1/12 (8.3%)**

## Axis scores

| Axis | Score | N valid | Notes |
|------|-------|---------|-------|
| A1 atomic Brier | 0.679 | 5/12 | Severely inflated — model reports p_correct ~0.90 but atomic path wrong 4/5 times |
| A2 word MAPE | 5.957 | 12/12 | Severe verbosity — Q43 = 10376 words, Q49 = 7341. Many Qs produce 10× expected length |
| A3 decomp payoff | 0/6 | 6/12 chose decomp | Decomposition never helped. Atomic arm passed 1/6. No net benefit from HCH. |
| B subtask Brier | 0.033 | 11 subs reported | Well-calibrated on subtask p_solve, BUT only correctly-resolved subtasks reported (upward bias) |
| C p_correct Brier | 0.737 | 10/12 | Extremely overconfident. Reports 0.75–0.99 across all Qs, correct only 1/10 times |
| D pass rate | HCH=0.083, Van=0.083 | 12/12 | Identical floor performance. HCH adds no value at this capability level. |

## Notable findings

### 1. Q43 + Q49 extreme verbosity
Q43 vanilla = 10,376 words; Q49 vanilla = 7,341 words. Flash-Lite produces very long responses
on multi-choice reasoning Qs. This inflates word MAPE dramatically. Also pushed task latency to
65-67s (close to 90s timeout). Consider 120s timeout for Flash-Lite.

### 2. HCH decomp pattern
6/12 Qs chose decomp (same rate as v1 flash). But ALL 6 failed at integration — the model
decomposes correctly but the integration step produces wrong or empty answers. This is consistent
with the weakness being integration, not decomposition.

### 3. Subtask partial reporting
Many decomp tasks report only the first subtask result (sub_0 or sub_1 have ok=True) and then
None for subsequent subtasks. This means integration was attempted partway and failed. Only Q99
has all 4 subtasks reporting ok=True but still failed the final answer.

### 4. Overconfidence (A1 + C)
Flash-Lite reports p_correct = 0.75–0.99 on almost all wrong answers. The model has no
uncertainty signal even for very hard HLE questions. This is characteristic of a weaker model
that cannot distinguish easy from hard questions.

### 5. Cost estimate
~$0.05–0.08 for 24 tasks with Flash-Lite (estimated; token counts not captured by bridge).
Significantly cheaper than Flash, Pro, or Sonnet arms.

## Comparison vs v1 Flash (reference)
| Metric | Flash-Lite v2 | Flash v1 |
|--------|--------------|----------|
| D (HCH pass) | 0.083 | 0.083* |
| D (Van pass) | 0.083 | 0.083* |
| A1 Brier | 0.679 | 0.427 (clean) |
| C Brier | 0.737 | 0.022 (clean)* |

*v1 had noise from 4 bugs; clean v2 Flash not yet run with all patches. Flash-Lite shows floor.
