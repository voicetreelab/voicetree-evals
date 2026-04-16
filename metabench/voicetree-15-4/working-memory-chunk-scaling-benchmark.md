---
color: green
isContextNode: false
agent_name: Amy
---
# Working-memory chunk scaling — benchmark design for agents

Developed the idea of problems where the number of mutually interdependent 'chunks' (simultaneous info pieces) is a tunable difficulty knob N. This tests metacognition: at what N does the agent recognize it must externalize? Key insight: difficulty comes from WIDTH of attention per reasoning step, not LENGTH of reasoning chain — so solution tokens stay short even as N grows.

## Why this is different from "just needs more tokens"

The parent concern: scaling N just increases token count, testing context length not cognition. Working-memory problems are different:

1. **Solution is SHORT** — answer might be a single number. It's the *reasoning step width* that's hard.
2. **Problem size can stay constant** while chunk interdependence grows — same constraint count, more cross-references.
3. **The measurement is metacognitive** — not "did it solve N=12" but "did it recognize it needed to externalize at N=12?"

## Core design property

Chunks must be **mutually interdependent at each reasoning step**. If independent, the agent processes them sequentially — no simultaneous working memory pressure. The constraint graph between chunks must be dense enough that you can't decompose into independent sub-problems.

## 4 concrete problem classes

### 1. Live Variable Tracking
> "A chemical plant has N tanks connected by pipes. Each minute, each tank transfers a fraction to neighbors per rules. After T steps, what's the level in tank K?"
- Chunk count = N (all tank levels needed simultaneously per step)
- N=4 easy, N=12 requires externalization
- Verification: trivial simulation

### 2. Constraint Intersection (Einstein puzzle scaling)
> "N people on a street, each with K attributes, linked by cross-referencing constraints. Who owns the fish?"
- Chunk count ≈ live constraints during each deduction
- N=5,K=3 manageable; N=8,K=5 impossible without externalization
- Each deduction may invalidate/activate multiple constraints — can't process linearly

### 3. Multi-Party Resource Flow with Conditionals
> "12 traders with portfolios. Each round, trades follow personal rules referencing others' holdings. After 5 rounds, who holds most gold?"
- Conditional rules create circular interdependence (A depends on B, B on C, C on A)
- Chunk count = number of traders whose state must be simultaneously tracked
- Scales cleanly by adding traders

### 4. Coupled Constraint Satisfaction (extends existing job-shop work)
> "Schedule N jobs across 2 factories where B's release times depend on A's completions AND A's priorities depend on B's queue lengths"
- Already explored in this project — the "coupled" property forces simultaneous consideration
- Chunk count = cross-factory dependencies held during any scheduling decision

## The metacognition measurement protocol

You're measuring 4 things at each N:

| Metric | What it reveals |
|--------|----------------|
| Accuracy at N | Raw capability ceiling |
| N where agent starts using tools/externalization | Metacognitive self-monitoring threshold |
| Gap between accuracy-drop N and tool-use N | Metacognitive calibration (smaller = better) |
| Accuracy improvement when tools used | Effective externalization skill |

An agent with **perfect metacognition**: detects overload → externalizes → solves correctly.  
An agent with **poor metacognition**: attempts raw → fails → retries same way.

## Generator signature

```
generate(seed, N_chunks, domain) → (question_nl, gold_answer, verify_fn, metadata)
```

Difficulty tiers:
- N=5 (easy — most models solve in-context)
- N=8 (medium — some fail without externalization)
- N=12 (hard — most need externalization)
- N=18 (extreme — even with tools, requires good decomposition)

## Open question: anti-solver framing

The NL-wrapping idea from the parent context ("specification gap") is especially important here. If the problem is stated formally, the agent just writes a simulator. The NL framing forces the agent to:
1. Parse ambiguous specs into formal constraints (itself a cognitive load task)
2. THEN solve the constraint problem

This doubles the working memory pressure — you need chunks for both the interpretation AND the solution state.

### NOTES

- This connects directly to the benchmark-v2-plan Phase 1 generators — chunk count becomes a unified difficulty knob across problem types
- The coupled job-shop work already done is an instance of problem class 4 — the N=2 factory case with cross-dependencies
- Critical design choice: the NL wrapping must be calibrated so that spec-parsing difficulty doesn't dominate chunk-tracking difficulty, or you're measuring language comprehension not working memory

## Related

- [benchmark-v2-plan](benchmark-v2-plan.md)
- [hch-v2-coupled-job-shop-solution](hch-v2-coupled-job-shop-solution.md)

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_0]]
