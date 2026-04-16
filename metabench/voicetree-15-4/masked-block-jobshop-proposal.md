---
color: green
isContextNode: false
agent_name: Sai
---
# Masked Block Jobshop — indeterminate-boundary proposal

Concrete jobshop design with hidden SBM family structure, bridge jobs, competing bottlenecks, outliers, and due-date tension — four competing decomposition axes, no single recipe wins.

## Core design

**25 jobs × 15 machines**, weighted makespan + tardiness objective, 30-min budget. Model sees only the operation matrix + processing times + due dates + tardiness weights. No family labels, no bottleneck markers, no outlier tags.

## Hidden generation (what makes boundaries indeterminate)

- **Latent families via SBM.** 4 hidden clusters (6–7 jobs each), each with a preferred 5-machine set. 80% of a cluster's ops on preferred machines; 20% leak to OTHER clusters' preferred machines → families overlap by construction.
- **Bridge jobs.** 2 jobs per cluster route through 2+ families' preferred machines → genuinely ambiguous cluster membership. Any partition faces the question: where do these go?
- **Competing bottlenecks.** 3 cross-family shared machines + 4 intra-family local bottlenecks = 7 candidates for "the bottleneck." Load isn't monotone with raw processing time (shifting-bottleneck phenomenon).
- **Outlier jobs.** 5 jobs at 3× processing time, scattered across families — sequencing them drives makespan but splinters any clean family cut.
- **Due-date tension.** 30% of jobs (mostly non-outliers) on tight deadlines with high tardiness weight. Deadline-aware scheduling beats makespan-only.

## Competing decomposition axes

| Axis | Cut on | Cheap piece | Expensive residual |
|------|--------|-------------|--------------------|
| Bottleneck-first | Shared-machine sequence first | Clear critical path | Local bottlenecks + tardiness unresolved |
| Family-first | Detect clusters, solve each, reconcile on shared | Small clean CP-SAT pieces | Shared-machine conflicts + bridge jobs |
| Outlier-first | Sequence 5 long jobs, fill around them | Makespan backbone | Tardiness blows up |
| Due-date-first | Tight-deadline jobs up front | Good tardiness | Outliers pushed late → makespan inflates |
| Composite priority | Per-job f(deadline, length, load) | Multi-axis capture | Model-dependent; metacog-rich |

## Why this is genuinely indeterminate

- Family-first forces the model to *detect* clusters (modularity on job-machine bipartite) AND *place bridge jobs* — two non-trivial choices with real quality consequences.
- Bottleneck-first forces identification of the actual binding machine — not the raw-load winner, because sequencing shifts load.
- The axes aren't compatible — choosing one sacrifices what another captures. No named algorithm covers the composite.
- Boundaries aren't handed by the problem; they must be inferred and defended.

## Gold + baseline

- **Gold:** CP-SAT on full composite (makespan + weighted tardiness), runs in minutes.
- **Baseline:** SPT dispatching heuristic; typical 20–30% gap vs gold, leaving real headroom.

## Metacog signals

1. Declared decomposition axis at plan-turn + declared cut (which machines/jobs grouped)
2. Per-subproblem declared p_solve vs realized subproblem quality → intra-run A1
3. Cross-axis realized quality → "did the model pick the right axis for this instance?"
4. AUC of partial-quality over turns → rewards decompositions that front-load informative pieces
5. Plan revision: did the model swap axes after seeing a subproblem result?

## Phase-transition ablation

Run 15×10 / 25×15 / 40×25 variants. Predicted: recipes hold at 15×10 (one-shot), break at ≥25×15 (forced exploration). 25×15 is the sweet spot for the metacog regime.

## Integration with existing harness

- Same operation-matrix representation as Mei's 6×7 harness
- Same CP-SAT gold path
- Same NL surface
- Net new: richer instance generator (SBM + overlap + outliers + due-dates) + composite objective + plan-axis declaration in plan-turn schema

## Open design questions

1. Tune SBM overlap parameter — how fuzzy is "genuinely indeterminate" without becoming noise?
2. Are 4 families the right count? Too few → family-first is trivial; too many → working-memory test.
3. Should plan-axis be a declared enum (5 options) or free-form NL? Enum cleaner for scoring; free-form catches hybrid strategies.
4. Tardiness weight vs makespan weight ratio — needs tuning so no single axis dominates.

### NOTES

- Axis 5 (composite priority) is where rich metacog behavior is most likely to emerge — but hardest to score because it's diffuse. Consider making axis declaration an enum of 4 with "other + describe" as a fifth option.
- Bridge-job placement is the cleanest single test of indeterminate boundary reasoning. Could be isolated as a mini-benchmark on its own.
- Risk: if CP-SAT solves 25×15 trivially at gold, the gap collapses and A1 loses discriminative power. Pre-flight: measure CP-SAT vs SPT gap on sample instances before committing.

[[recommended-problem-setup-post-tsp_2_1]]
