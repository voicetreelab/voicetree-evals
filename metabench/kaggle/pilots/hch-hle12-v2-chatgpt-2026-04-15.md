# HCH HLE-12 v2 — ChatGPT/GPT arm — Pilot Note (2026-04-15)

## Model
**`openai/gpt-5.4`** (base; NOT pro)

Model selection rationale: `openai/gpt-5.4-pro` was initially tried but failed with quota error at ~$23/call estimated cost with `max_output_tokens=32768`. Downgraded to `openai/gpt-5.4` (base) which ran without quota issues. Full OpenAI model list from proxy:
- `openai/gpt-5.4-pro`, `openai/gpt-5.4`, `openai/gpt-5.4-mini`, `openai/gpt-5.4-nano`, `openai/gpt-oss-120b`, `openai/gpt-oss-20b`

## Run Configuration
- Runner: `kaggle/scripts/run_hch_hle12_with_model.py --model openai/gpt-5.4 --task-timeout 240 --sleep-between 30 --idle-wait 120`
- Results files: 
  - Run 1 (partial, 10 tasks): `results/hch_hle12_v2_openai_gpt-5_4_20260415_100926.jsonl`
  - Run 3 (full 24 tasks): `results/hch_hle12_v2_openai_gpt-5_4_20260415_104821.jsonl`
- Data merged: run3 primary, run1 fills KERNEL_BUSY gaps

## Coverage
**15/24 tasks valid** (9 tasks missing — KERNEL_BUSY due to shared Kaggle kernel with Gemini 3 Pro + Sonnet arms running in parallel)

| Valid HCH | Valid Vanilla | Missing |
|-----------|---------------|---------|
| 7/12 | 8/12 | q43_{hch,van}, q44_hch, q52_{hch,van}, q53_hch, q68_van, q99_{hch,van} |

## Results Table

| Q | Gold | HCH Answer | HCH Pass | Van Answer | Van Pass |
|---|------|------------|----------|------------|----------|
| Q41 | 46.24 | (wrong) | ❌ | 48.00 | ❌ |
| Q43 | C | — MISSING — | | — MISSING — | |
| Q44 | flag{no_zeros} | MISSING | | flag{shamir_0n_strings} | ❌ |
| Q48 | 5429515560378 | 5429515560378 | ✅ | 54295198140 | ❌ |
| Q49 | D | E | ❌ | I | ❌ |
| Q52 | A | — MISSING — | | — MISSING — | |
| Q53 | 0 | MISSING | | 1/4 | ❌ |
| Q55 | TC⁰ | uniform TC0 | ✅ (judge) | TC^0 | ✅ |
| Q57 | C | D | ❌ | D | ❌ |
| Q65 | D | C | ❌ | B | ❌ |
| Q68 | B | B | ✅ | — MISSING — | |
| Q99 | dodecagon | — MISSING — | | — MISSING — | |

## Axis Scores (from 15/24 valid tasks)

| Axis | GPT-5.4 | Gemini 2.5 Flash v1 (ref) | Notes |
|------|---------|---------------------------|-------|
| A1 (atomic Brier) | **0.406** | 0.427 (clean) | N=7/12 HCH. Overconfident when wrong |
| A2 (subtask word MAPE) | **1.069** | 0.745 | N=13 subtasks. GPT-5.4 undershoots actual words |
| A3 (decomp decision) | **2/5 paid off** | 0/5 (clean) | Also 1/2 atomic passed. Decomp helps more than Gemini |
| B (subtask p_solve Brier) | **0.063** | 0.507 (partially valid) | N=13. REMARKABLE — near-perfect subtask calibration |
| C (p_correct Brier, HCH) | **0.474** | 0.002 (but design gap) | Severely overconfident. GPT-5.4 says ~0.9 p_correct but fails |
| C (p_correct Brier, Van) | **0.769** | 0.000 (design gap) | Even worse for vanilla |
| D (HCH pass rate) | **3/7 = 0.429** | ~0.3 (v1, noise) | HCH strong advantage |
| D (Vanilla pass rate) | **1/8 = 0.125** | ~0.2 (v1, noise) | |

### Axis C note
The C values here are p_correct Brier (final answer). In v1 analysis, Axis C was subtask p_solve Brier (which showed 0.026 as "design gap"). The naming may differ — treat as clarified in progress node.

## Key Findings

### 1. HCH substantially outperforms Vanilla (+0.304 pass rate)
HCH: 3/7 = 43% vs Vanilla: 1/8 = 13%. This is the clearest signal from the run. HCH decomposition is helping GPT-5.4 on hard questions.

### 2. Subtask calibration (B=0.063) is exceptional
GPT-5.4 knows when it solved a subtask (p_solve tracks correctly_solved tightly). Far better than Gemini 2.5 Flash (0.507). This is a genuine strength of GPT-5.4.

### 3. Final confidence is severely overconfident (C=0.474/0.769)
GPT-5.4 reports p_correct ~0.90-0.99 but fails most questions. Severe overconfidence at the final step. The model does NOT know when its final answer is wrong.

### 4. Word count estimation is poor (A2=1.069)
GPT-5.4 systematically underestimates how many words subtasks will take (some subtasks produce 5-10x more words than predicted). Notable outlier: q49_sub3 predicted 40 words, produced 6.

### 5. Decomposition helps when applied
When GPT-5.4 chose to decompose, 2/5 paid off (40%). When it stayed atomic, 1/2 passed (50%). Mixed — but neither catastrophically bad.

## Notable Task Behaviors

### Q55 (TC⁰ — Physics)
- HCH: Went atomic (1 subtask), said "uniform TC0" — judge correctly identified as TC⁰ equivalent ✅
- Vanilla: Said "TC^0" — official regex failed but judge passed ✅
- Both arms passed via judge (not regex) — confirming judge value over regex

### Q48 (Large integer — Math)
- HCH: Decomposed into 2 subtasks, computed 5429515560378 correctly ✅
- Vanilla: Got 54295198140 (off by factor ~100) ❌
- Clear HCH advantage on computation

### Q49 (Multiple choice — Medicine/Biology)
- Both arms failed. HCH decomposed into 3 subtasks, sub1 explicitly flagged as wrong (correctly_solved=False, confidence=0.42)
- Despite knowing sub1 failed, HCH still produced wrong final answer

## Cost and Latency
- Total valid task time: ~713s across 15 tasks (~47.5s avg per task)
- GPT-5.4 base: no quota errors observed (only gpt-5.4-pro hit $23/call quota limit)
- Full 24-task run would take ~19 min on uncontested kernel

## Blockers Encountered
1. `gpt-5.4-pro` quota exceeded at $23/call — switched to `gpt-5.4` base
2. Kernel contention from 3 parallel arms — 9/24 tasks missing
3. Run 2 crashed due to `ReadTimeout` during `wait_for_idle` (HTTP-level timeout)

## Comparison Arm Context
- Gemini 3.1 Pro (Gus): 19/24 tasks in file (stuck on last 5 when I finished)  
- Claude Sonnet 4.6 (Hana): 4/24 tasks in file when I finished
