---
color: blue
isContextNode: false
agent_name: Juan
---
# Spike v2 TSP-25 — sub2 2-opt improvement

Applied 2-opt and Or-opt moves to reduce tour from 366.07 → 353.76. Key moves: insert city 19 between 22 and 20 (saves 10.24), reorder bottom segment 2→6→17→9 (saves 2.07).

=== SUB 2 START ===

Starting tour: 0,8,16,3,18,14,23,10,15,13,1,4,22,20,21,24,11,5,7,19,12,2,17,6,9,0  length=366.07

**Move 1 — Or-opt: relocate city 19 between 22 and 20**
Remove edges: (22,20)=21.10, (7,19)=26.08, (19,12)=33.30  total=80.48
Add edges:    (22,19)=18.11, (19,20)=24.84, (7,12)=27.29   total=70.24
Net saving: +10.24
New tour: 0,8,16,3,18,14,23,10,15,13,1,4,22,19,20,21,24,11,5,7,12,2,17,6,9,0  length=355.83

**Move 2 — 2-opt: reorder bottom segment 2→17→6→9 → 2→6→17→9**
Old: 2→17(22.36)+17→6(1.41)+6→9(7.62)+9→0(13.60) = 44.99
New: 2→6(21.59)+6→17(1.41)+17→9(6.32)+9→0(13.60) = 42.92
Net saving: +2.07
Final tour: 0,8,16,3,18,14,23,10,15,13,1,4,22,19,20,21,24,11,5,7,12,2,6,17,9,0  length=353.76

**Edge-by-edge verification of final tour (353.76):**
0→8:16.28 | 8→16:3.61 | 16→3:18.97 | 3→18:5.83 | 18→14:10.44
14→23:20.62 | 23→10:35.36 | 10→15:20.22 | 15→13:9.22 | 13→1:30.15
1→4:9.85 | 4→22:7.62 | 22→19:18.11 | 19→20:24.84 | 20→21:5.00
21→24:2.24 | 24→11:6.32 | 11→5:8.00 | 5→7:9.85 | 7→12:27.29
12→2:21.02 | 2→6:21.59 | 6→17:1.41 | 17→9:6.32 | 9→0:13.60
Sum = 353.76

All 25 cities appear exactly once: 0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24 ✓

=== SUB 2 END === {"correctly_solved": true, "confidence": 0.92}

---
BEST_SO_FAR: 0,8,16,3,18,14,23,10,15,13,1,4,22,19,20,21,24,11,5,7,12,2,6,17,9,0
CURRENT_P: 0.65
ELAPSED_EST: 14

[[spike-tsp25-v2-sub1-nn-construct]]
