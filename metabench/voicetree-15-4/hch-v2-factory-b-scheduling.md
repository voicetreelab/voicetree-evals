---
color: green
isContextNode: false
agent_name: Ama
---
# Sub 2+3: Factory B scheduling + lower bound proof

A1 release times (6,6,9) give B makespan=15. A2 release times (9,6,7) give B makespan=17. A1 is provably optimal via M4 mandatory-idle lower bound.

=== SUB 2+3 START ===

**B jobs:** B-J1=M4(2)→M3(1), B-J2=M3(3)→M4(2), B-J3=M3(1)→M4(4)
M4 total = 8 hrs.

### A1 release times (r=6, 6, 9)

t=6: B-J1 starts M4[6-8]; B-J2 starts M3[6-9]. (No conflict.)
t=8: M4 free. Nothing ready — B-J2 still on M3; B-J3 not released. **M4 idle [8-9]: MANDATORY.**
t=9: B-J2 done M3→wants M4. B-J3 released→needs M3. B-J1 waiting for M3.
- M3: B-J2[6-9], B-J1[9-10], B-J3[10-11]
- M4: B-J1[6-8], idle[8-9], B-J2[9-11], B-J3[11-15]

**Makespan = 15.**

**Lower bound (tight):** M4 span = 6(start)+2+1(idle)+2+4 = **15** → no schedule can beat 15 under A1.

### A2 release times (r=9, 6, 7)

t=6: B-J2 starts M3[6-9]. M4 idle (B-J1 not released, B-J3 needs M3 first).
t=9: B-J1 (M4 first) and B-J2 (done M3, wants M4) both arrive on M4 simultaneously.
- M4: [B-J1 or B-J2][9-11], [other][11-13], B-J3[13-17]
- **Makespan = 17.** (Late B-J1 congests M4.)

### Full constraint check for A1 solution
- M1 no overlap: [0-3],[3-5],[5-6] ✓
- M2 no overlap: [0-4],[4-6],[6-9] ✓
- A precedences: J1(3≤4)✓, J2(4≤5)✓, J3(5≤6)✓
- Coupling: B-J1 starts t=6≥6✓, B-J2 t=6≥6✓, B-J3 t=10≥9✓
- M3 no overlap: [6-9],[9-10],[10-11] ✓
- M4 no overlap: [6-8],[9-11],[11-15] ✓
- B precedences: B-J1(8≤9)✓, B-J2(9≤9)✓, B-J3(11≤11)✓

=== SUB 2+3 END === {"correctly_solved": true, "confidence": 0.94}

decomposes into [[hch-v2-coupled-job-shop-solution]]
