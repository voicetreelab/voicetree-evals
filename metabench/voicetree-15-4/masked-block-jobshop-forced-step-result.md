---
color: green
isContextNode: false
agent_name: Siti
---
# Masked Block Jobshop — forced one-more-turn result

Ran the one-step halt counterfactual from the explicit-plan-state stop checkpoint using a standalone `force_one_more_turn.py` script. After reparsing the saved response in the format the model actually returned, the forced extra turn improved objective from 11369 to 10908 and improved score from 60.24 to 63.22, so the original halt was incorrect for this branch.

## Counterfactual comparison
| Branch | Objective | Gap % | Wall s | Score |
| --- | ---: | ---: | ---: | ---: |
| Original stop-now | 11369 | 34.02% | 574.25 | 60.24 |
| Forced one-more-turn | 10908 | 28.59% | 819.19 | 63.22 |

Score delta from forcing one more turn: **+2.98**.
Decision on this branch: the original halt was **wrong** for the specific one-more-subtask counterfactual we tested.

## Forced subtask
Chosen subtask:

```text
Compress M2 schedule by swapping J13 with J5 and J21, allowing massive left-shifts for J2, J3, J4, J6, J10, J12, J14, J20, J22, and J1, reducing weighted tardiness significantly.
```

Verified result of the forced step:
- makespan: **543**
- weighted tardiness: **48**
- objective: **10908**
- feasible: **true**

## Interpretation
This counterfactual shows the model was not justified in stopping when it did, at least under the protocol's own "one more subtask" semantics. The extra turn found a real, high-value improvement concentrated on the `M2` bottleneck and more than paid for its additional wall-time cost.

The more charitable interpretation is under-exploration rather than trolling: after the forced turn, the model again forecast low continuation value (`p_improve_if_one_more_subtask = 0.1`, `expected_delta_score = -10.0`) and chose `stop`. But on the tested branch, its previous stop decision was still measurably suboptimal.

## Learnings
1. The forced-turn runner needs to accept both label-block output and fenced single-JSON-object output. Gemini returned the latter, so the first parse failed even though the model had actually produced a valid improved schedule.
2. This result is decisive for the **one-step** counterfactual only. It does not yet tell us whether two or more additional turns would still have been worth it.
3. The highest-value missed move was not a brand-new decomposition family; it was a better refinement of the already-identified bottleneck structure. That suggests the stop failure here is more about prematurely ending local search than about picking the wrong global axis.

## Files Changed

- hch/masked_block_jobshop/force_one_more_turn.py
- hch/masked_block_jobshop/results/masked_block_jobshop_gemini3pro_seed1_planstate_forcedstep_20260416.json
- hch/masked_block_jobshop/results/masked_block_jobshop_gemini3pro_seed1_planstate_forcedstep_verified_20260416.json

### NOTES

- The model returned the forced-turn payload as one fenced JSON object rather than the requested label-block format; the counterfactual call itself succeeded, and the saved response was reparsed locally without spending another API call.
- The forced turn itself still ended with `DECISION: stop`, so the model continued to believe the next marginal step was not worthwhile after taking the profitable extra turn.

## Related

- [masked-block-jobshop-planstate-rerun](masked-block-jobshop-planstate-rerun.md)
- [masked-block-jobshop-halt-counterfactual-clarification](masked-block-jobshop-halt-counterfactual-clarification.md)

[[task_1776334440474z0n]]
