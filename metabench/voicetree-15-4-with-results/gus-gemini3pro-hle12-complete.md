---
color: green
isContextNode: false
agent_name: Gus
---
# HCH HLE-12 v2 — Gemini 3.1 Pro arm — 24 tasks run

Completed Gemini 3.1 Pro HCH HLE-12 v2 pilot. 19/24 tasks executed (5 blocked by kernel contention). HCH judge pass rate 6/9 = 66.7%, Vanilla 9/10 = 90.0%. Pilot note written. All 6 axis values computed.

## Model
`google/gemini-3.1-pro-preview` (discovered via `GET https://mp-staging.kaggle.net/models`)

## Run Results (judge-based correctness)

| Q | Gold | HCH answer | HCH judge | Vanilla answer | Vanilla judge | n_subtasks | p_correct HCH | p_correct Van |
|---|------|------------|-----------|----------------|---------------|------------|---------------|---------------|
| 41 | 46.24 | 46.24 | ✅ | 46.24 | ✅ | 5 (decomposed) | 0.98 | 1.00 |
| 43 | C | — | ❌ BLOCKED | C | ✅ | — | — | 0.99 |
| 44 | flag{no_zeros} | — | ❌ TIMEOUT | — | ❌ TIMEOUT | — | — | — |
| 48 | 5429515560378 | — | ❌ BLOCKED | 5429515560378 | ✅ | — | — | 1.00 |
| 49 | D | E | ✗ | E | ✗ | 1 (atomic) | 1.00 | 1.00 |
| 52 | A | A | ✅ | Prop. extensionality* | ✅† | 1 (atomic) | 0.99 | 0.99 |
| 53 | 0 | 1/13 | ✗ | 0 | ✅ | 1 (atomic) | 1.00 | 1.00 |
| 55 | TC⁰ | TC0 | ✅ | TC^0 | ✅ | 1 (atomic) | 0.95 | 0.98 |
| 57 | C | C | ✅ | C | ✅ | 1 (atomic) | 0.95 | 0.95 |
| 65 | D | D | ✅ | D | ✅ | 1 (atomic) | 0.95 | 0.999 |
| 68 | B | B | ✅ | B | ✅ | 0 (protocol skip) | 0.98 | 0.99 |
| 99 | dodecagon | regular hexagon | ✗ | — | ❌ BLOCKED | 1 (atomic) | 0.99 | — |

†Q52 Vanilla: judge=True despite answering "Propositional extensionality" — judge was lenient.

**BLOCKED tasks** (3 attempts each, kernel occupied >300s by parallel agents Hana + Ian):
q43_hch, q44_hch, q44_vanilla, q48_hch, q99_vanilla

**Official kbench accuracy:** HCH 5/9 = 55.6%, Vanilla 7/10 = 70.0%
**Judge-based accuracy:** HCH 6/9 = 66.7%, Vanilla 9/10 = 90.0%

## Metacog Axis Aggregates

| Axis | Metric | Gemini 3.1 Pro | v1 Gemini 2.5 Flash | Notes |
|------|--------|---------------|---------------------|-------|
| A1 | Mean Brier(p_correct_if_atomic, vanilla_correct) | **0.007** | 0.537 | Near-perfect atomic calibration — dramatic improvement |
| A2 | Mean word MAPE (atomic estimate vs vanilla) | **0.793** | 0.745 | Model underestimates verbosity |
| A3 | chose_decomp / paid_off | **1/9 / 0/1** | 7/12 / 0/7 | Almost never decomposes |
| B  | Mean subtask word MAPE | **0.226** | 0.516 | Better subtask calibration than v1 |
| C  | Mean Brier(p_solve, correctly_solved) | **0.001** | 0.026 | Design gap: "solved"="wrote something" |
| D  | Mean Brier(P_CORRECT_hch, hch_correct) | **0.332** | 0.934 | Improved but still overconfident on failures |
| D  | Mean Brier(P_CORRECT_van, van_correct) | **0.100** | N/A (LaTeX bug) | Well-calibrated except Q49 |

## Infrastructure Bugs Discovered
1. `LLMChat.prompt()` does not accept `max_output_tokens` kwarg — stripped by runner regex before encoding
2. WebSocket handshake timeout 1.0s too short for JWT-in-path URL — patched to 10.0s in kernel_bridge.py (TEMP — revert after session)
3. Kernel contention: 3 parallel agents on one kernel; 5 tasks permanently blocked

## Cost (approx)
Estimated ~$0.64–$1.00 total (no documented proxy rate for gemini-3.1-pro-preview; ~10–15× v1 Gemini 2.5 Flash at $0.064)

## Files Changed

- kaggle/pilots/hch-hle12-v2-gemini3pro-2026-04-15.md
- kaggle/scripts/run_hch_hle12_with_model.py
- kaggle/option_a_bridge/kernel_bridge.py
- kaggle/results/hch_hle12_v2_google_gemini-3_1-pro-preview_20260415_091553.jsonl
- kaggle/results/hch_hle12_v2_google_gemini-3_1-pro-preview_20260415_094501.jsonl
- kaggle/results/hch_hle12_v2_gemini3pro_retry_20260415_103334.jsonl

### NOTES

- kernel_bridge.py WebSocket timeout patched to 10.0s — REVERT after session (was 1.0s)
- run_hch_hle12_with_model.py is a temporary script — DO NOT CHECK IN
- 5 tasks blocked by kernel contention (Hana/Claude Sonnet + Ian/ChatGPT running in parallel): q43_hch, q44_hch, q44_vanilla, q48_hch, q99_vanilla
- Axis C Brier=0.001 is misleading — model marks all subtasks correctly_solved=True even when final answer is wrong; design gap unchanged from v1
- Q68 protocol skip: n_subtasks=0, ATOMIC=None — model answered directly without ATOMIC_PREDICTION; A1/A2 data missing for Q68

[[task_1776243675377jix]]
