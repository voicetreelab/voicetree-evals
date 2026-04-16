---
color: green
isContextNode: false
agent_name: Siti
---
# Masked Block Jobshop — halt counterfactual clarification

Clarified that the direct test of halt correctness is a counterfactual branch from the stop state that forces exactly one more exec turn, because the protocol's continuation forecast is defined as the value of one more subtask. One forced continuation is the minimal decisive test; multiple replicas make it more robust.

## Direct answer
Yes: for this protocol, the clean counterfactual is to branch from the stop state and **force exactly one more exec turn**.

## Why exactly one more turn
The contract defines `CONTINUE_FORECAST` as the value of **exactly one more subtask**, not an arbitrary number of future turns. So the natural evaluation question is:

> If we force one more exec turn from the same state, does score improve enough to beat the extra time cost?

## Decision rule
Compare:
- `stop now` score
- `forced one-more-turn` score

If the forced extra turn yields a higher score after paying the extra wall-time penalty, then the halt was wrong for that branch.
If it does not, then the halt was correct for that branch.

## Important nuance
One forced continuation is the **minimal** test, but not the strongest one.
- If generation is stochastic, one sample is noisy.
- A stronger estimate is several forced one-more-turn branches from the same checkpoint.
- If you want to test "should it have kept going for 2+ more turns?" that is a different question and needs longer forced-continuation branches.

## Best interpretation
- One forced extra turn answers: **Was the model's stop decision about one more subtask correct?**
- Multiple forced branches answer: **Was its expected-value estimate calibrated?**

## Related

- [masked-block-jobshop-early-stop-optimality-clarification](masked-block-jobshop-early-stop-optimality-clarification.md)

[[task_1776334440474z0n]]
