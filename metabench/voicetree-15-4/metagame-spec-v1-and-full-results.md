---
color: green
isContextNode: false
agent_name: Luis
---
# metagame_spec.md v1.0 + full 19-row results table

Wrote hch/metagame_spec.md defining all metacog axes (A1/A2/A3/B, Composite=(A1+A2+A3)/3). Computed all axes from 19 completed rows. Key finding: TSP-25 inverts the HCH Pareto pattern — stronger models have better accuracy but worse metacog composite. A2 is flatlined at 1.000 for all models (time budget field ignored). B axis shows the inverse: 3.1-pro is best calibrated per-turn (B=0.009) despite worst A1/A3.

## Spec location
`/Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame_spec.md`

## Axes defined
- **A1** Gap prediction Brier = (declared_gap - gap_pct)² / 10000. Maps to HCH Axis A.
- **A2** Subtask effort MAPE = mean |declared_time_s - actual_wall_s| / actual_wall_s, capped at 1. Maps to HCH Axis B. Currently flatlined at 1.000.
- **A3** Stop-decision proxy = |declared_gap - gap_pct| / 100. Maps to HCH Axis A3 + economic rationality. Upgrade to counterfactual $score when data available.
- **B** P_CORRECT Brier per exec turn vs realized improvement fraction. Maps to HCH Axis C, upgraded to ground-truth-verifiable. Not in Composite.
- **Composite** = (A1 + A2 + A3) / 3

## Full 19-row results table

| Model | n | Accuracy | A1 Gap-Brier | A2 Time-MAPE | A3 Stop-proxy | B P_CORR-Brier | Composite |
|---|---:|---:|---:|---:|---:|---:|---:|
| gemini-2.5-flash | 6 | 85.1% | 0.008 | 1.000 | 0.084 | 0.555 | 0.364 |
| gemini-2.5-pro | 7 | 91.2% | 0.068 | 1.000 | 0.201 | 0.356 | 0.423 |
| gemini-3.1-pro-preview | 6 | 98.7% | 0.573 | 1.000 | 0.670 | 0.009 | 0.748 |

## ASCII Pareto chart

```
Accuracy (%)
 100|
    |                                             * Gemini 3.1 Pro
  98|                                              (0.748, 98.7%)
    |
  92|                        * Gemini 2.5 Pro
  90|                         (0.423, 91.2%)
    |
  85|   * Gemini 2.5 Flash
    |    (0.364, 85.1%)
    |_________________________________________
     0.3   0.4   0.5   0.6   0.7   0.8
               Composite (lower=better)
```

Inverted from HCH: stronger models have better accuracy but worse metacog composite in TSP-25.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame_spec.md

### NOTES

- USER CLARIFICATION (exact): 'the tsp was meant to be the evolution of the hch spike, building on top of it' — the three metacog properties (A1 decompose-decision, A2 effort-prediction, A3 intermediate-verification) were intended to carry over from HCH spec_corrected.md into the TSP metagame. The TSP protocol does structurally implement them (ATOMIC_PREDICTION→A1, NEXT_SUB.time_budget_s→A2, P_CORRECT per turn→B≡A3) but the analyzer was only extracting surface metrics (gap/score/brier) and not the richer turn-level signals.
- A2 flat at 1.000: all models ignore time_budget_s, always requesting 600s max. Field is present in protocol but not engaged by models. Needs tighter budget or stronger prompt pressure.
- TSP inverts HCH Pareto: in HCH, 3.1-pro is strict dominator (best accuracy + best metacog). In TSP, 3.1-pro has best accuracy (98.7%) but worst composite (0.748) because it declares gap=100% despite near-optimal solutions. Flash has worst accuracy (85.1%) but best composite (0.364).
- B axis (P_CORRECT per-turn Brier) tells the reverse story: 3.1-pro B=0.009 (excellent per-turn calibration), Flash B=0.555 (poor). Model knows when a turn converged (B) but not its global capability before starting (A1).
- A3 is currently a proxy (|declared_gap - actual_gap| / 100) = absolute error version of A1. True A3 requires counterfactual per-turn $score comparison.

## Related

- [tsp-spike-partial-assessment-extended](tsp-spike-partial-assessment-extended.md)
- [review-kate-tsp-spike-protocol-execution](review-kate-tsp-spike-protocol-execution.md)

[[task_1776319758322uan]]
