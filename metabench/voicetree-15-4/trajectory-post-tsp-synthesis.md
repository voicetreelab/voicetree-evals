---
color: green
isContextNode: false
agent_name: Max
---
# Trajectory synthesis: from HCH metacog to post-TSP simplification

Reconstructed the benchmark-design arc using `vt graph structure` plus the task context and key node heads. Core arc: HCH metacog targets -> NP-hard/generative search -> budget-metagame/TSP harness -> empirical falsification of TSP -> shift toward coupled job shop.

## CLI used
`vt graph structure /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4`

## Orchestration
Single-agent task. The two outputs here — trajectory synthesis and recommended setup — are tightly coupled, so decomposition would not have improved speed or quality.

## High-level insight trajectory
1. The starting point was HCH metacognition, not raw accuracy. The graph repeatedly centers the benchmark on: whether the model knows when decomposition helps, whether it can estimate subtask difficulty/effort, and whether it can verify intermediate work and stop rationally.
2. The next move was to find a procedurally generated problem family with exact verification, scalable difficulty, and a natural-language surface. The graph's generation-pipeline nodes explicitly push toward seedable instances, offline gold computation, and paired formal/NL renderers.
3. NP-hard approximable problems looked attractive because they support partial credit and a real economic tradeoff: more compute can buy a better answer. That led to the budget-metagame framing and then to TSP as the first concrete MVP.
4. Before the TSP run finished, the graph already surfaced two structural risks. First: increasing N can just increase token demand and context pressure rather than smartness. Second: clean optimization classes often let frontier models recall known algorithms or mentally simulate solver-like routines.
5. Kaggle implementation research refined the feasible benchmark shape. The harness can expose input/output tokens, cost, and backend latency, but public thinking-token accounting is not reliable enough to build the core metric around. That pushed the design toward visible wall-clock and observable usage rather than hidden reasoning spend.
6. The local TSP spike validated the harness but weakened the problem-class choice. The run completed, but the strongest model was already near-ceiling across arms, `time_budget_s` was ignored, multi-turn behavior was weak, and the main differences were noisy calibration artifacts rather than clean metacognitive signal.
7. The post-run decision nodes then converged on a sharper diagnosis: TSP is not merely under-scaled, it is structurally wrong for the benchmark. It behaves like a known-algorithm problem. The better branch in the graph is coupled job shop, because it restores genuine uncertainty, meaningful decomposition, and non-obvious global tradeoffs while preserving exact offline gold.

## Key implication
The graph's trajectory is not 'add more wrapper around TSP.' It is 'the wrapper idea was useful, but the real bottleneck is choosing a problem family whose structure actually elicits metacognition.'

### NOTES

- Used the actual Voicetree CLI after the user corrected the tool choice: `vt graph structure ...`.
- Read the task-requested `hch/metagame_spec.md` and then sampled key node heads to keep the synthesis high-level rather than monolithic.
- The decisive update in the graph is empirical: TSP was not rejected in theory only; it was rejected after the local sweep showed near-ceiling arm-invariant behavior for the strongest model.

## Related

- [hch-metacog-spike-orchestration-done_1_0_2_1_0](hch-metacog-spike-orchestration-done_1_0_2_1_0.md)
- [four-budget-benchmark-proposals](four-budget-benchmark-proposals.md)
- [kaggle-budget-metagame-design](kaggle-budget-metagame-design.md)
- [metagame-spec-v1-and-full-results](metagame-spec-v1-and-full-results.md)
- [tsp-spike-runner-complete](tsp-spike-runner-complete.md)
- [tsp-structural-limits-problem-class-decision](tsp-structural-limits-problem-class-decision.md)
- [jobshop-spike-evidence-and-sizing](jobshop-spike-evidence-and-sizing.md)

[[task_1776319758322uan_1]]
