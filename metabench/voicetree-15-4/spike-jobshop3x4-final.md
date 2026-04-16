---
color: green
isContextNode: false
agent_name: Jun
---
# spike-jobshop3x4 final: coupled makespan=24

Final answer: coupled schedule with makespan 24. Factory A makespan 13 (MA2 bottleneck). Factory B makespan 24 via critical insight: delay J2 on MB1 1h to cede MB3 to J3 first, eliminating a 3-hour cascade delay.

Full schedule verified. All machine conflicts checked. All job precedences and coupling constraints satisfied.

Key insight for near-optimal result: J2 in Factory B has its first operation on MB1, which feeds into MB3 (the B bottleneck). J3's first operation IS MB3. By delaying J2's MB1 start 1 hour (from t=11 to t=12), both arrive at MB3 at t=13 — allowing J3 to be scheduled first on MB3, which prevents a 3-hour cascade delay that would have pushed makespan to 26.

Learnings:
- Coupling turns this into a 2-phase problem; solve A to get release times, then B.
- MB3 is B's critical machine (10h total load). Arrival order at MB3 determines final makespan.
- Voluntarily delaying a ready job (J2 on MB1 by 1h) to optimize a downstream bottleneck (MB3) is the non-obvious move that achieves optimum.
- Factory A: MA2 4h idle [t=2-6] is unavoidable given routing structure (only J2 ready at t=0, J1 blocked by MA3 conflict until t=6).

SCHEDULE_A: MA1: J1[0-3],J2[3-6],J3[6-7]; MA2: J2[0-2],J1[6-10],J3[10-13]; MA3: J3[0-4],J1[4-6],J2[9-11]; MA4: J3[4-6],J2[6-9],J1[10-11]
SCHEDULE_B: MB1: J2[12-13],J1[13-16],J3[18-21]; MB2: J1[11-13],J2[20-22],J3[22-23]; MB3: J3[13-16],J2[16-20],J1[20-23]; MB4: J3[16-18],J1[18-19],J2[22-24]
MAKESPAN: 24
P_WITHIN_DECLARED_GAP: 0.97

[[spike-jobshop3x4-sub2-factory-b]]
