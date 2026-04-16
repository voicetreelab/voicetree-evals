---
isContextNode: false
agent_name: Ben
color: green
---
# Discussion of Overnight Results — Done

Wrote `voicetree-16-4/discussion-of-results.md` and updated `kaggle_submission/writeup-v2.md` with a new **Results from the Overnight Pilot Run (2026-04-17)** subsection inserted *above* the existing Phase-1 capability tables (no existing content removed or reordered).

## Sources read
- `voicetree-16-4/OVERNIGHT-RESULTS.md` (Ayu_1 wake-up brief)
- `voicetree-16-4/round1-review.md` (Tao) + `round1-review-complete.md`
- `voicetree-16-4/round2-review.md` (Ayu_1) + `round2-review-complete.md`
- `voicetree-16-4/task_1776359444895al9.md` (Noam's overnight brief)
- `voicetree-16-4/factory-a-eval-plan-v1.md`
- `kaggle_submission/results/full/concerns.md` × 9: portfolio_medium_seed14, cjs_hard_seed4, mwis_hard_seed5, graphcol_hard_seed7, steiner_hard_seed7, tsp_hard_seed4, ve_hard_seed4, portfolio_hard_seed25, portfolio_hard_seed5

## Discussion artifact contents
1. Headline (1 paragraph) — 26→206 rows, ~192 LLM probe runs, both rounds PROCEED, dominant signal is portfolio infeasibility (1/72 feasible).
2. Per-model strict-parse table (G 84.4 %, S 75 %, GPT 100 %).
3. Per-class feasibility table (G/S/GPT broken out per class × difficulty, 14 rows incl. portfolio).
4. 8 headline findings — portfolio failure, Sonnet MWIS/VE-hard pattern, GPT parse-vs-quality decoupling, W5 budget hole, Mary/Rex W1 divergence, W7→W8 seed drift, MWIS bridge-check generator limit, R1↔R2 reviewer agreement.
5. Top 6 bugs with severity (1 blocker × 2 portfolio + Sonnet, 2 warnings, 2 nuisances).
6. 5 next experiments ordered by impact, each tied to a finding.

## writeup-v2.md update
- Inserted new `### Results from the Overnight Pilot Run (2026-04-17, 3 models × 64 probe rows)` subsection at the top of the existing `## Results, Insights, and Conclusions` section, *before* the Phase-1 capability baseline table.
- Includes both tables, 3 load-bearing pilot findings, and pipeline issues (non-blocking).
- All existing content preserved verbatim (Phase-1 baselines, metacog profile, audit, 7 findings, CF pass, coaching, etc.) — no reorder, no deletion.
- Decision: kept the existing fictional-projected tables intact (5 models incl. Gemini 3 Pro / Haiku 4.5 / Nano) since they're not labelled TODO. The new subsection makes clear which tables come from the actual overnight run.

## Commit (next)
```
cd /Users/bobbobby/repos/voicetree-evals/metabench
git add voicetree-16-4/discussion-of-results.md kaggle_submission/writeup-v2.md
git commit -m "discussion of overnight results + writeup-v2 update"
```

## Related
- [discussion-of-results](discussion-of-results.md)
- [OVERNIGHT-RESULTS](OVERNIGHT-RESULTS.md)

[[task_1776369185208zf0]]
