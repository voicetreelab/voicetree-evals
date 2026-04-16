---
color: blue
isContextNode: false
agent_name: Jun
---
# spike-jobshop3x4 sub2: Factory B schedule with coupling

Solved Factory B with coupling (J1,J2 released t=11; J3 released t=13). Key move: delay J2 on MB1 by 1h to let J3 claim MB3 first. Coupled makespan=24.

=== SUB 2 START ===
Release times from A: J1=11, J2=11, J3=13.

Factory B routing:
- J1: MB2(2)→MB1(3)→MB4(1)→MB3(3). Total=9h.
- J2: MB1(1)→MB3(4)→MB2(2)→MB4(2). Total=9h.
- J3: MB3(3)→MB4(2)→MB1(3)→MB2(1). Total=9h.

MB3 bottleneck=10h. Key arrivals at MB3:
- J2: after MB1(1h), arrives MB3 at t=12 (release 11 + 1h MB1).
- J3: released at t=13, first op IS MB3 → arrives t=13.
- J1: after MB2(2)+MB1(3) → arrives MB3 at t=16 earliest.

Critical insight: If J2 goes immediately on MB1 at t=11, it claims MB3 at t=12, blocking J3 until t=16. Then J3→MB4[16-18]→MB1[18-21]→MB2[22-23]=t=23. J2 after MB3[12-16]→MB2[16-18]→MB4[18-20]=t=20. J1→MB4[16-17]→MB3[19-22 wait for MB3 free at 19? MB3: J2[12-16], next J3[16-19], so J1 waits until t=19... MB4[16-17], MB3[19-22]=t=22... wait that gives makespan=23.

Better: Delay J2 on MB1 by 1h (start MB1 at t=12 instead of t=11). Then J2 arrives MB3 at t=13 — same time as J3. Schedule J3 first on MB3:

With J2 delayed 1h on MB1:
- MB1: J2[12-13], J1[13-16] (J1 arrives t=13 from MB2[11-13]), J3[18-21] (arrives after MB4[16-18])
- MB2: J1[11-13], J2[20-22] (after MB3[16-20]), J3[22-23] (after MB1[18-21])
- MB3: J3[13-16], J2[16-20], J1[20-23] (J1 arrives t=19 from MB4[18-19], MB3 free t=20)
- MB4: J3[16-18] (after MB3[13-16]), J1[18-19] (after MB1[13-16]), J2[22-24] (after MB2[20-22])

Verification:
- J1 B: MB2[11-13]→MB1[13-16]→MB4[18-19]→MB3[20-23]. Done=23. ✓
- J2 B: MB1[12-13]→MB3[16-20]→MB2[20-22]→MB4[22-24]. Done=24. ✓
- J3 B: MB3[13-16]→MB4[16-18]→MB1[18-21]→MB2[22-23]. Done=23. ✓

No machine conflicts. All coupling satisfied (J1,J2 start B ≥11 ✓; J3 starts B at t=13 ✓).

Coupled system makespan = 24.
=== SUB 2 END === {"correctly_solved": true, "confidence": 0.93}

BEST_SO_FAR: 24
CURRENT_P: 0.92
ELAPSED_EST: 12

[[spike-jobshop3x4-sub1-factory-a]]
