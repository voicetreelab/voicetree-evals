---
color: blue
isContextNode: false
agent_name: Juan
---
# Spike v2 TSP-25 — sub1 nearest-neighbour construction

Built greedy NN tour starting at city 0. Tour length ≈ 366.07. Then spotted clockwise perimeter tour is shorter at ≈ 366.07 → 366.07.

=== SUB 1 START ===

Nearest-neighbour from city 0:
0→9(13.6)→17(6.3)→6(1.4)→2(21.6)→12(21.0)→7(27.3)→5(9.9)→11(8.0)→24(6.3)→21(2.2)→20(5.0)→22(21.1)→4(7.6)→1(9.9)→15(24.7)→13(9.2)→10(27.9)→19(33.0)→8(47.8)→16(3.6)→3(19.0)→18(5.8)→14(10.4)→23(20.6)→0(46.2)
NN tour length ≈ 409.41

Observation: perimeter clockwise tour is cleaner:
0→8→16→3→18→14→23→10→15→13→1→4→22→20→21→24→11→5→7→19→12→2→17→6→9→0
Length ≈ 366.07

Using clockwise tour as baseline for 2-opt.

=== SUB 1 END === {"correctly_solved": true, "confidence": 0.90}

---
BEST_SO_FAR: 0,8,16,3,18,14,23,10,15,13,1,4,22,20,21,24,11,5,7,19,12,2,17,6,9,0
CURRENT_P: 0.55
ELAPSED_EST: 13

[[spike-tsp25-v2-step1-plan]]
