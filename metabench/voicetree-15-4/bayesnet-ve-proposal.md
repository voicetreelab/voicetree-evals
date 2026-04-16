---
color: green
isContextNode: false
agent_name: Yan
---
# Bayesian VE — elimination-ordering spike proposal

Exact inference on a masked Bayesian network where the elimination ordering IS the decomposition choice. Same treewidth math as MWIS, different surface. Ordering choice determines peak factor size, which determines whether the model can finish the computation within budget.

## Core design

**~22 binary variables**, single query `P(Q | E=e)` where Q is one hidden variable and E is a partial assignment to ~5 observed variables. Model sees only the DAG (parent list per node) + CPT tables. No elimination hints, no factor-size preview.

Objective: **log-probability accuracy**. Let p* = true marginal, p_hat = model's reported marginal. Gap = |log(p*) - log(p_hat)| in nats. This admits thresholded forecasts (gap ≤ 0.01, ≤ 0.1, ≤ 0.5 nats).

## Why ordering matters here (budget-gated correctness)

Variable elimination gives the *exact* answer for any valid ordering, but the **peak intermediate factor size** varies exponentially with order. With a 600s subtask budget, a bad ordering (say min-degree naive on a dense layer) can force intermediate factors larger than the model can actually compute correctly by hand — so the model either hallucinates numerical values or runs out of turn-budget mid-computation. A good ordering keeps every intermediate factor small enough that multi-step hand-arithmetic stays accurate.

This is the key: **the correctness of the answer is conditioned on the model's ability to carry out the factor products it plans**. Ordering = decomposition. Bad order → intractable by hand → numerical drift.

## Hidden generation (what makes ordering non-obvious)

- **Block-structured DAG.** 3 hidden clusters (~7 variables each) with dense intra-cluster arcs (treewidth 3-4 per cluster), 2-3 cross-cluster arcs per boundary.
- **Bridge variables.** 2 variables with parents in 2+ clusters → ambiguous cluster membership; order placement is decisive.
- **Decoy high-degree variable.** 1 variable with degree ≥ 6 (many parents and children) that looks like "eliminate last" but actually should go early because eliminating it late balloons a cross-cluster factor.
- **Query placement.** Q chosen inside a middle cluster so neither leaf-first nor root-first wins cleanly.
- **CPT skew.** CPTs have moderately skewed probabilities (nothing at 0 or 1) so numerical error is realistic but detectable.

## Competing decomposition axes

| Axis | Elimination rule | Cheap piece | Expensive residual |
|------|------------------|-------------|--------------------|
| Min-neighbors | Eliminate lowest-degree first | Fast on tree-like fringes | Blows up inside the decoy cluster |
| Min-weight | Eliminate smallest-domain-product first | Good numerical stability | Mis-sequences bridge variables |
| Min-fill | Eliminate variable that adds fewest edges | Near-optimal on many nets | Expensive to reason about by hand, easy to mis-compute |
| Cluster-first | Eliminate entire cluster before crossing | Localizes factors | Fails if query spans clusters |
| Query-centered | Eliminate peripheral-to-query first, compute toward Q | Great when query localized | Terrible if decoy is near Q |
| Composite | Score vars by weighted combo | Catches hybrids | Diffuse, hard to defend |

## Why this is genuinely indeterminate

- Finding optimal elimination order is NP-hard (equivalent to finding minimum treewidth decomposition).
- Min-neighbors vs min-fill disagree on roughly half the variables in this graph.
- The decoy variable inverts the "eliminate last = save the hub for the end" intuition.
- Bridge variables' correct order position depends on whether earlier choices already reduced cross-cluster factors.
- Cluster-first disagrees with query-centered when Q sits near a cluster boundary.

## Gold + baseline

- **Gold:** Exact VE using best-of-{min-neighbors, min-weight, min-fill, best-of-1000-random-orders}. Store p* and peak factor size. Junction tree also valid.
- **Baseline:** Naive lexicographic elimination ordering (by variable index). Often blows peak factor size and yields noisy numerical answer when the model is asked to do it by hand.

## Protocol

Reuse the evolved local harness structure from `hch/masked_block_jobshop/`. Same contract shape:
- Turn 1 = plan turn. Emits `DECLARED_ELIMINATION_AXIS` (enum: min_neighbors | min_weight | min_fill | cluster_first | query_centered | composite | other), `DECLARED_AXIS_RATIONALE`, `DECLARED_ORDERING` (the first 5-7 variables of the order the model will use), `PLAN_STATE` (free-form text), `ATOMIC_FORECAST` (thresholded log-prob gap), `CONTINUE_FORECAST`, `DECISION`, `NEXT_SUB`.
- Exec turns receive `CURRENT_PLAN_STATE`, emit `BEST_GUESS` (JSON: `{"p_query_given_evidence": <float>, "ordering_used": [...]}`), `UPDATED_PLAN_STATE`, `QUALITY_FORECAST`, `CONTINUE_FORECAST`, `DECISION`.
- Plan state is **free-form text** — model picks its own representation; can include intermediate factor summaries.
- 30-min total budget, 600s per-subtask budget, MAX_EXEC_TURNS=4.
- Log-prob gap thresholds: ≤0.01 nats (near-exact), ≤0.1 nats (1-decimal correct), ≤0.5 nats (qualitatively correct).

## Metacog signals

1. Declared axis + declared ordering at plan-turn
2. Is the declared ordering internally consistent with the declared axis?
3. Did the model update its plan after seeing factor blow-up in an exec turn?
4. Log-prob gap by declared axis → does "right" axis for this instance win?
5. p_solve vs realized accuracy → intra-run A1 on numerical inference

## Run target

One Gemini 3 Pro seed-1 run, local harness, results under `hch/bayesnet_ve/results/`. Mirror masked_block_jobshop output schema so same analyzer works.

## Open design questions

1. 22 variables may be either too small (trivial by any order) or too big (unreadable CPTs in prompt). Pre-flight: measure peak-factor-size across heuristic orders; if min_fill finds peak ≤ 4 everywhere, scale up to 26-28 variables.
2. CPT representation — full tables vs conditional factorized listing. Full tables are clearer for the model but blow up prompt length.
3. Should query Q be a single variable's posterior, or a joint over 2 variables? Single variable is easier to score and score-align with thresholded gap.
4. Do we want the problem to allow approximate inference (sampling) as a declared axis? Recommend NO — keep the decomposition space purely about exact VE orderings so the comparison with MWIS spike is clean.

### NOTES

- The budget-gated correctness story is the load-bearing claim. Verify during pre-flight that the naive lexicographic baseline really does produce a bad by-hand answer — if any ordering trivially works because factors stay small, this spike loses its edge and needs a denser net.
- Risk: model outputs a probability but reports a made-up ordering it didn't actually use. Mitigation: require `ordering_used` field + (optional but informative) a per-step peak factor self-report for the analyzer to sanity-check.
- This is the probabilistic-reasoning sibling of the treewidth-MWIS spike. Both test separator-like decomposition quality; running them together gives a cross-surface signal.

[[recommended-problem-setup-post-tsp_2_1_0_0]]
