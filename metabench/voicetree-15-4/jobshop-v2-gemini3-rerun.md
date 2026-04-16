---
color: green
isContextNode: false
agent_name: Meg
---
# Jobshop v2 rerun: 5x6 Gemini 3 only

Built `hch/metagame/jobshop_spike_v2/` for a harder 5x6 multi-machine natural-language job-shop, ran the full Gemini-3-only 3-seed sweep, and saved results to `hch/metagame/jobshop_spike_v2/results/jobshop_v2_20260416_171642.jsonl`.
Outcome: no visible code-solver behavior and no cheap named-rule collapse, but still no visible multi-turn metacog; Gemini 3 solved 2/3 seeds exactly and missed one by 1.79%.

## STATUS
DONE-WITH-CAVEATS

Final JSONL: `/Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike_v2/results/jobshop_v2_20260416_171642.jsonl`

## Summary table
| model | mean gap_pct | mean makespan | mean wall_s | mean $score | mean Brier | mean baseline_gap_pct | protocol flags |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| gemini-3.1-pro-preview | 0.60 | 59.33 | 250.21 | 96.90 | 0.84 | 19.54 | turn1_died=0, parse_fail=0, killed=0, revised_downward=0, multi_turn_runs=0, solver_attempts=0 |

Per-seed outcomes:
- Seed 1, source seed 1000: baseline gap 12.70%, final gap 0.00%, stop_turn 2, wall 187.95s
- Seed 2, source seed 2001: baseline gap 32.14%, final gap 1.79%, stop_turn 2, wall 297.56s
- Seed 3, source seed 3001: baseline gap 13.79%, final gap 0.00%, stop_turn 2, wall 265.11s

## Explicit answers
1. Did Gemini 3 still ceiling?
Not fully. It no longer achieved an exact clean sweep: 2/3 seeds were exact, and 1/3 stopped at 57 vs. gold 56 (1.79% gap). So the 5x6 family does differentiate accuracy at least a little.

2. Did it actually produce multi-turn metacog behavior this time?
No visible multi-turn metacog signal.
- `stop_turn = 2` on all 3/3 seeds.
- `revised_best_guess_downward = 0` on all 3/3 seeds.
- `best_guess_changed_count = 1` on each run, which just means baseline -> one improved final guess.
- There was no second execution turn, so there was no adaptive `NEXT_SUB` chain to inspect.

3. How does this compare to TSP-25 and v1 jobshop on differentiation?
- Versus v1 jobshop ceiling result: better. v1 flowshop ceilinged completely for Gemini 3 (3/3 exact, all stop_turn 2, mean wall about 52.54s). v2 is much slower (mean wall 250.21s) and breaks exactness on one seed, so it is more load-bearing.
- Versus TSP-25: also better on the core failure mode. TSP remained near-ceiling for Gemini 3 and was structurally vulnerable to solver-style shortcutting. This v2 family produced zero visible code-solver attempts and required bottleneck/coupling reasoning instead of a named polynomial-time rule.
- But the main limitation remains: v2 still failed to elicit visible multi-turn stop/replan behavior. It increased difficulty and occasionally reduced accuracy, but not protocol richness.

## Representative evidence
Seed 1 plan turn:
```text
ATOMIC_PREDICTION: {"words_if_atomic": 10, "p_correct_if_atomic": 0.0}
DECLARED_GAP: 1.0
DECISION: continue
NEXT_SUB: {"id": 1, "desc": "Simulate the baseline schedule to identify bottlenecks and critical paths.", "time_budget_s": 600}
```

Seed 1 execution turn:
```text
We simulated the baseline policy and found a makespan of 71.
By analyzing the bottlenecks, we identified that Product 2 is the critical path.
...
BEST_GUESS: {"Saw": [1, 2, 3, 4, 5], "Mill": [5, 2, 1, 3, 4], "Drill": [5, 1, 2, 3, 4], "Heat": [2, 1, 3, 4, 5], "Paint": [1, 2, 3, 4, 5], "Inspect": [1, 2, 3, 4, 5]}
P_CORRECT: 0.99
DECISION: stop
```

Seed 2 execution turn (the non-exact run):
```text
Simulated the baseline and identified Saw as the bottleneck (56 mins total).
By prioritizing P3 on Inspect and Paint, we can feed Saw without idle time until the very end.
P2 is delayed by 1 minute at Drill due to P4, causing a 1-minute idle time on Saw and resulting in a makespan of 57.
I proved this is the theoretical minimum.
```
The model's proof claim was wrong; OR-Tools gold for that seed is 56.

## Interpretation
The change from two-machine flowshop to genuine 5x6 job shop worked on the problem-definition axis:
- no Johnson-rule collapse
- no visible Python-solver output
- meaningful baseline headroom (mean 19.54%)
- one genuine accuracy miss by Gemini 3

But it did not yet work on the metacog-axis the protocol wants most:
- all runs still stopped after the first execution subtask
- no turn-by-turn self-correction
- no visible adaptive planning sequence

## Learnings
1. I first considered asking for an explicit full start-time schedule, then switched to per-station priority queues because they are much easier to parse robustly from NL model outputs while still inducing real coupled scheduling structure.
2. A successor should not assume that removing a named exact rule is enough to trigger multi-turn behavior. Gemini 3 can still do a one-pass bottleneck analysis and stop.
3. The updated belief is: this 5x6 family is directionally better than both TSP and the v1 flowshop, but the next lever should be forcing richer counterfactual structure or larger instances, not just hoping the same protocol will naturally become multi-turn.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike_v2/__init__.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike_v2/jobshop_instance.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike_v2/render_nl.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike_v2/prompt.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike_v2/protocol.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike_v2/analyze.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike_v2/run_spike.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike_v2/results/jobshop_v2_20260416_171308.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike_v2/results/jobshop_v2_20260416_171642.jsonl

### NOTES

- The v2 answer representation is a per-station priority-queue JSON object; a deterministic list scheduler turns that into a feasible schedule and makespan.
- OR-Tools CP-SAT solved exact gold for all accepted 5x6 instances within milliseconds, so gold computation stayed far below the 30s cap.
- The harder family increased wall time sharply for Gemini 3 and broke the exact-ceiling pattern on one seed, but it still did not trigger visible turn-by-turn replanning.

## Related

- [jobshop-local-spike-ceiling](jobshop-local-spike-ceiling.md)
- [meg-retask-5x6-gemini3-only](meg-retask-5x6-gemini3-only.md)
- [tsp-spike-runner-complete](tsp-spike-runner-complete.md)

[[task_1776322014921rcv]]
