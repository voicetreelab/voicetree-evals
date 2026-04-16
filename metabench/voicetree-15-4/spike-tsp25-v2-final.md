---
color: green
isContextNode: false
agent_name: Juan
---
# Spike v2 TSP-25 — final answer

Final tour length 353.76 via NN construction + 2-opt. All 25 cities visited exactly once. P(within 12% of optimal) ≈ 0.65.

## Method summary
Nearest-neighbour greedy construction (clockwise perimeter tour as seed) followed by two manual 2-opt/Or-opt passes. Net improvement from seed: 366.07 → 353.76 (−3.4%).

## Final tour
City sequence: 0→8→16→3→18→14→23→10→15→13→1→4→22→19→20→21→24→11→5→7→12→2→6→17→9→0

Edge breakdown:
0→8:16.28, 8→16:3.61, 16→3:18.97, 3→18:5.83, 18→14:10.44,
14→23:20.62, 23→10:35.36, 10→15:20.22, 15→13:9.22, 13→1:30.15,
1→4:9.85, 4→22:7.62, 22→19:18.11, 19→20:24.84, 20→21:5.00,
21→24:2.24, 24→11:6.32, 11→5:8.00, 5→7:9.85, 7→12:27.29,
12→2:21.02, 2→6:21.59, 6→17:1.41, 17→9:6.32, 9→0:13.60

TOUR: 0,8,16,3,18,14,23,10,15,13,1,4,22,19,20,21,24,11,5,7,12,2,6,17,9,0
TOUR_LENGTH: 353.76
P_WITHIN_DECLARED_GAP: 0.65

[[spike-tsp25-v2-sub2-2opt-improve]]
