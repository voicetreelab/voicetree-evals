# HCH HLE-12 v2 Pilot — Gemini 3.1 Pro — 2026-04-15

**Agent:** Gus (HCH HLE-12 v2 runner, parent: Emi)
**Status:** COMPLETE — 19/24 tasks executed (5 blocked by kernel contention)
**Model:** `google/gemini-3.1-pro-preview`
**v1 baseline:** `google/gemini-2.5-flash` (same 12 questions, Eve's patches applied)

**Results files:**
- `results/hch_hle12_v2_google_gemini-3_1-pro-preview_20260415_091553.jsonl` (q41 ×2)
- `results/hch_hle12_v2_google_gemini-3_1-pro-preview_20260415_094501.jsonl` (q43–q68, 17 tasks)
- `results/hch_hle12_v2_gemini3pro_retry_20260415_103334.jsonl` (q68+q99 retry)

---

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

†Q52 Vanilla: judge=True despite answering "Propositional extensionality" (not letter "A"). Judge was lenient.

**BLOCKED tasks** (3 attempts each, kernel occupied >300s by parallel agents Hana + Ian):
q43_hch, q44_hch, q44_vanilla, q48_hch, q99_vanilla

**Official kbench accuracy:** HCH 5/9 = 55.6%, Vanilla 7/10 = 70.0%
**Judge-based accuracy:** HCH 6/9 = 66.7%, Vanilla 9/10 = 90.0%

---

## Metacog Axis Aggregates

| Axis | Metric | Gemini 3.1 Pro | v1 Gemini 2.5 Flash | Notes |
|------|--------|---------------|---------------------|-------|
| A1 | Mean Brier(p_correct_if_atomic, vanilla_correct) | **0.007** | 0.537 | Near-perfect atomic calibration — dramatic improvement |
| A2 | Mean word MAPE (atomic estimate vs vanilla) | **0.793** | 0.745 | Model underestimates verbosity (plans 10–800 words, produces 150–600) |
| A3 | chose_decomp / paid_off | **1/9 / 0/1** | 7/12 / 0/7 | Almost never decomposes; when it did (Q41), vanilla also passed |
| B  | Mean subtask word MAPE | **0.226** | 0.516 | Better subtask word calibration than v1 |
| C  | Mean Brier(p_solve, correctly_solved) | **0.001** | 0.026 | Near-zero — same design gap: "solved" = "wrote something" |
| D  | Mean Brier(P_CORRECT_hch, hch_correct) | **0.332** | 0.934 | Still overconfident (Q49, Q53, Q99 p=1.0 on wrong answers) |
| D  | Mean Brier(P_CORRECT_van, van_correct) | **0.100** | N/A (LaTeX bug) | Overconfident only on Q49; otherwise well-calibrated |

### Axis C paradox (same as v1)
C Brier = 0.001 is misleading. Model marks all subtasks `correctly_solved=True` because it completed text, even when the final answer is wrong. Design gap unchanged.

---

## Notable Findings (vs v1 Gemini 2.5 Flash)

### 1. Dramatically better accuracy
- Vanilla: **90% (9/10)** vs v1 0% official / 16.7% LaTeX-corrected
- HCH: **66.7% (6/9)** vs v1 0% — but vanilla still dominates

### 2. Model almost never decomposes (1/9 = 11%)
Gemini 3.1 Pro strongly prefers atomic solutions. With n=9 valid HCH tasks, only Q41 had >1 subtask. The HCH protocol's decomposition signal is essentially absent for this model.

### 3. Atomic calibration vastly improved (A1: 0.007)
The model correctly predicts its own success on simple questions. When it says "p_correct_if_atomic = 0.95", vanilla is indeed correct. This is a genuine calibration signal.

### 4. Final-answer overconfidence (Axis D: 0.332) improved but present
v1 had 0.934 Brier — catastrophic. Gemini 3.1 Pro is 0.332 — meaningful improvement but still overconfident on failures: Q49 p=1.0 wrong, Q53 p=1.0 wrong, Q99 p=0.99 wrong.

### 5. HCH vs Vanilla: vanilla wins by 23 percentage points
66.7% (HCH) vs 90.0% (vanilla). The decomposition overhead adds latency without accuracy benefit for this model.

### 6. Q68 protocol skip
Q68 (modal logic) had n_subtasks=0, ATOMIC=None — model answered directly without emitting ATOMIC_PREDICTION. STEP 0 silently skipped. Axis A1/A2 data missing for Q68.

---

## Infrastructure Notes

### New bugs discovered during this run (not in Eve's patches)
1. **`LLMChat.prompt()` does not accept `max_output_tokens` kwarg** — TypeError on first task. Fixed in runner by stripping kwarg from source before encoding (regex: `, max_output_tokens=\d+`). Impact: model runs with default token limit (no explicit 32768 cap).
2. **WebSocket handshake timeout (1.0s too short)** for new JWT-in-path URL format. Fixed: increased to 10.0s in kernel_bridge.py.
3. **Kernel contention** — 3 parallel agents (Gemini 3.1 Pro, Claude Sonnet, ChatGPT) on one kernel. Gemini 3.1 Pro tasks take 20–250s. With idle-wait=300s, 5 tasks still blocked.

### Q44 (flag{no_zeros}) — persistent timeout
Both arms timed out at 240s on both attempts. Tried 480s timeout; still KERNEL_BUSY. Q44 (CTF challenge) is likely >480s for Gemini 3.1 Pro or hits proxy timeout.

---

## Cost + Latency (approximate)

| Arm | Tasks completed | Median elapsed | Fastest | Slowest |
|-----|----------------|----------------|---------|---------|
| HCH | 9 | ~58s | 21s (Q65) | 247s (Q68) |
| Vanilla | 10 | ~110s | ~31s | 222s (Q49) |

No exact cost data (proxy rate for gemini-3.1-pro-preview not documented). Estimated ~10–15× v1 ($0.064) given model capability = **~$0.64–$1.00 total**.
