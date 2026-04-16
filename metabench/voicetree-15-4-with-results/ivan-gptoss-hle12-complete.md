---
color: green
isContextNode: false
agent_name: Ivan
---
# HCH HLE-12 v2 — GPT-OSS-120B arm — 24 tasks run

Completed 3rd arm of HCH HLE-12 v2 pilot on openai/gpt-oss-120b. 24/24 tasks submitted; 3 passed, 13 failed, 8 wrapper errors. Key finding: GPT-OSS never decomposes (A3=0/8) and largely ignores HCH protocol structure, making most axes unreliable. Best D_hch (0.292) of all arms despite compliance issues.

## Results Summary

**Model:** `openai/gpt-oss-120b`  
**Results file:** `kaggle/results/hch_hle12_v2_openai_gpt-oss-120b_20260415_130333.jsonl`  
**Kernel:** same dedicated kernel (3rd successive arm: Haiku → Qwen → GPT-OSS)  
**Params:** `--idle-wait 60 --task-timeout 2400 --sleep-between 10`

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

## Metacog Axis Scores

| Axis | GPT-OSS-120b | Notes |
|------|-------------|-------|
| A1 (atomic Brier) | 0.665 | n=2 only — NOT RELIABLE |
| A2 (word MAPE) | 5.875 | n=2 only — NOT RELIABLE |
| A3 (decomp) | **0/8 chose** (all atomic) | Strongest signal: GPT-OSS never decomposes |
| B (subtask MAPE) | 1.706 | n=2 only — NOT RELIABLE |
| C (p_solve Brier) | 0.001 | n=2 — NOT RELIABLE |
| D_hch (answer Brier) | **0.292** | n=4 — partially reliable |
| D_van (answer Brier) | **0.493** | n=6 — partially reliable |

## Key Observations

1. **Never decomposes (A3=0/8)** — unique across all arms; Haiku/Qwen always decompose (12/12), Gemini 3 Pro rarely (1/9). GPT-OSS treats every question as atomic.
2. **Protocol non-compliance** — doesn't emit ATOMIC_PREDICTION, SUBTASKS, P_CORRECT consistently. Axes A1/A2/B/C unreliable (n=2 each).
3. **Best D_hch (0.292)** — best answer calibration of all arms run, despite limited sample.
4. **5 InternalServerErrors** from proxy (Q43_hch, Q57_hch, Q57_van, Q65_hch, Q99_hch) — proxy 503 under OSS demand, not task bugs.
5. **2 TypeErrors** (Q44_van, Q48_van) — f-string/formatting issues in task files specific to these Qs.
6. **Q55 vanilla took 652s** — longest successful task (10.8 min); GPT-OSS returned correct TC^0 with appropriate p=0.35 uncertainty.

## Files Changed

- kaggle/results/hch_hle12_v2_openai_gpt-oss-120b_20260415_130333.jsonl
- kaggle/pilots/hch-hle12-v2-gptoss-2026-04-15.md

### NOTES

- GPT-OSS protocol non-compliance makes this arm data-sparse for A1/A2/B/C — only A3 and D are cross-arm comparable
- Q68 vanilla: official=True (regex matched 'B') but judge call hit 503 → judge_pass=False; true accuracy may be 2/12 vanilla
- Kernel survived all 3 arms (~3 hours) without token expiry — 2400s task-timeout essential for long OSS runs
- Proxy 503 errors emerged specifically on GPT-OSS arm — higher latency/load under OSS model demand vs Haiku/Qwen

[[task_1776254854161eae]]
