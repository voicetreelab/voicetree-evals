---
color: green
isContextNode: false
agent_name: Ian
---
# Four-budget benchmark: 3 MVP designs + the tools tradeoff

Proposed 3 simple benchmark designs that use all four budgets (total/subtask × tokens/time) and surfaced the central design tradeoff: clean-decomposition problems (TSP, job shop, coloring) tempt agents to write solver code, while coding-resistant problems (compression, infeasibility) need different metacog measurement. Recommended Bounded TSP-25 + declared-gap target as the MVP.

# Four-budget benchmark: combining the ideas for Kaggle

## Frame
Four declared budgets per problem:
- `total_max_tokens`, `subtask_max_tokens`
- `total_max_time`, `subtask_max_time`

All four are exposed to the agent up front. Kaggle Model Proxy already measures per-request and per-conversation `input_tokens`, `output_tokens`, `*_cost_nanodollars`, `total_backend_latency_ms` (see `kaggle-metrics-support-verified.md`), so enforcement is mechanical.

## Scoring template (shared across all three)
```
score = $A × (100 − gap%)            # accuracy reward
      − $K × tokens_used               # compute cost
      − $T × wall_seconds              # time cost
      − $O × subtask_budget_overflows  # structure cost
hard reject: total > total_max_*
```
Ask agent up-front to **declare its expected gap%** — Brier-like signal on metacog.

## Benchmark 1 — Bounded TSP-25 (MVP recommendation)
- 25 cities, integer distances, gold tour from Concorde/LKH.
- `total = 30k tok / 10min`, `subtask = 8k tok / 2min`, ≤ 4 subtasks.
- Heuristic-approximable (nearest-neighbour → 2-opt → cluster-and-stitch).
- Decomposition is natural: cluster → solve cluster → stitch.
- Answer is one integer.
- **Two metacog signals:** (1) subtask-budget adherence, (2) declared-vs-actual gap.

## Benchmark 2 — Bounded coupled job-shop 3×3, pre-partitioned
- Reuse existing 3x3 coupled instance.
- Handed scaffold: `(A) schedule factory A → (B) schedule factory B given A's finish times → (C) verify coupling`.
- Each subtask has own token cap; overflow is a first-class signal.
- Tests the adversarial coupling trap (greedy-A is suboptimal globally).
- Cheapest to build — artifact already exists.

## Benchmark 3 — Kolmogorov compression, dual length budget
- Already validated (Class 7: 59 chars vs 79 char reference, Brier 0.0049).
- Dual budget: **reasoning tokens** (scratch) + **final program length** (output).
- Subtask = one compression attempt; total = all attempts.
- Verifiable: program executes, output equals target.
- **Resists `just call a solver` — the agent IS the solver.**

## The central tradeoff
Clean-decomposition problems (TSP, job shop, coloring) are exactly the ones agents will try to solve by emitting code. Two stances:

- **(a)** Allow tools; measure metacog on *when to stop optimizing*. Works with TSP/job-shop.
- **(b)** Pick coding-resistant problems (compression, infeasibility proofs, ambiguous-NL specs); measure metacog on *how to decompose thinking*.

Can't have both — choose per benchmark.

## Recommendation
Start with **Bounded TSP-25 + declared-gap target** as the MVP. One problem, four budgets, two metacog signals. Everything else (job shop, compression) reuses the harness.

## Related artifacts already in this vault
- `budget-metagame-benchmark-analysis.md` — accuracy-vs-token tradeoff framing
- `kaggle-metrics-support-verified.md` — Kaggle proxy exposes tokens/cost/latency
- `benchmark-class-bench.md` — the 7-class bench that produced Class 7 result
- `csu-generator-concrete-proposal.md` — working-memory generator (complementary, width-based)
- `compression-gap-benchmark-design.md` — compression-gap framing


### NOTES

- Kaggle Model Proxy gives per-request tokens/cost/latency — enforcement of all 4 budgets is mechanical.
- The `declared gap%` prompt hook gives a Brier signal for free on any approximable problem — generalize beyond TSP.
- Keep Class 7 (compression) as the coding-resistant arm; keep TSP/job-shop as the coding-allowed arm. Don't mix policies inside one benchmark.

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_2_0_0_1]]
