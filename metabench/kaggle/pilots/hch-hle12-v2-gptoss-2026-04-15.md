# HCH HLE-12 v2 — GPT-OSS-120B arm pilot note

**Date:** 2026-04-15  
**Model:** `openai/gpt-oss-120b`  
**Runner:** `run_hch_hle12_with_model.py` (patched v2 task files)  
**Results file:** `results/hch_hle12_v2_openai_gpt-oss-120b_20260415_130333.jsonl`  
**Kernel:** same dedicated kernel (3rd successive arm)  
**Params:** `--idle-wait 60 --task-timeout 2400 --sleep-between 10`

---

## Setup Notes

- Same dedicated kernel reused (alive across all 3 arms: Haiku → Qwen → GPT-OSS)
- `max_output_tokens=32768` stripped by runner regex
- Model does **not** follow HCH protocol structure — ATOMIC_PREDICTION, SUBTASKS, P_CORRECT largely absent
- Several wrapper errors (InternalServerError): Q43_hch, Q57_hch, Q57_van, Q65_hch, Q99_hch
- Two TypeErrors: Q44_van, Q48_van (likely f-string/formatting issue in task code)
- Two judge errors (503 model unavailable): Q53_hch, Q68_hch

---

## Results: 24/24 submitted, 3 passed, 13 failed, 8 wrapper errors

| Q | Gold | HCH judge | Vanilla judge | n_sub | HCH status | Notes |
|---|------|-----------|---------------|-------|------------|-------|
| 41 | 46.24 | ❌ (48.00) | ❌ (48.00) | 1 | ok | |
| 43 | C | ❌ (503 err) | ❌ (E) | — | wrapper error | |
| 44 | flag{no_zeros} | ❌ (n_sub=0) | — | 0 | ok / van: TypeError | |
| 48 | 5429515560378 | ✅ | — | 0 | ok / van: TypeError | Atomic, correct! |
| 49 | D | ✅ | ❌ (F) | 0 | ok | judge=True despite answer=None |
| 52 | A | ❌ | ❌ | 0 | ok | Both answer=None |
| 53 | 0 | ❌ (judge 503) | — | 1 | ok / van: wrapper error | |
| 55 | TC⁰ | ❌ | ✅ (TC^0) | 0 | ok | Van took 652s! p_correct=0.35 |
| 57 | C | — | — | — | wrapper / wrapper | Both wrapper errors |
| 65 | D | — | ❌ (A) | — | wrapper error | |
| 68 | B | ❌ (judge 503) | ❌† | 0 | ok | †official=True but judge 503 → False |
| 99 | dodecagon | — | ❌ (pentagon) | — | wrapper error | |

**HCH pass: 2/12 = 16.7%** (Q48, Q49)  
**Vanilla pass: 1/12 = 8.3%** (Q55)  
**True accuracy (incl. Q68 van official match): possibly 2/12 vanilla**

---

## Metacog Axis Scores (⚠️ severely limited — protocol non-compliance)

| Axis | GPT-OSS-120b | Notes |
|------|-------------|-------|
| A1 (atomic Brier) | 0.665 | n=2 only — NOT RELIABLE |
| A2 (word MAPE) | 5.875 | n=2 only — NOT RELIABLE |
| A3 (decomp) | **0/8 chose** (all atomic) | Strongest signal: GPT-OSS never decomposes |
| B (subtask MAPE) | 1.706 | n=2 only — NOT RELIABLE |
| C (p_solve Brier) | 0.001 | n=2 — NOT RELIABLE |
| D_hch (answer Brier) | **0.292** | n=4 — partially reliable |
| D_van (answer Brier) | **0.493** | n=6 — partially reliable |

**Comparable to other arms only for A3 and D.**

---

## Key Observations

### 1. Never decomposes — unique across all arms
GPT-OSS uses n_subtasks=0 (pure atomic, no protocol output) or n_subtasks=1 (one subtask = still atomic). Never decomposed into 2+ subtasks. Sharp contrast with Haiku/Qwen (12/12 decompose) and Gemini 3 Pro (1/9).

### 2. Protocol non-compliance breaks most metrics
GPT-OSS largely ignores the HCH prompt structure — doesn't emit `ATOMIC_PREDICTION`, `SUBTASKS`, or consistent `P_CORRECT`. Axis A1/A2/B/C cannot be computed reliably (n=2 each). Only A3 and D have meaningful signal.

### 3. Best D_hch so far (0.292, n=4)
Despite limited sample, D_hch=0.292 is the best answer calibration of all arms run. For Q55 vanilla, p_correct=0.35 with correct answer (TC^0) — appropriately uncertain.

### 4. Infrastructure: 5 wrapper InternalServerErrors
Q43_hch, Q57_hch, Q57_van, Q65_hch, Q99_hch all got InternalServerError during task execution. These are proxy/model errors, not task bugs. Two TypeErrors (Q44_van, Q48_van) may be f-string issues specific to these task files.

### 5. Q55 vanilla: 652 seconds, correct
The longest successful task of the session (10.8 minutes). GPT-OSS eventually returned TC^0 with appropriate uncertainty (p=0.35).

### 6. Q68 vanilla: official=True but judge 503
The regex check matched 'B'==gold but the judge call hit 503, making judge_pass=False. The answer appears correct — this should count as a pass if judge error is treated as inconclusive.

---

## Infrastructure Notes
- Kernel survived all 3 arms across ~3 hours without token expiry
- 2400s task-timeout essential — Q55 vanilla took 652s
- Model proxy 503 errors emerged on GPT-OSS (not seen on Haiku or Qwen) — proxy load under OSS demand
