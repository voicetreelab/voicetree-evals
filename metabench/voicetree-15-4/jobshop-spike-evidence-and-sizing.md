---
color: green
isContextNode: false
agent_name: Luis
---
# 3x4 job shop spike evidence + recommended sizing for metacog benchmark

The 3x4 coupled job shop spike (Sonnet) showed exactly the metacog signals TSP lacked: genuine upfront uncertainty (p_correct_if_atomic=0.55), natural Factory A→B decomposition, and a non-obvious optimal move. Hit exact optimum (makespan=24). Recommended sizing: 4x5 for MVP, 5x6 for frontier tier.

## 3x4 spike metacog signals (Sonnet agent)

```
ATOMIC_PREDICTION: {words_if_atomic: 300, p_correct_if_atomic: 0.55}  ← genuine uncertainty
DECLARED_GAP: 5%
Initial best guess: makespan ~26 (greedy FIFO estimate)
Final result: makespan 24 = TRUE OPTIMUM
P_WITHIN_DECLARED_GAP: 0.97
```

Decomposition: Factory A schedule (Sub1) → Factory B given release times (Sub2). Natural, structurally forced, meaningful.

Key insight found: delay J2 on MB1 by 1 hour to prevent 3-hour cascade at MB3 bottleneck. Non-obvious, non-greedy, correct.

Compare to TSP: gemini-3.1 declared gap=100% with no grounding, identical results across all arms, solved in 2 turns with no genuine uncertainty.

## Recommended instance sizing

| instance | ops per factory | expected difficulty | use for |
|---|---:|---|---|
| 3×3 | 9 | trivial for all models | smoke test only |
| 3×4 | 12 | medium-Sonnet, easy-frontier | calibration baseline |
| **4×5** | **20** | **hard-Sonnet, medium-frontier** | **MVP benchmark tier** |
| 5×6 | 30 | very hard, ceiling-resistant | upper / frontier tier |

## Scoring (same formula as TSP)

```
gap_pct  = 100 × (achieved_makespan − optimal_makespan) / optimal_makespan
Accuracy = 100 − gap_pct
$score   = ACCURACY_REWARD × max(0, 100 − gap_pct) − TIME_PENALTY × total_wall_seconds
```

Infeasible schedule → score as gap_pct = baseline_gap (no improvement credit).

## Gold computation

OR-Tools CP-SAT solver or branch-and-bound. Exact optimal for ≤4×5 instances in seconds. Strictly better than TSP's NN+2-opt heuristic reference — models can be compared against a true ceiling.

### NOTES

- 3x4 was solved optimally by Sonnet — same ceiling risk as TSP-25 for stronger models. Need 4x5 or 5x6 for frontier tiers.
- The non-obvious optimal move in 3x4: deliberately delay J2 in Factory B by 1 hour to cede MB3 to J3, avoiding a 3-hour cascade delay. This is the kind of insight that cannot be found by a memorized algorithm — it requires genuine planning.
- Gold for job shop: exact optimal via branch-and-bound or OR-Tools (seconds for ≤4x5 instances). Strictly better than TSP's heuristic NN+2-opt reference.
- Feasibility constraint: infeasible schedules (violating machine or job ordering) must be penalized. Score infeasible outputs as makespan=baseline (no improvement). This is the main complexity added vs TSP.

evidence + next steps [[tsp-structural-limits-problem-class-decision]]
