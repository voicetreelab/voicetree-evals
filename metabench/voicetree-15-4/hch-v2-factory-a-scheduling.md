---
color: green
isContextNode: false
agent_name: Ama
---
# Sub 1: Factory A scheduling — two optimal options

Factory A lower bound = 9 (M2 bottleneck). Two distinct optimal schedules found. A1 gives completions (6,6,9); A2 gives (9,6,7).

=== SUB 1 START ===

Jobs: Job1=M1(3)→M2(2), Job2=M2(4)→M1(1), Job3=M1(2)→M2(3)

M1 total = 6 hrs. M2 total = 9 hrs. LB = max(6,9) = **9 hrs** (M2 bottleneck).

For makespan=9, M2 runs continuously. Only Job2 can start M2 at t=0 (it needs M2 first).

**Schedule A1** (M1: Job1 first):
- M1: Job1[0-3], Job3[3-5], Job2[5-6]
- M2: Job2[0-4], Job1[4-6], Job3[6-9]
- Job1: M1 done t=3, M2 at max(3,4)=4, done=6 ✓
- Job2: M2 done t=4, M1 at max(4,5)=5, done=6 ✓
- Job3: M1 done t=5, M2 at max(5,6)=6, done=9 ✓
- **Completions: Job1=6, Job2=6, Job3=9** → B release times (6,6,9)

**Schedule A2** (M1: Job3 first):
- M1: Job3[0-2], Job1[2-5], Job2[5-6]
- M2: Job2[0-4], Job3[4-7], Job1[7-9]
- **Completions: Job1=9, Job2=6, Job3=7** → B release times (9,6,7)

These are the only two distinct optimal orderings (swapping M1/M2 sequences produces one of these two).

=== SUB 1 END === {"correctly_solved": true, "confidence": 0.97}

decomposes into [[hch-v2-coupled-job-shop-solution]]
