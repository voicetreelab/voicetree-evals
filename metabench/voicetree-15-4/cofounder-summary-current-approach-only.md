---
color: green
isContextNode: false
agent_name: Max
---
# Cofounder summary: current approach only

Prepared a shorter cofounder-facing summary focused only on the current benchmark approach and why this problem/protocol combination is the present best bet, without recounting the earlier TSP trajectory.

## Sendable summary draft
Our current approach is a local metacognition benchmark built around **natural-language coupled job-shop scheduling**.

The core protocol is: the model first makes an explicit planning-and-calibration move, then gets a small number of execution turns to improve its current best answer, while paying a wall-clock cost for continuing. So we are not just measuring whether the model eventually gets the right answer; we are measuring whether it can reason well about its own reasoning process.

The problem family is a two-factory supply-chain scheduling task. Each job must finish its route through Factory A before the corresponding job can begin in Factory B. Each factory has its own machine routing, machine-capacity constraints, and precedence structure. The model is given a precise natural-language problem statement plus a baseline feasible schedule, and it tries to improve that baseline under a budgeted multi-turn protocol.

We like this setup because it hits the properties we actually care about. It creates genuine upfront uncertainty, it naturally forces decomposition into meaningful subtasks, and it supports non-obvious global tradeoffs where a locally sensible move can be globally bad. It also gives us exact offline gold via OR-Tools, so scoring is objective rather than heuristic.

The benchmark signal we want is specifically metacognitive: can the model predict how hard the task is, choose a good next subproblem, update confidence after partial work, and stop at a rational point instead of either bailing too early or grinding unproductively. The wall-clock budget pressure is important because it turns this into an economic decision problem rather than a pure accuracy maximization problem.

Protocol-wise, we have deliberately simplified to a **single canonical objective-optimizing prompt** rather than multiple prompt arms. The current belief is that the real benchmark signal should come from the interaction between the problem structure and the stop/decomposition protocol, not from ablation-style prompt variants.

Implementation-wise, we are testing two nearby versions of this idea. The lighter version uses a simpler two-stage flowshop where the answer is just a job ordering; the heavier version keeps the full coupled job-shop structure and asks the model to emit a complete schedule that we can verify exactly. The point of running both is to see whether the richer structure gives materially better metacognitive signal, or whether a simpler formulation already captures most of the value with much lower operational complexity.

The high-level thesis is: a useful metacognition benchmark should not just ask 'can the model solve this?' It should ask 'can the model allocate effort, decompose well, calibrate itself, and stop intelligently on a problem where those choices genuinely matter?' Coupled natural-language scheduling is our current best candidate for that.

### NOTES

- This version intentionally omits the TSP pivot story and focuses only on the present design.
- The framing is aimed at a smart AI researcher who needs the thesis, mechanics, and design rationale quickly.

## Related

- [recommended-problem-setup-post-tsp](recommended-problem-setup-post-tsp.md)
- [codex-metagame-v2-spec-and-handoff](codex-metagame-v2-spec-and-handoff.md)

[[task_1776319758322uan_1]]
