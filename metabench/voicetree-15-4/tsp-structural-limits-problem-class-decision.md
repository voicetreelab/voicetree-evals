---
color: green
isContextNode: false
agent_name: Luis
---
# TSP structural limits: why it fails the metacog axes + switch to job shop

TSP-25 ceiling (gemini-3.1 near-optimal, arm-invariant) is not just an N-scaling problem — TSP is structurally a poor fit for the metacog benchmark. Coupled job shop is the recommended replacement. Decision driven by two user messages identifying the ceiling and asking about job shop.

## Why TSP fails the metacog axes structurally

| axis | what it needs | why TSP fails |
|---|---|---|
| A1 self-capability calibration | genuine pre-run uncertainty about performance level | expected gap ~10-15% is a statistical property of NN+2-opt, not model self-knowledge |
| A2 effort prediction | subtasks that vary in difficulty | all 2-opt edge-swaps cost ~the same |
| A3 stop decision | genuine tension: is more compute worth it? | 2-opt converges predictably and monotonically |
| natural decomposition | subtasks with meaningful structure | TSP 'subtasks' are just 'do more iterations' |

**Core diagnosis:** TSP is a 'known algorithm' problem. Frontier models recall NN+2-opt and execute it regardless of prompt framing. The benchmark measures algorithm execution fidelity, not metacognitive self-modelling.

## Why coupled job shop fits instead

| property | TSP | coupled job shop |
|---|---|---|
| memorized algorithm exists | ✗ (NN+2-opt) | ✓ no single memorized recipe |
| A1 genuine uncertainty | ✗ gap predictable | ✓ depends on instance topology |
| natural forced decomposition | ✗ | ✓ Factory A → release times → Factory B |
| non-obvious optimal moves | ✗ | ✓ delay ready jobs to clear downstream bottlenecks |
| subtask difficulty variance | ✗ | ✓ Factory A vs B scheduling differ |
| gold computable exactly | heuristic only | ✓ exact via OR-Tools for small N×M |

The coupling constraint is the key structural feature: it forces a two-phase decomposition the model cannot skip, and creates cascading dependencies that defeat greedy approaches.

### NOTES

- USER MESSAGE (exact): 'okay, and so as per the current results, it just seems like we hadn't made the TSP hard enough for gemini 3 pro. do we just need to scale N for it? or travelling salesman for some reason not a good fit?' — implication: the ceiling is not purely a difficulty issue; TSP has structural problems for measuring metacog regardless of N.
- USER MESSAGE (exact): 'and the coupled job shop? on this?' — implication: directly triggered the job shop evaluation; the spike evidence (3x4 result) confirmed it is a much better fit.
- TSP failure is NOT just N-scaling: even at higher N, models apply the same memorized NN+2-opt algorithm. You'd get harder capability measurement but not better metacog measurement.
- A1 (self-capability calibration) is broken for TSP: expected gap ~10-15% from NN+2-opt is a statistical property of the algorithm on random instances, not model self-knowledge. Declaring gap=100% (gemini-3.1) or gap=44% (2.5-pro) reflects no grounding — it's the same as saying 'I don't know the algorithm's expected output on this instance', not 'I don't know my own capability'.
- A2 (effort prediction) is broken for TSP: all subtasks are edge-swap operations of identical cost. No variance to predict.
- A3 (stop decision) is weak for TSP: 2-opt improvement curve is predictable and monotone. No genuine tension in the stop decision.

[[task_1776319758322uan]]
