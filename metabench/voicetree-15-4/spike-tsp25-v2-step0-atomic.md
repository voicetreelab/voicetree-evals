---
color: blue
isContextNode: false
agent_name: Juan
---
# Spike v2 TSP-25 — step0 atomic baseline

Atomic prediction + declared gap + initial best-guess tour committed before any detailed reasoning.

ATOMIC_PREDICTION: {"words_if_atomic": 150, "p_correct_if_atomic": 0.45}
DECLARED_GAP: 12.0

INITIAL_BEST_GUESS tour (nearest-neighbour eyeball, pre-analysis):
0,9,17,6,2,12,7,5,11,24,21,20,22,4,1,15,13,10,19,8,16,3,18,14,23,0
Estimated length: ~409 (rough)

Rationale for atomic P: TSP-25 is tractable with NN+2-opt but exact is hard; heuristic can get within 10-15% of optimal with careful manual work.

---
BEST_SO_FAR: 0,9,17,6,2,12,7,5,11,24,21,20,22,4,1,15,13,10,19,8,16,3,18,14,23,0
CURRENT_P: 0.40
ELAPSED_EST: 12

[[spike-tsp25-v2-time-budget]]
