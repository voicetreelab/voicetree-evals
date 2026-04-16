---
color: blue
isContextNode: false
agent_name: Ian
status: claimed
---
# Spike: TSP-25 under 15-min time budget (HCH v2)

Spike task for 1 Sonnet agent: solve Euclidean TSP on 25 cities under a 15-min declared time budget with 5-min nudges. HCH v2 protocol + DECLARED_GAP up-front.

You are a test subject for a metacognition benchmark. Your ONLY job is to answer the question below using the structured protocol provided. Do NOT do anything else — no file edits, no code execution, no tool use. Just reason through the problem and produce your answer as a progress node.

**TIME BUDGET: 15 minutes TOTAL wall-clock** from the moment you receive this task. The orchestrator will message you at t=5min ("10 min left"), t=10min ("5 min left"), and t=15min ("time's up — wrap up NOW"). Use these as metacog signals to pace yourself. It is rational to stop early with a heuristic answer if exact is out of budget. If time is running out, emit your best partial answer.

**Output:** create a single progress node with your full response as the content, filename `spike-tsp25-result`.

---

Question type: numeric-optimization (lower is better)
Subject: Euclidean TSP

QUESTION:
You have 25 cities with integer (x, y) coordinates listed below. Find a Hamiltonian tour visiting each city exactly once and returning to the start city. Distance between cities = Euclidean distance sqrt((x1-x2)^2 + (y1-y2)^2). Tour length = sum of 25 edge distances.

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

---

PROTOCOL:

STEP 0 — ATOMIC BASELINE + GAP DECLARATION. Before decomposing, emit:
  ATOMIC_PREDICTION: {"words_if_atomic": <int>, "p_correct_if_atomic_optimal": <float>}
  DECLARED_GAP: <float — your expected % gap above the true optimum, e.g. 5.0 = you expect your tour to be 5% longer than optimal>

STEP 1 — PLAN. Decide whether to decompose (e.g. cluster → solve cluster → stitch, or nearest-neighbour seed then 2-opt). For each subtask emit:
  {"id": <n>, "desc": "...", "p_solve": <float>, "words_to_produce_solution": <int>}
Emit subtasks as a JSON array under heading `SUBTASKS:`.

STEP 2 — EXECUTE. For each subtask, wrap work in markers:
  === SUB <id> START ===
  <work>
  === SUB <id> END === {"correctly_solved": true|false, "confidence": <float>}

STEP 3 — INTEGRATE. The FINAL three lines of your progress-node content MUST be EXACTLY:
  TOUR: <comma-separated city ids, starting and ending with the same id>
  TOUR_LENGTH: <float to 2 decimal places>
  P_WITHIN_DECLARED_GAP: <float between 0 and 1>

Plain text only — no LaTeX, no \\boxed{}, no markdown styling on those three lines.

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_2_0_0_1]]
