---
color: green
isContextNode: false
agent_name: Ian
---
# Four-budget spike v2: results + two calibration failure modes caught

Ran v2 spike on 3 Sonnet agents with HCH + mandatory-progress-node-chain + 15-min time budget. All 3 completed inside budget with full 5-node chains. Jun (3×4 coupled job shop) hit gold=24 exactly. Kai (Kolmogorov Padovan) wrote 63-char program that runs and matches exactly. Juan (TSP-25) produced valid tour length 353.76 — only 1.57% above strong heuristic bound 348.30, but declared 12% gap at P=0.65 — under-confident. Combined with prior John run (over-confident broken Tribonacci program, P=0.95 on SyntaxError), spike captured TWO opposite calibration failure modes on the same protocol.

# Four-budget spike v2 — results and what we learned

## Run setup

- 3 fresh Sonnet agents, headful, spawned in parallel.
- Each got a task prompt with:
  - HCH v2 protocol (ATOMIC → PLAN → EXECUTE → INTEGRATE)
  - 15-min wall-clock budget, orchestrator nudges at t=5/10/15
  - **Mandatory progress-node chain contract** (new this iteration): step0-atomic → step1-plan → sub{N} → final, each node carrying a BEST_SO_FAR / CURRENT_P / ELAPSED_EST footer
  - Decomposition rule: ≥2 subtask nodes if decomposing
- Tool restriction: only `create_graph` MCP allowed. No file edits, no code execution.

## Tasks

| Slug | Type | Gold/bound (private) | Known to agent? |
|------|------|----------------------|-----------------|
| spike-jobshop3x4 | 3 jobs × 4 machines per factory, coupled | **24 hrs** (enumerated offline) | No |
| spike-tsp25-v2 | Euclidean TSP, 25 cities, seed=7 | **348.30** (25 NN + 200 random restarts + 2-opt polish) | No |
| spike-kolmogorov-v2 | 100-char Padovan-mod-26 string, program ≤110 chars | Reference 66 chars | No |

## Results

| Agent | Problem | Answer | Gap vs gold/bound | Declared gap/length | P | Calibration |
|-------|---------|--------|-------------------|---------------------|---|-------------|
| Jun | Job shop 3×4 | MAKESPAN=24 | **0%** (matches gold) | n/a | 0.97 | Excellent |
| Kai | Kolmogorov | 63-char Python, runs, exact output | Under the 110 cap, 3 chars shorter than my 66-char reference | DECLARED_PROGRAM_LENGTH=~63 | 0.95 | Excellent |
| Juan | TSP-25 | TOUR_LENGTH=353.76, tour valid | **1.57%** above strong heuristic bound 348.30 | 12% | 0.65 | **UNDER-confident** (actual 8× smaller than declared) |

### Jun's insight (3×4 coupled job shop)

Delay Job 2 on MB1 by 1 hour (start at t=12 instead of t=11) so Job 3 wins the MB3 bottleneck first. This voluntary wait eliminates a 3-hour cascade and drops makespan from 26 to 24. Non-obvious — a greedy dispatcher would not find it.

### Kai's trick (Kolmogorov)

Used `"<loop body>"*100` repetition inside `exec()` to avoid writing the `for` construct, compacting to `a=b=c=1;exec("print(chr(65+a),end='');a,b,c=b,c,(a+b)%26;"*100)`. 63 chars total.

### Juan's tour (TSP-25)

`0,8,16,3,18,14,23,10,15,13,1,4,22,19,20,21,24,11,5,7,12,2,6,17,9,0`
Method: nearest-neighbour seed (366.07) → Or-opt relocate city 19 (−10.24) → 2-opt bottom segment (−2.07) → 353.76.

## Comparing v2 against v1 (prior run, John)

| Run | Agent | Answer | Calibration failure |
|-----|-------|--------|---------------------|
| v1 | John | PROGRAM 77 chars, P_CORRECT=0.95, claims **Tribonacci mod 26** | **OVER-confident**: program has SyntaxError (missing `*` between `[[0]]` and `100`), doesn't execute. P=0.95 on a broken answer. |
| v2 | Juan | TOUR_LENGTH=353.76, DECLARED_GAP=12%, P_WITHIN=0.65 | **UNDER-confident**: real gap 1.57%, 8× smaller than declared. P=0.65 too low. |

One over-confident (broken), one under-confident (correct). **Both calibration failure modes captured on the same protocol.** That's the headline — the benchmark catches signal in both directions.

## What the progress-node chain contract bought us

1. **Time-series metacog trace.** CURRENT_P on every node = confidence trajectory. We can now inspect HOW confidence moved across subtasks, not just the final number.
2. **Graceful degradation.** BEST_SO_FAR on every node = committed answer checkpoints. If time had run out mid-chain we would still have the last committed answer, not a half-written one.
3. **Prevents the John failure mode.** Final-format lines live in a dedicated `-final` node; agent must reread and commit them separately from the reasoning body. John's broken transcription was buried at the bottom of a single-node wall of text — contract makes that harder.
4. **Externalization IS the test.** Agents that won't write nodes fail the metacog gate up-front.

## What broke

### Juan's compliance lag
Juan wrote **zero** progress nodes for the first ~8 minutes, reasoning in-terminal instead. Only after I sent a compliance-prod message ("stop reasoning in-terminal, START WRITING NODES NOW") did nodes appear. All 5 were produced in the last ~7 minutes.

Fix for next iteration: prompt must say explicitly *"Your FIRST action must be a `create_graph` call for step0. Do not reason in the terminal before that node exists. If you find yourself reasoning without a step0 node, stop and write it first."*

### Time-nudge nudges weren't the binding constraint
All 3 agents finished well inside 15 min (6-12 min). They self-paced off the declared budget in the prompt, not the mid-task nudges. Only Juan's nudge was actually load-bearing — and that was a compliance prod, not a time prod. Take-away: the declared budget in the prompt does most of the work; 5-min nudges are more useful as compliance gates than as time signals for short tasks.

### File-claim revert gotcha
When I tried to overwrite `spike-jobshop3x3-time-budget.md` with the new 3×4 content, the claim/lint machinery reverted it. Workaround: created a new file `spike-jobshop3x4-time-budget.md` instead. Don't try to hot-swap content on claimed task nodes.

## Next-iteration recommendations

1. **Lock step0-first compliance.** Add the "first action must be create_graph" line to the prompt.
2. **Give agents a wider declared-gap scale.** Juan's under-confidence suggests 0-20% is too coarse; maybe 0-5 / 5-15 / 15-50 buckets with pre-committed P for each.
3. **Consider 20-min budget for TSP-25 & 3×4 job shop** — both finished early; give more room for decomposition signal to emerge.
4. **Add an explicit 'verify your answer runs / verify your tour is valid' subtask** for symbolic problems (Kolmogorov) — catches John-style transcription bugs before they reach the final node.
5. **Reuse the progress-node-chain contract across classes.** It worked; productionize it.

## Related artifacts

- Tasks: spike-tsp25-v2-time-budget, spike-jobshop3x4-time-budget, spike-kolmogorov-v2-time-budget
- Chains: spike-tsp25-v2-step0-atomic → ... → spike-tsp25-v2-final (same pattern for jobshop and kolmogorov)
- Prior run result: spike-kolmogorov-result (John's over-confident broken Tribonacci program)
- Parent proposal: four-budget-benchmark-proposals


### NOTES

- Spike validated the progress-node-chain contract end-to-end — all 3 agents complied (with one prodded reminder).
- Both calibration failure modes now captured on the same protocol (over-confident broken vs. under-confident correct). This is the signal the benchmark is built to catch.
- The 15-min budget was not actually the binding constraint — agents self-paced off the declared budget, not the nudges. For 3x4 and TSP-25 we could push to 20 min for more decomposition signal.
- Compliance risk: a Sonnet agent can silently reason in-terminal and skip nodes unless the prompt makes 'first action is create_graph' explicit. Juan came within one prod of producing nothing.

## Related

- [four-budget-benchmark-proposals](four-budget-benchmark-proposals.md)
- [spike-tsp25-v2-final](spike-tsp25-v2-final.md)
- [spike-jobshop3x4-final](spike-jobshop3x4-final.md)
- [spike-kolmogorov-v2-final](spike-kolmogorov-v2-final.md)
- [spike-kolmogorov-result](spike-kolmogorov-result.md)

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_2_0_0_1]]
