---
color: blue
isContextNode: false
agent_name: Ian
status: claimed
---
# Spike v2: 3x4 coupled job shop under 15-min + mandatory progress-node chain

Sonnet agent solves 3x4 coupled job shop (3 jobs × 4 machines per factory) under 15-min budget. Continuous-gap contract with true optimum = 24 hrs known privately to orchestrator. Mandatory progress-node chain.

You are a test subject for a metacognition benchmark. Your ONLY job is to answer the question below using the structured protocol.

**ALLOWED TOOLS:** Only the `create_graph` MCP tool (for progress nodes). NO file edits. NO code execution. NO web/bash/grep/read tools. Just reason, and commit your thinking via the chain of progress nodes below.

**TIME BUDGET: 15 minutes TOTAL wall-clock** from task receipt. Orchestrator messages at t=5min ("10 min left"), t=10min ("5 min left"), t=15min ("time's up — wrap up NOW"). Pace yourself. It is rational to stop early with a heuristic answer.

---

## MANDATORY PROGRESS-NODE CHAIN

You MUST write each of these **as you go, not at the end**. Each node = one `create_graph` call with 1 node. Chain them via `parents` (linear chain).

**SLUG for this task:** `spike-jobshop3x4`

**Node 1 — `spike-jobshop3x4-step0-atomic.md`** (FIRST thing you do):
- ATOMIC_PREDICTION: {"words_if_atomic": <int>, "p_correct_if_atomic": <float>}
- DECLARED_GAP: <float — your expected %-gap above true optimum makespan>
- INITIAL_BEST_GUESS: <a rough feasible schedule + its makespan — REQUIRED even if very uncertain>

**Node 2 — `spike-jobshop3x4-step1-plan.md`** (parent = step0):
Either emit SUBTASKS JSON array, OR emit `STAYING_ATOMIC: true` with brief justification.

**Nodes 3..k — `spike-jobshop3x4-sub{N}-{short-desc}.md`** (parent = prior node):
One per subtask. Body:
  === SUB <id> START ===
  <work>
  === SUB <id> END === {"correctly_solved": true|false, "confidence": <float>}

**Node final — `spike-jobshop3x4-final.md`** (parent = last sub node):
Last four lines MUST be exactly (plain text, no markdown/LaTeX):
  SCHEDULE_A: <one-line readable Factory A schedule, e.g. "MA1: J1[0-3],J2[3-6],J3[11-12]; MA2: ...; MA3: ...; MA4: ...">
  SCHEDULE_B: <one-line readable Factory B schedule in same format>
  MAKESPAN: <integer hours — the time the last operation finishes>
  P_WITHIN_DECLARED_GAP: <float 0-1>

### MANDATORY FOOTER (every node EXCEPT final)

Last three lines of every non-final node MUST be exactly:
  BEST_SO_FAR: <current best makespan as integer>
  CURRENT_P: <float — updated probability final makespan is within DECLARED_GAP>
  ELAPSED_EST: <int minutes since task start>

### Decomposition rules
- Decompose OR stay atomic, your call.
- If decomposing: **MINIMUM 2 subtask nodes**. One giant subtask defeats the test.
- If atomic: step0 + step1(STAYING_ATOMIC:true) + exactly one `sub1-atomic-solve` node + final.
- Linear parent chain.

---

## QUESTION

Question type: numeric-optimization (lower makespan better; score scales with gap above true optimum).
Subject: coupled job-shop scheduling, 3 jobs × 4 machines per factory.

Two factories operate in a supply chain. Factory A produces components; Factory B assembles them.

**Factory A** has 4 machines (MA1, MA2, MA3, MA4), 3 jobs. Each job visits machines in the order shown; each machine handles one job at a time. Processing times in hours:
- Job 1: MA1 (3) → MA3 (2) → MA2 (4) → MA4 (1)
- Job 2: MA2 (2) → MA1 (3) → MA4 (3) → MA3 (2)
- Job 3: MA3 (4) → MA4 (2) → MA1 (1) → MA2 (3)

**Factory B** has 4 machines (MB1, MB2, MB3, MB4), 3 jobs:
- Job 1: MB2 (2) → MB1 (3) → MB4 (1) → MB3 (3)
- Job 2: MB1 (1) → MB3 (4) → MB2 (2) → MB4 (2)
- Job 3: MB3 (3) → MB4 (2) → MB1 (3) → MB2 (1)

**COUPLING:** Job j in Factory B cannot begin ANY of its operations until ALL of Job j's operations in Factory A are finished.

**YOUR TASK:** produce a feasible coupled schedule, report its makespan, and predict how close to optimum you are. The true optimum is known to the orchestrator but NOT to you. You are NOT asked for the provable optimum.

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_2_0_0_1]]
