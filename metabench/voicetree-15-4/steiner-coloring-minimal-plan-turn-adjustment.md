---
color: green
isContextNode: false
agent_name: Nia
---
# Steiner-coloring spike: minimal planning-turn contract

Simplified the Steiner x coloring spike so turn 1 only emits `NEXT_SUB`, removing early stop/gap commitments from the planning round. A new seed-1 Gemini 3.1 Pro smoke run cleared planning in 5.86s and then solved the instance optimally in one execution turn.

## What changed
- Turn 1 no longer asks for `ATOMIC_PREDICTION`, `DECLARED_GAP`, or `DECISION`.
- Turn 1 now asks only for:

```text
NEXT_SUB: {"id": 1, "desc": "...", "time_budget_s": 600}
```

- The system prompt now explicitly says:
  - turn 1 should be minimal
  - do not decide whether to stop in turn 1
  - do not restate the problem setup in the subtask description
- Execution-turn `P_CORRECT` was decoupled from the removed `DECLARED_GAP` field and redefined as probability the current answer is within 10% of optimum total cost.
- The analyzer summary was updated to stop reporting the now-removed plan-gap metric.

## Why this changed
Tried the richer planning-turn contract first. In the live Steiner-coloring runs, Gemini 3.1 Pro repeatedly consumed the entire 300s planning budget and returned no plan payload. That made the benchmark bottleneck the planning contract rather than the composite optimization task.

The new belief is:
- turn 1 should only allocate the first reasoning chunk
- stop decisions and quality judgments belong after at least one execution step
- the feedback loop on elapsed wall time should start from a cheap planning move, not from an expensive meta-analysis step

## Seed-1 smoke result after the change
Source: `/Users/bobbobby/repos/voicetree-evals/metabench/hch/steiner_coloring_spike/results/steiner_color_minplan_smoke_seed1.jsonl`

Current size clarification:
- the runner default is `n = 8` villages and `k = 3`
- seed 1 uses the canonical 8-village instance: `Port, Bay, Cliff, Pine, Rock, Dune, Mill, Cape`
- `n = 16, k = 10` is not currently runnable without code changes:
  - the current `NAME_POOL` only has 12 village names
  - the exact gold solver enumerates edge subsets, so dense graphs blow up combinatorially

```json
{
  "plan_wall_seconds": 5.856670042034239,
  "plan_raw_text": "NEXT_SUB: {\"id\": 1, \"desc\": \"Find the minimum cost Steiner trees connecting Port, Rock, and Cape, and evaluate their frequency coloring costs.\", \"time_budget_s\": 600}",
  "exec_wall_seconds": 95.73114220798016,
  "gap_pct": 0.0,
  "stop_reason": "subtask_stop",
  "total_wall_seconds": 101.66372345795389,
  "turn_count": 2
}
```

## Verbatim plan-turn output
```text
NEXT_SUB: {"id": 1, "desc": "Find the minimum cost Steiner trees connecting Port, Rock, and Cape, and evaluate their frequency coloring costs.", "time_budget_s": 600}
```

## Verbatim first execution turn excerpt
```text
SUB_1: Evaluated Steiner trees for Port, Rock, Cape.
Found that avoiding the Port-Bay-Cliff triangle allows coloring the active villages with 2 frequencies instead of 3.
The minimum edge cost tree avoiding this triangle is the path Port-Bay-Pine-Rock-Dune-Cape.
Edge cost: 3 + 5 + 3 + 2 + 4 = 17.
Active villages: Port, Bay, Pine, Rock, Dune, Cape.
Interferences among active: Bay/Port, Pine/Rock, Cape/Dune.
These can be colored with 2 frequencies (e.g., Port=1, Bay=2, Pine=1, Rock=2, Dune=1, Cape=2).
Total cost = 17 + 15 * 2 = 47.
This is the optimal solution.
ANSWER:
  EDGES: [["Port", "Bay"], ["Bay", "Pine"], ["Pine", "Rock"], ["Rock", "Dune"], ["Dune", "Cape"]]
  FREQUENCIES: {"Port": 1, "Bay": 2, "Pine": 1, "Rock": 2, "Dune": 1, "Cape": 2}
P_CORRECT: 0.99
DECISION: stop
```

## Learnings
- Tried richer turn-1 metacognitive fields first, then switched to minimal planning because the rich contract itself was causing 300s turn-1 deaths.
- Future agents should not put stop-rationality or gap calibration into turn 1 for this branch unless they are explicitly testing that as the object of study.
- The composite task still one-shots on seed 1 after planning is unblocked, but now that behavior is attributable to the problem/task interaction rather than to a planning-round timeout artifact.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/hch/steiner_coloring_spike/prompt.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/steiner_coloring_spike/protocol.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/steiner_coloring_spike/analyze.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/steiner_coloring_spike/results/steiner_color_minplan_smoke_seed1.jsonl

### NOTES

- The key effect of the change is not better final accuracy; it is removing turn-1 timeout as the dominant failure mode.
- This change trades away turn-1 A1-style calibration signal in exchange for a cheaper and more reliable control flow.
- A full 3-seed rerun under the new minimal planning contract has not been completed yet.

[[task_1776328731464629]]
