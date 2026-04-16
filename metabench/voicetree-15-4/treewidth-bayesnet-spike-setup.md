---
color: green
isContextNode: false
agent_name: Yan
---
# Two decomposition-uncertainty spikes — setup + spawn

Wrote concrete proposals for the two Tier-1 problem classes (tree-decomposition graph problems and Bayesian VE) from the parent research node, then spawned two parallel Codex execution agents to build each spike on the evolved local harness with free-form PLAN_STATE string.

## Proposals written
- [treewidth-mwis-proposal](treewidth-mwis-proposal.md) — Max Weighted Independent Set on a 120-node (scale-up allowed) masked SBM graph with bridge nodes, decoy heavy vertices, and weight-vs-cluster disagreement. Separator choice is load-bearing. Gold = CP-SAT. Axes: balanced_separator | modularity | high_degree_peel | weight_greedy | composite | other.
- [bayesnet-ve-proposal](bayesnet-ve-proposal.md) — ~22-variable block-DAG Bayes net with bridge + decoy variables, single-variable conditional query. Elimination ordering IS the decomposition. Gold = exact VE with best of heuristics + 1000 random. Gap metric = |log p* - log p_hat|. Axes: min_neighbors | min_weight | min_fill | cluster_first | query_centered | composite | other.

## Harness pattern reused
Both spikes mirror `hch/masked_block_jobshop/` planstate variant:
- Plan turn emits declared axis + declared cut/ordering + free-form `PLAN_STATE` string + thresholded gap forecasts + continue forecast + decision + optional `NEXT_SUB`.
- Exec turns get `CURRENT_PLAN_STATE`, emit `BEST_GUESS` (instance-specific JSON), `UPDATED_PLAN_STATE`, forecasts, decision.
- `PLAN_STATE` is free-form text — the user explicitly asked for todo/subtask plan state as a string.
- 30-min total budget, 600s per-subtask, MAX_EXEC_TURNS=4.
- One Gemini 3 Pro seed-1 run per spike, local-only.

## Agents spawned
- **Aki (Codex)** — Treewidth MWIS spike. Task node `task_1776340037222wdf`. Will deliver `hch/treewidth_mwis/` + one progress node.
- **Ama (Codex)** — Bayesian VE spike. Task node `task_1776340059062d0k`. Will deliver `hch/bayesnet_ve/` + one progress node.

Both pinned to: build → run once → write one progress node, NO Kaggle port, NO multi-seed/model sweep.

## Decisions taken (working assumptions — flag if wrong)
1. Used the same budget/turn structure as masked_block_jobshop rather than redesigning. Rationale: the point is to vary the problem class, not the protocol.
2. Gave each spike its own `DECLARED_*` axis enum specific to that problem class, but kept the rest of the contract identical to the jobshop planstate variant.
3. Verified that the MWIS and VE answers can be scored with thresholded gap (MWIS: gap%; VE: log-prob gap in nats) so the metacog calibration metrics (Brier over thresholds) carry over.
4. Did NOT confirm with user before spawning — the directive "let's make two spikes ... evolved local harness ... plan state saved as string" was explicit. If I misread the ask, stop the two agents and rescope.

## Open risks flagged in proposals
- MWIS: CP-SAT may solve 120 nodes trivially; pre-flight gap measurement required, scale-up allowed.
- Bayes VE: 22 variables may either be trivial or too big for prompt; pre-flight peak-factor-size spread across heuristics required.
- Both: pattern-locked to the jobshop contract; if a cleaner shape emerges for the new problem classes, surface as an open question, don't refactor mid-run.

## PREDICTION CLAIMS

- **Claim 1:** Both agents will complete and emit one progress node each within 90 minutes of spawn. Confidence: 0.75. Falsifier: either agent still in-progress / errored at the 90-min mark.
- **Claim 2:** The plan-once-execute-once-stop pattern observed across every prior spike (TSP, 3 jobshop sizes, 2 Steiner sizes, masked-block jobshop) will repeat on at least one of these two spikes. Confidence: 0.80. Falsifier: both runs show exec_turn_count ≥ 2 and the final BEST_GUESS differs from the first exec turn's BEST_GUESS.
- **Claim 3:** The declared-axis distribution across the two spikes will NOT be `composite` in both cases — Gemini 3 Pro will collapse to one of the named enums for at least one of the two spikes. Confidence: 0.65. Falsifier: both runs declare `composite`.
- **Claim 4:** The MWIS baseline-to-gold gap will be ≥15% on the default 120-node instance (so the spike is discriminative without scale-up). Confidence: 0.55. Falsifier: baseline gap < 15%, triggering scale-up.
- **Claim 5:** On the Bayes VE spike, the model's `peak_factor_size_self_report` will be wrong (differ from the true peak for `ordering_used`) on at least one turn. Confidence: 0.70. Falsifier: self-report matches true peak on every exec turn for every run.

## Files changed
- voicetree-15-4/treewidth-mwis-proposal.md (new)
- voicetree-15-4/bayesnet-ve-proposal.md (new)
- voicetree-15-4/task_1776340037222wdf.md (new, via spawn)
- voicetree-15-4/task_1776340059062d0k.md (new, via spawn)

## Related
- [recommended-problem-setup-post-tsp_2_1_0_0](recommended-problem-setup-post-tsp_2_1_0_0.md) — parent research node with the Tier-1 problem classes
- [masked-block-jobshop-proposal](masked-block-jobshop-proposal.md) — format template for these proposals
- [masked-block-jobshop-planstate-rerun](masked-block-jobshop-planstate-rerun.md) — harness variant being reused

[[recommended-problem-setup-post-tsp_2_1_0_0]]
