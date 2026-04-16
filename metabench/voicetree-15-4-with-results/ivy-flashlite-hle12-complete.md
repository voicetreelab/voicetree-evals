---
color: green
isContextNode: false
agent_name: Ivy
---
# HCH HLE-12 v2 — Flash-Lite arm — 24/24 complete

Ran all 24 HCH HLE-12 v2 tasks on google/gemini-2.5-flash-lite. 2/24 passed (1 HCH, 1 Vanilla). Axis scores computed. Floor-tier reference point delivered.

## Model
`google/gemini-2.5-flash-lite` (discovered via `GET https://mp-staging.kaggle.net/models`)

## Run Results
| Q | Gold | HCH judge | Vanilla judge | n_sub | chose_decomp | p_correct HCH |
|---|------|-----------|---------------|-------|--------------|---------------|
| 41 | 46.24 | ❌ | ❌ | 0 | No | 0.98 |
| 43 | C | ❌ | ❌ | 0 | No | — |
| 44 | flag{no_zeros} | ❌ | ❌ | 0 | No | 0.90 |
| 48 | 5429515560378 | ✅ | ❌ | 0 | No | 1.00 |
| 49 | D | ❌ | ✅ | 5 | Yes | — |
| 52 | A | ❌ | ❌ | 0 | No | 0.85 |
| 53 | 0 | ❌ | ❌ | 3 | Yes | 0.95 |
| 55 | TC⁰ | ❌ | ❌ | 3 | Yes | 0.99 |
| 57 | C | ❌ | ❌ | 2 | Yes | 0.85 |
| 65 | D | ❌ | ❌ | 1 | No | 0.95 |
| 68 | B | ❌ | ❌ | 5 | Yes | 0.90 |
| 99 | dodecagon | ❌ | ❌ | 4 | Yes | 0.75 |

**HCH pass: 1/12 (8.3%) | Vanilla pass: 1/12 (8.3%)**

## Axis Scores
| Axis | Score | N valid | Interpretation |
|------|-------|---------|----------------|
| A1 atomic Brier | 0.679 | 5/12 | Severe overconfidence; p_correct ~0.90 but wrong 4/5 |
| A2 word MAPE | 5.957 | 12/12 | Extreme verbosity (Q43=10376w, Q49=7341w) |
| A3 decomp payoff | 0/6 | 6 chose decomp | Decomp never paid off; integration fails every time |
| B subtask Brier | 0.033 | 11 subs | Well-calibrated subtasks BUT only correct subs reported (upward bias) |
| C p_correct Brier | 0.737 | 10/12 | Extreme overconfidence; reports 0.75–0.99 on wrong answers |
| D pass rate | HCH=0.083, Van=0.083 | 12/12 | Identical floor; HCH adds no value at this tier |

## Key Setup Bug Found
Kaggle fresh kernels share session credentials via the pre-initialized `kbench.llm`. Evicting `kaggle_benchmarks` modules forces re-init with static `MODEL_PROXY_API_KEY` (IP-locked) → `PermissionDeniedError`. Fix: swap `kbench.llm.model` in-place without eviction. See `run_flashlite.py`.

## Files Changed

- kaggle/scripts/run_flashlite.py
- kaggle/.env.flashlite
- kaggle/results/hch_hle12_v2_flashlite_20260415_123434.jsonl
- kaggle/pilots/hch-hle12-v2-flashlite-2026-04-15.md

### NOTES

- The static MODEL_PROXY_API_KEY in kaggle/.env is IP-locked. Works only from the notebook that originally set up the session. Do NOT evict kaggle_benchmarks modules when running on dedicated kernels.
- Q43 and Q49 produce extreme output lengths (10k+ words) which pushes latency near the 90s timeout. Flash-Lite needs 120s task timeout for safety.
- All decomp cases: integration step fails (produces wrong/empty answer). All 6 decomp Qs failed. Q99 had all 4 subtasks correctly_solved=True but still got wrong final answer.
- Subtask B calibration 0.033 is misleadingly good — only subtasks the model explicitly reported as correct are counted. Subtasks with None outcome are majority.

[[task_17762548542193eb]]
