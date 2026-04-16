# HCH HLE-12 v2 — Claude Haiku arm pilot note

**Date:** 2026-04-15  
**Model:** `anthropic/claude-haiku-4-5`  
**Runner:** `run_hch_hle12_with_model.py` (patched v2 task files)  
**Results file:** `results/hch_hle12_v2_anthropic_claude-haiku-4-5_20260415_122210.jsonl`  
**Kernel:** dedicated Haiku kernel (base-domain URL format, query-param token)  
**Purpose:** Floor/weak-tier reference point for capability curve

---

## Setup Notes

- Fresh Kaggle kernel provided; needed `kaggle-benchmarks` pip install + protobuf==5.29.6 fix on first kernel (abandoned). Second fresh kernel had correct environment pre-installed.
- `max_output_tokens=32768` stripped by runner regex (LLMChat.prompt() doesn't accept kwarg).
- Used `--idle-wait 25 --task-timeout 120 --sleep-between 10`.
- Did NOT use kaggle/.env (dedicated kernel, inline env vars).

---

## Results: 24/24 tasks run, 0 errors

| Q | Gold | HCH answer | HCH judge | Vanilla answer | Vanilla judge | n_sub | p_correct HCH | p_correct Van |
|---|------|------------|-----------|----------------|---------------|-------|---------------|---------------|
| 41 | 46.24 | 48.00 | ❌ | 48.00 | ❌ | 4 | 0.92 | 0.95 |
| 43 | C | None (cut off) | ❌ | E | ❌ | 2 | None | 0.45 |
| 44 | flag{no_zeros} | shamir_secret_key | ❌ | cybersecurity_ | ❌ | 3 | 0.35 | 0.75 |
| 48 | 5429515560378 | 110075771153 | ❌ | 5429515560378 | ✅ | 4 | 0.68 | 0.60 |
| 49 | D | F | ❌ | F | ❌ | 4 | 0.32 | 0.35 |
| 52 | A | G | ❌ | G | ❌ | 4 | 0.40 | 0.72 |
| 53 | 0 | 1/7 | ❌ | 1/13 | ❌ | 4 | 0.98 | 0.95 |
| 55 | TC⁰ | refused/non-answer | ❌ | NC¹ | ❌ | 3 | 0.12 | 0.35 |
| 57 | C | C | ✅ | D | ❌ | 4 | 0.80 | 0.72 |
| 65 | D | D | ✅ | B | ❌ | 4 | 0.72 | 0.85 |
| 68 | B | C | ❌ | C | ❌ | 4 | 0.90 | 0.85 |
| 99 | dodecagon | A regular hexagon | ❌ | Regular hexagon | ❌ | 3 | 0.85 | 0.90 |

**HCH judge pass rate: 2/12 = 16.7%**  
**Vanilla judge pass rate: 1/12 = 8.3%**

---

## Metacog Axis Scores

| Axis | Metric | Haiku | Gemini 2.5 Flash v1 | Gemini 3.1 Pro v2 |
|------|--------|-------|----------------------|-------------------|
| A1 (atomic Brier) | Brier(p_correct_if_atomic, vanilla_correct) | **0.252** | 0.427 | 0.007 |
| A2 (word MAPE) | \|words_if_atomic − van_words\| / van_words | **0.582** | 0.745 | 0.793 |
| A3 (decomp) | chose_decomp / paid_off | **12/12 / 2/12** | 7/12 / 0/7 | 1/9 / 0/1 |
| B (subtask MAPE) | mean \|actual_words − planned\| / planned | **0.371** | 0.507 | 0.226 |
| C (p_solve Brier) | Brier(p_solve, correctly_solved), n=41 sub | **0.100** | 0.002 | 0.001 |
| D_hch (answer Brier) | Brier(P_CORRECT_hch, hch_correct) | **0.393** | 0.934 | 0.332 |
| D_van (answer Brier) | Brier(P_CORRECT_van, van_correct) | **0.522** | N/A (LaTeX bug v1) | 0.100 |

---

## Key Observations

### 1. Haiku always decomposes (A3 = 12/12)
Haiku chose decomposition for ALL 12 questions — unlike Gemini 3.1 Pro (1/9) which nearly never decomposes, and v1 Flash (7/12). Decomposition paid off only 2/12 times. This is likely a prompt-following artifact: Haiku is weaker at evaluating when NOT to decompose.

### 2. Extreme overconfidence on wrong answers (D)
D_hch = 0.393, D_van = 0.522. Haiku reports p_correct=0.85–0.98 on questions where it gives completely wrong answers (e.g., Q53: answer=1/7, gold=0, p_correct=0.98; Q99: answer=hexagon, gold=dodecagon, p_correct=0.85). Vanilla is even worse calibrated.

### 3. One exception: Q55 self-aware refusal
Q55 (circuit complexity) — Haiku answered "Cannot provide reliable bound without clarification..." with p_correct=0.12. The low confidence was appropriate (actually knew it didn't know). Score: correct that it didn't know, but still failed.

### 4. A1 better than v1 but much worse than Gemini 3 Pro
Atomic calibration improved from v1 (0.427→0.252) but far behind Gemini 3 Pro (0.007). Haiku systematically overestimates p_correct_if_atomic (range 0.15–0.75 across Qs vs actual 8.3% vanilla pass rate).

### 5. Q43 truncation again
Q43 HCH response was cut off despite max_output_tokens stripping — the task ran for 69s (longest task), suggesting context/token issues.

### 6. B axis: Haiku over-shoots word targets
Subtask MAPE 0.371 — Q44 is an outlier (MAPE=1.28, subtasks ran 175/336/241 words vs planned 80/150/100). Generally Haiku produces more words than it plans.

---

## Infrastructure Notes

- First dedicated kernel lacked `kaggle-benchmarks` — needed pip install + protobuf==5.29.6 fix + kernel restart. Didn't work cleanly (IP auth issues with manually overriding MODEL_PROXY_API_KEY).
- User provided second fresh kernel which had the complete Kaggle benchmark environment pre-installed — worked immediately.
- Base-domain URL format (`https://kkb-production.jupyter-proxy.kaggle.net`) with token as query param returned 200 (unlike Iris's previous session which required path-embedded format). New kernel may have been provisioned differently.
