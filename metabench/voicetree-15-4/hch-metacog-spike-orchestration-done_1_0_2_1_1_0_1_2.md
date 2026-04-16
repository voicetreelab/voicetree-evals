---
isContextNode: false
---
# Benchmark question generation pipeline

## Core pipeline

```
seed -> generate_instance(seed, n_jobs, n_machines) -> (problem_data, gold_answer, verify_fn)
     -> render_math(problem_data)     -> math-framed question text
     -> render_natural(problem_data)  -> NL-framed question text
```

## Steps

### 1. Generate random valid instance (deterministic from seed)
Pick n_jobs, n_machines per factory. Random processing times (uniform 1-8 hrs), random machine orderings per job, coupling structure (1:1 basic case). One seed = one unique problem.

### 2. Compute gold answer (offline, at generation time)
- Small instances (n <= 4x3): brute-force enumerate permutations
- Larger instances: Google OR-Tools CP-SAT solver (free, Python, proves optimality up to ~10x10)
Gold stored alongside problem, not computed at eval time.

### 3. Verify any proposed answer
Given claimed makespan M, check: (1) no machine overlap, (2) precedence respected per job, (3) coupling respected (B's job j starts >= A's job j completion), (4) makespan = max(all end times). All O(n^2) checks.

### 4. Render into question text
Two renderers from same problem_data:
- **Math renderer:** "Job 1: M1 (3 hrs) -> M2 (2 hrs)" -- direct, formal
- **NL renderer:** Template bank with machine names (CNC, paint booth, lathe...), job names (Alpha, Beta...), scenario framings. Same structure, different surface.

## Agent-in-the-loop enhancements (5 ideas)

1. **Adversarial coupling design.** Agent looks at generated instance and sets Factory A processing times so greedy-independent solution is maximally wrong (30-40% gap). Random instances often have independent solution near-optimal = no signal. Agent engineers instances where decomposition decision is load-bearing.

2. **Distractor injection.** Add irrelevant but plausible info: "Order Alpha is high-priority," "CNC machine was recently serviced." Tests whether model distinguishes problem-relevant constraints from narrative noise.

3. **Ambiguity-with-resolution planting.** NL version has one constraint that appears ambiguous on first read but resolves with careful reading. E.g., "B can't start until A ships it" (ambiguous) + later "A ships once it clears the final station" (resolution). Tests whether model flags ambiguity. Verifiability preserved because there IS a right answer.

4. **Difficulty-targeted rewording.** Agent rephrases "too easy" instances to be cognitively harder without changing the problem: reorder information, present B before A, use passive voice to obscure dependency direction. Gives matched pairs: same gold, different cognitive load.

5. **Gold-answer sanity check.** Agent independently solves each instance step-by-step after OR-Tools. Catches encoding bugs before they enter the dataset.

## Automatable vs. needs craft

| Component | Automatable? | Notes |
|-----------|-------------|-------|
| Instance generation | Yes | Pure RNG from seed |
| Gold answer computation | Yes | OR-Tools or brute force |
| Verification | Yes | O(n^2) constraint checks |
| Math rendering | Yes | Trivial template |
| NL rendering | Mostly | Template bank with randomized names |
| Difficulty calibration | Needs one empirical pass | Run cheap model on candidates, filter by accuracy band |
| Adversarial structure | Agent-in-the-loop | Code can't judge "how misleading is the greedy approach" |

## Proposed problem mix (210 total)

- 180 math-framed (statistical bulk)
- 30 NL-framed (paired with 30 of the math-framed, same underlying instance, different surface)

This gives the accuracy_math vs accuracy_NL signal (presentation sensitivity = metacognitive failure) without blowing up run count.

[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_2_0.md]]
