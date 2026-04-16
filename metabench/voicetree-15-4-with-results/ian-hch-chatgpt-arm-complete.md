---
color: green
isContextNode: false
agent_name: Ian
---
# HCH HLE-12 v2 — GPT-5.4 arm — 15/24 tasks run, axis scores delivered

Completed GPT-5.4 (openai/gpt-5.4 base) arm of HCH HLE-12 v2. 15/24 tasks valid (9 KERNEL_BUSY from 3-arm contention). Key finding: HCH 3/7=43% vs Vanilla 1/8=13%, subtask calibration B=0.063 (exceptional), severe overconfidence on final p_correct.

## Model: `openai/gpt-5.4` (base)
First tried `gpt-5.4-pro` → quota error at $23/call. Downgraded to `gpt-5.4` base — ran cleanly.

## Coverage: 15/24 tasks valid
9 tasks missing (KERNEL_BUSY): q43_{hch,van}, q44_hch, q52_{hch,van}, q53_hch, q68_van, q99_{hch,van}

## Axis Scores
| Axis | GPT-5.4 | Gemini 2.5 Flash v1 (ref) |
|------|---------|---------------------------|
| A1 (atomic Brier) | **0.406** | 0.427 |
| A2 (word MAPE) | **1.069** | 0.745 |
| A3 (decomp paid off) | **2/5 (40%)** | 0/5 |
| B (subtask p_solve Brier) | **0.063** | 0.507 |
| C (p_correct Brier HCH) | **0.474** | — |
| C (p_correct Brier Van) | **0.769** | — |
| D HCH pass rate | **3/7 = 0.429** | — |
| D Vanilla pass rate | **1/8 = 0.125** | — |

## Key Findings
1. **HCH +0.304 over Vanilla** (43% vs 13%) — strong signal
2. **B=0.063 (subtask calibration) — exceptional** — GPT-5.4 tracks whether subtasks are solved correctly far better than Gemini 2.5 Flash (0.507)
3. **Severe overconfidence on final p_correct** (C=0.474/0.769) — says 0.9-0.99 but fails most questions
4. **Word MAPE 1.069** — poor estimation; 5-10x variance on subtask word counts
5. **Decomp helps**: 2/5 decompositions paid off vs 1/2 atomic

## Results Files
- Primary: `results/hch_hle12_v2_openai_gpt-5_4_20260415_104821.jsonl`
- Fill-in: `results/hch_hle12_v2_openai_gpt-5_4_20260415_100926.jsonl`
- Pilot note: `pilots/hch-hle12-v2-chatgpt-2026-04-15.md`

## Files Changed

- kaggle/pilots/hch-hle12-v2-chatgpt-2026-04-15.md

### NOTES

- gpt-5.4-pro quota failure ($23/call with max_output_tokens=32768) — for future GPT arms, use base model or lower max_output_tokens
- Kernel contention with 3 simultaneous arms causes ~37% task loss — should stagger starts or use dedicated kernels per arm
- Axis C naming: in this run C = final p_correct Brier. v1 pilot used C = subtask p_solve Brier. Clarify in final comparison table.
- Q55 TC⁰ case: official regex failed (TC^0 ≠ TC⁰ as string) but judge passed for both arms — confirms judge > regex
- B=0.063 is the most surprising result: GPT-5.4 has excellent subtask-level self-assessment despite poor final-answer confidence

[[task_1776243675480prt]]
