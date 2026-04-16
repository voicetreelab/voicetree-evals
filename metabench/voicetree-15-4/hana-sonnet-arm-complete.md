---
color: green
isContextNode: false
agent_name: Hana
---
# HCH HLE-12 v2 — Claude Sonnet arm — 23/24 tasks complete

23/24 HCH HLE-12 v2 tasks run on anthropic/claude-sonnet-4-6. q44_hch timed out (CTF, >30 min). Full 6-axis scores computed. Key finding: Axis D dramatically improved vs Gemini Flash (0.410 vs 0.934).

## Model
`anthropic/claude-sonnet-4-6` (confirmed live via proxy test)

## Pass rates
- HCH: 4/11 = 36.4% (q44 timed out)
- Vanilla: 4/12 = 33.3%

## MC-Properties Table

| Axis | Metric | Sonnet v2 | Gemini Flash v1 (clean) |
|------|--------|-----------|------------------------|
| A1 | Brier(p_atomic, van_correct) | 0.353 | 0.427 |
| A2 | Word MAPE (atomic vs vanilla wc) | 0.524 | 0.745 |
| A3 | chose_decomp / paid_off | 5/11 / 1/5 | 7/12 / 0/5 |
| B | Subtask word MAPE | 0.527 | 0.507 |
| C | Brier(p_solve, self-solved) | 0.065 | 0.022 |
| D HCH | Brier(p_correct, hch_correct) | **0.410** | **0.934** |
| D Van | Brier(p_correct, van_correct) | 0.307 | N/A |

## Key findings
1. **Axis D: 0.410 vs 0.934** — Claude Sonnet calibration dramatically better than Gemini Flash
2. **Axis A2: 0.524 vs 0.745** — better word-count self-estimation
3. **Q43/Q49 runaway generation** — without max_output_tokens, subtask 1 produced 11,592 / 9,982 words respectively (11.5 min / 6 min). max_output_tokens was stripped because LLMChat.prompt() on this kernel doesn't support the kwarg — needs a proxy-side fix
4. **Q44 CTF intractable** — HCH arm timed out at 1800s (30 min); CTF problem needs code execution, not just reasoning
5. **A3 first payoff** — Q41 decomposed into 4 subtasks and passed (first decomp payoff across all pilot runs)
6. **Axis C design gap** — self-reported correctly_solved=True for 10/11 questions including all wrong answers

## Files Changed

- kaggle/pilots/hch-hle12-v2-claudesonnet-2026-04-15.md
- kaggle/results/hch_hle12_v2_anthropic_claude-sonnet-4-6_20260415_102239.jsonl
- kaggle/results/hch_hle12_v2_anthropic_claude-sonnet-4-6_20260415_115135.jsonl

### NOTES

- q44_hch still outstanding — needs 60+ min timeout or skip; CTF problem may be fundamentally unanswerable without code execution
- max_output_tokens stripping causes runaway generation on hard Qs — need proxy-side token cap or task-level workaround
- Kernel contention with 3 parallel arms was the main operational hazard — idle-wait 600s resolved it
- Results are non-deterministic: q68_vanilla gave B (pass) in run2, C (fail) in run3 — note variance in final analysis

[[task_1776243675433sac]]
