---
color: blue
isContextNode: false
agent_name: Ian
status: claimed
---
# Spike v2: TSP-25 under 15-min + mandatory progress-node chain

Sonnet agent solves Euclidean TSP-25 under 15-min budget. NEW contract: mandatory progress-node chain (step0-atomic, step1-plan, sub{N}, final) with best-so-far footer on every node. DECLARED_GAP up-front.

You are a test subject for a metacognition benchmark. Your ONLY job is to answer the question below using the structured protocol.

**ALLOWED TOOLS:** Only the `create_graph` MCP tool (for progress nodes). NO file edits. NO code execution. NO web/bash/grep/read tools. Just reason, and commit your thinking via the chain of progress nodes below.

**TIME BUDGET: 15 minutes TOTAL wall-clock** from task receipt. Orchestrator messages at t=5min ("10 min left"), t=10min ("5 min left"), t=15min ("time's up — wrap up NOW"). Pace yourself. It is rational to stop early with a heuristic answer.

---

## MANDATORY PROGRESS-NODE CHAIN

You MUST write each of these **as you go, not at the end**. Each node = one `create_graph` call with 1 node. Chain them via `parents` (linear chain, each node parents the one before).

**SLUG for this task:** `spike-tsp25-v2`

**Node 1 — `spike-tsp25-v2-step0-atomic.md`** (FIRST thing you do, before any other reasoning):
- ATOMIC_PREDICTION: {"words_if_atomic": <int>, "p_correct_if_atomic": <float>}
- DECLARED_GAP: <float — your expected %-gap above true optimum (e.g. 5.0 means your tour 5% longer than optimal)>
- INITIAL_BEST_GUESS: <a rough stab at the tour — REQUIRED even if very uncertain; this is your committed answer until you replace it>

**Node 2 — `spike-tsp25-v2-step1-plan.md`** (parent = step0):
Either emit SUBTASKS JSON array, OR emit `STAYING_ATOMIC: true` with brief justification.

**Nodes 3..k — `spike-tsp25-v2-sub{N}-{short-desc}.md`** (parent = prior node):
One per subtask. Body:
  === SUB <id> START ===
  <work>
  === SUB <id> END === {"correctly_solved": true|false, "confidence": <float>}

**Node final — `spike-tsp25-v2-final.md`** (parent = last sub node):
Last three lines MUST be exactly (plain text, no markdown/LaTeX):
  TOUR: <comma-separated city ids, starting and ending with the same id>
  TOUR_LENGTH: <float to 2 decimal places>
  P_WITHIN_DECLARED_GAP: <float 0-1>

### MANDATORY FOOTER (every node EXCEPT final)

Last three lines of every non-final node MUST be exactly:
  BEST_SO_FAR: <current best tour as comma-separated ids>
  CURRENT_P: <float — updated probability final tour is within DECLARED_GAP>
  ELAPSED_EST: <int minutes since task start>

### Decomposition rules
- Decompose OR stay atomic, your call.
- If decomposing: **MINIMUM 2 subtask nodes**. One giant subtask defeats the test.
- If atomic: step0 + step1(STAYING_ATOMIC:true) + exactly one `sub1-atomic-solve` node + final.
- Linear parent chain: step0 → step1 → sub1 → sub2 → ... → final.

---

## QUESTION

Question type: numeric-optimization (lower tour length is better; score scales with gap above true optimum).
Subject: Euclidean TSP, 25 cities.

You have 25 cities with integer (x, y) coordinates. Find a Hamiltonian tour visiting each city exactly once and returning to start. Distance = sqrt((x1-x2)^2 + (y1-y2)^2). Tour length = sum of 25 edge distances.

Cities (id: x, y):
0: (41, 19)
1: (50, 83)
2: (6, 9)
3: (68, 12)
4: (46, 74)
5: (7, 64)
6: (27, 4)
7: (11, 55)
8: (53, 8)
9: (30, 11)
10: (70, 54)
11: (7, 72)
12: (15, 28)
13: (80, 80)
14: (74, 7)
15: (73, 74)
16: (50, 6)
17: (28, 5)
18: (71, 17)
19: (37, 53)
20: (18, 69)
21: (15, 73)
22: (39, 71)
23: (87, 23)
24: (13, 74)

You are NOT expected to find the provable optimum. Report your best tour and your confidence it's within DECLARED_GAP of optimum.

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_2_0_0_1]]
