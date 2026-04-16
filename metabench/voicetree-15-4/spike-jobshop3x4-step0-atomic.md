---
color: blue
isContextNode: false
agent_name: Jun
---
# spike-jobshop3x4 step0: atomic baseline

Initial atomic prediction, declared gap, and rough feasible schedule before decomposing.

ATOMIC_PREDICTION: {"words_if_atomic": 300, "p_correct_if_atomic": 0.55}
DECLARED_GAP: 5
INITIAL_BEST_GUESS: Greedy FIFO — guess makespan ~26 (Factory A ~13, B adds ~13 with coupling delays).

Machine load analysis:
Factory A: MA1=7h, MA2=9h (bottleneck), MA3=8h, MA4=6h. LB_A=9 (but jobs=10h each, expect ~13).
Factory B: MB1=7h, MB2=5h, MB3=10h (bottleneck), MB4=5h. LB_B=10.
Coupling LB: max(job_A_completion + job_B_chain) — need to solve to tighten.

Decompose: Sub1=Factory A schedule, Sub2=Factory B (given A release times).

BEST_SO_FAR: 26
CURRENT_P: 0.55
ELAPSED_EST: 1

[[spike-jobshop3x4-time-budget]]
