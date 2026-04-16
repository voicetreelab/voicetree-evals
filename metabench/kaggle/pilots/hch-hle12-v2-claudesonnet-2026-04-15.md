# HCH HLE-12 v2 Pilot — Claude Sonnet — 2026-04-15

**Agent:** Hana (HCH HLE-12 v2 runner, Claude Sonnet arm; parent: Emi)
**Status:** COMPLETE — 23/24 tasks executed (q44_hch timed out at 1800s)
**Model:** `anthropic/claude-sonnet-4-6`
**Results files:**
- `results/hch_hle12_v2_anthropic_claude-sonnet-4-6_20260415_102239.jsonl` (q41 pair)
- `results/hch_hle12_v2_anthropic_claude-sonnet-4-6_20260415_115135.jsonl` (q43–q99)

---

## Run Results

| Q | Gold | HCH answer | HCH pass | Vanilla answer | Vanilla pass | n_subtasks | p_correct HCH | p_correct Van |
|---|------|------------|----------|----------------|--------------|------------|--------------|--------------|
| 41 | 46.24 | '46.24 inches' | ✅ | '45.00 inches' | ❌ | 4 | 0.72 | 0.45 |
| 43 | C | 'D' | ❌ | 'D' | ❌ | 2 | 0.72 | 0.45 |
| 44 | flag{no_zeros} | TIMEOUT (>30 min) | — | 'secret_sharing}' | ❌ | — | — | 0.10 |
| 48 | 5429515560378 | '5429515560378' | ✅ | '5429515560378' | ✅ | 1 | 0.72 | 0.60 |
| 49 | D | 'E' | ❌ | 'D' | ✅ | 2 | 0.82 | 0.25 |
| 52 | A | 'E' | ❌ | 'E' | ❌ | 1 | 0.30 | 0.35 |
| 53 | 0 | '1/13' | ❌ | '1/13' | ❌ | 2 | 0.97 | 0.85 |
| 55 | TC⁰ | 'TC^0' | ✅ | 'TC⁰' | ✅ | 1 | 0.75 | 0.55 |
| 57 | C | 'D' | ❌ | 'D' | ❌ | 1 | 0.78 | 0.62 |
| 65 | D | 'D. Odaka' | ✅ | 'D' | ✅ | 1 | 0.72 | 0.72 |
| 68 | B | 'C' | ❌ | 'C' | ❌ | 1 | 0.88 | 0.72 |
| 99 | dodecagon | 'regular hexagon' | ❌ | 'Regular hexagon' | ❌ | 2 | 0.78 | 0.72 |

**HCH judge pass rate: 4/11 = 36.4%** (q44 timed out — no data)
**Vanilla judge pass rate: 4/12 = 33.3%**

---

## Metacog Axis Aggregates

| Axis | Metric | Claude Sonnet | v1 Gemini Flash (clean) | Delta |
|------|--------|--------------|------------------------|-------|
| A1 | Brier(p_correct_if_atomic, van_correct) | **0.353** | 0.427 | −0.074 ✅ |
| A2 | Word MAPE (atomic est. vs vanilla actual) | **0.524** | 0.745 | −0.221 ✅ |
| A3 | chose_decomp / paid_off | **5/11 / 1/5** | 7/12 / 0/5 | 1 payoff |
| B  | Subtask word MAPE | **0.527** | 0.507 | +0.020 ≈ |
| C  | Brier(p_solve, self-reported solved) | **0.065** | 0.022 | design gap (same issue) |
| D  | Brier(P_CORRECT_hch, hch_correct) | **0.410** | 0.934 | −0.524 ✅✅ |
| D  | Brier(P_CORRECT_van, van_correct) | **0.307** | N/A (v1 parse fail) | — |

### Notable findings

**1. Axis D dramatically improved (0.410 vs 0.934)**
Claude Sonnet is far better calibrated than Gemini Flash. Still meaningfully miscalibrated — overconfident on wrong answers (q53: p=0.97 but wrong, q68: p=0.88 but wrong).

**2. Axis A2 improved (0.524 vs 0.745)**
Better word-count self-estimation, but still off by 0.5× on average.

**3. Axis C still a design gap (0.065)**
All subtasks self-report `correctly_solved=True` except q52 SUB1. Self-completion ≠ correctness. Needs external verification to be valid.

**4. Q43/Q49 runaway generation**
Without `max_output_tokens`, first subtask of q43 produced 11,592 words (11.5 min), q49 produced 9,982 words (6 min). This is a fundamental issue with HCH v2 without token caps.

**5. Q44 CTF problem — intractable for HCH**
`flag{no_zeros}` requires executable code + decompilation. Claude Sonnet's HCH decomposition ran for >30 min before timing out. Vanilla arm also failed (answered 'secret_sharing}'). This question may need a code-execution tool to be answerable.

**6. A3: First decomp payoff**
Q41 (genetics height calculation) was decomposed into 4 subtasks and passed — the only case where decomp paid off across all v1+v2 runs.

---

## Cost + Latency

| Arm | Tasks ran | Notable latency | Status |
|-----|-----------|-----------------|--------|
| HCH | 11/12 | q43=687s, q49=368s, q44=DNF(>1800s) | q44 timeout |
| Vanilla | 12/12 | all <35s except q48=20s | complete |

Estimated cost: ~$0.08–0.12 (Claude Sonnet pricing; no token breakdown available from proxy response)

---

## Operational notes

- **Token expiry:** First attempt blocked (session expired). Required kernel refresh.
- **`max_output_tokens` stripped:** The proxy's `LLMChat.prompt()` does not support `max_output_tokens` kwarg — patched out in runner. Side effect: runaway generation on hard Qs (q43/q49).
- **Kernel contention:** 3 parallel arms (Sonnet/Gemini3Pro/ChatGPT) on one kernel caused cascading KERNEL_BUSY failures. Resolved with `--idle-wait 600`.
- **Timeout calibration:** 30 min per task insufficient for q44 CTF. May need 60+ min or skip q44 HCH.
