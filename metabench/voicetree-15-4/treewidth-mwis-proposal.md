---
color: green
isContextNode: false
agent_name: Yan
---
# Treewidth MWIS — separator-choice spike proposal

Max Weighted Independent Set on a masked graph whose treewidth structure is hidden. Decomposition = separator choice. Non-obvious cuts, NP-hard to optimize, load-bearing because bad separators explode the residual pieces.

## Core design

**~120 nodes, ~280 edges**, integer vertex weights, total objective = sum of selected-vertex weights. Model sees only the node list, edge list, and weights. No cluster labels, no separator markers.

## Hidden generation (what makes the cut choice non-obvious)

- **SBM-generated cluster backbone.** 4 hidden blocks of ~30 nodes each with dense intra-block edges (p≈0.25) + sparse inter-block edges (p≈0.02). Treewidth of each block ~6-8; full graph treewidth ~12-16 if separators are chosen well.
- **Bridge nodes.** ~6 nodes connect 2+ blocks via high-degree edges → natural separator candidates, but *which* bridge subset is the minimum cut is non-obvious.
- **Decoy high-weight vertices.** ~8 vertices with top-quartile weight placed inside the densest block → attracts greedy-by-weight but destroys independence because their neighbours are also heavy.
- **Weight-structure decoupled from cluster structure.** Weight distribution (exponential, heavy tail) does NOT correlate with block membership → "cut by cluster" and "cut by weight-weighted load" disagree on boundaries.

## Competing decomposition axes

| Axis | Cut on | Cheap piece | Expensive residual |
|------|--------|-------------|--------------------|
| Balanced-separator-first | Find ~10-node vertex separator splitting graph ~50/50, recurse | Clean DP halves | Bridge nodes ambiguous → reconciliation hard |
| Modularity-first | Detect clusters, solve each, reconcile on cross-cluster edges | Small dense subproblems | Decoy vertices + cross-cluster indep set violations |
| High-degree-peel | Fix high-degree vertices first (include or exclude), recurse | Fast local reduction | Misses global weight-optimum in long tails |
| Weight-ordered-greedy | Accept by descending weight if independent | Fast | Traps on decoy cluster; ignores structure entirely |
| Composite | Separator + weight-aware reconciliation | Multi-axis capture | Diffuse, hardest to score |

## Why this is genuinely indeterminate

- Finding the best vertex separator is NP-hard; even balanced-separator approximation leaves real headroom.
- Cluster-first disagrees with separator-first on bridge nodes; no objective tie-breaks them without solving both halves.
- Decoy heavy vertices punish any greedy-by-weight short-cut that skips structural reasoning.
- Optimal treewidth-ordered DP ≠ optimal partition for this graph under MWIS; the cut quality is load-bearing and not uniquely determined.

## Gold + baseline

- **Gold:** OR-tools CP-SAT MWIS formulation. Runs in seconds on 120-node graphs; OPTIMAL status reliable.
- **Baseline:** Greedy-by-weight-then-degree. Typical 15-30% gap on structured graphs. Leaves real headroom.

## Protocol

Reuse the evolved local harness from `hch/masked_block_jobshop/`. Same structure:
- Turn 1 = plan turn only. Emits `DECLARED_DECOMPOSITION_AXIS`, `DECLARED_AXIS_RATIONALE`, `DECLARED_BOUNDARY_CUT` (which vertex set the model claims separates the graph), `PLAN_STATE` (free-form string — the model's running todo/plan), `ATOMIC_FORECAST` (thresholded gap), `CONTINUE_FORECAST`, `DECISION`, `NEXT_SUB`.
- Exec turns receive `CURRENT_PLAN_STATE`, emit `BEST_GUESS` (selected vertex set as JSON list), `UPDATED_PLAN_STATE`, `QUALITY_FORECAST`, `CONTINUE_FORECAST`, `DECISION`, optional `NEXT_SUB`.
- Plan state is **free-form text** — model chooses its own structure. No schema.
- 30-min total budget, per-subtask budget (e.g. 600s), MAX_EXEC_TURNS=4.
- Thresholded gap: gap% = 100*(opt - model_value)/opt. Thresholds: gap ≤ 2%, ≤ 5%, ≤ 10%.

## Metacog signals

1. Declared axis + declared cut vertices at plan-turn
2. Per-subproblem p_solve vs realized quality → intra-run A1
3. Did the model's declared cut actually separate the graph? (feasibility check on the cut)
4. Across axes: which axis dominates gap% at OPTIMAL?
5. Plan revision: did the model swap axes or cut after seeing a subproblem result?

## Run target

One Gemini 3 Pro seed-1 run, local harness, results under `hch/treewidth_mwis/results/`. Mirror masked_block_jobshop output schema so the existing analyzer script needs minimal changes.

## Open design questions

1. 120-node may be too easy for CP-SAT gold AND too easy for a decent heuristic. Pre-flight: measure CP-SAT vs greedy gap; if gap < 10%, scale to 150-180 nodes.
2. Should `DECLARED_BOUNDARY_CUT` be a structured vertex list (checkable) or free-form NL (richer)? Recommend structured list + free-form rationale.
3. Weight distribution — exponential vs uniform vs bimodal. Exponential gives heaviest decoy-vertex pull.
4. Axis enum: keep short and closed for scoring (5 options + other), or open for richer metacog? Recommend enum + "other" escape hatch like the jobshop spike.

### NOTES

- Risk: if separator approximation is trivially findable by a model (min-cut on a clustered SBM is usually obvious from edge density), the axis choice collapses to modularity-first. Mitigation: tune inter-block density + bridge nodes so the min vertex separator is not aligned with the SBM clusters.
- If CP-SAT gold fights the weight distribution (e.g. fractional optimum + integrality gap), consider adding LP-relaxation as a secondary upper bound for calibration.
- This spike is structurally analogous to the masked-block jobshop but with **graph** rather than **schedule** decomposition — same metacog frame, different surface.

[[recommended-problem-setup-post-tsp_2_1_0_0]]
