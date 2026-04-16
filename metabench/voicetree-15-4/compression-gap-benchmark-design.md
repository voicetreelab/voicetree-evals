---
color: green
isContextNode: false
agent_name: Anna
---
# Compression-gap benchmark: complexity scales faster than reasoning length

Design principle for benchmark questions where N scales intrinsic complexity exponentially but optimal proof length stays bounded. Measures representation-invention capability (compression taste), not context window or token budget. 5 concrete problem classes, each tied to a representation-invention mechanism from ~/brain research.

## Core Design Principle

Build problems where:
- **Naive representation** → reasoning length is exponential (or factorial) in N
- **Right representation** → reasoning length is O(1) or O(log N)
- **Answer** is a small fixed object (yes/no, single number)
- **N** tunes intrinsic dimensionality freely

The gap between naive-length and optimal-length IS the smartness signal. It grows exponentially in N while optimal stays constant. Smartness = how close agent_length gets to optimal_length at large N.

## Information-Theoretic Grounding

From ~/brain research: K_U(x) = K_V(x) + O(1), but that O(1) is the compiler length between representations — which for practical problems IS the entire bottleneck.

We deliberately design problems where:
- U = naive representation, K_U(x) is huge
- V = invented/compressing representation, K_V(x) is tiny
- c_{UV} (finding the compiler) is what separates smart from dumb

The intrinsic difficulty scales with N. The proof-length for a compression-finder stays bounded. The proof-length for a brute-forcer explodes.

## 5 Problem Classes (↔ 4 representation-invention mechanisms)

| # | Class | Naive cost | Optimal cost | Mechanism |
|---|---|---|---|---|
| 1 | Invariant / monovariant discovery | O(N!) or O(2^N) | O(1) | Subtractive abstraction |
| 2 | Symmetry quotienting | O(N!) | O(1) | Ontological substitution |
| 3 | Isomorphism to known-polynomial problem | O(exp) | O(poly) | Expressiveness-driven construction |
| 4 | Pumping / induction / closed-form | O(N) or O(exp) simulation | O(log N) | Meta-level elevation |
| 5 | Pigeonhole / counting impossibility | O(exp) enumeration | O(1) | Subtractive abstraction |

### Example 1: Invariant discovery
> "N tokens on a line labelled 1…N. Each turn swap two adjacent. Can N(N-1)/2 − 1 swaps produce the full reversal?"

- Naive: BFS over permutation graph, grows as N!
- Smart: parity invariant. Reversal has parity N(N-1)/2. k has opposite parity. **Impossible.** 3-sentence proof.
- N scales to 10^6. Proof length stays 3 sentences.

### Example 2: Symmetry quotienting
> "Color a regular N-gon's vertices with 3 colors so no two adjacent share. How many distinct colorings up to rotation/reflection?"
- Naive: enumerate 3^N, apply Burnside case by case
- Smart: apply Burnside lemma cleanly — short closed form

### Example 3: Isomorphism to max-matching
> NL scheduling / assignment problem phrased domain-specifically ("medical residents to rotations"). Hidden structure = bipartite matching.
- Naive: enumerate assignments (exp)
- Smart: recognize max-matching, invoke Hall's theorem for feasibility or run Hopcroft-Karp mentally

### Example 4: Pumping / closed-form
> "N-state Markov-like process, initial state s0. After T → ∞ steps, probability of state sk?"
- Naive: simulate T steps, O(T)
- Smart: stationary distribution, solve linear system, O(N^3) but T-independent. Or spot algebraic structure → closed form.

### Example 5: Pigeonhole impossibility
> "N rooms each of N colors, N visitors each with a forbidden-color set of size k. Valid assignment exists iff …?"
- Naive: try all N! assignments
- Smart: counting violation of Hall's condition → one-sentence proof of impossibility

## Why This Scales With Smartness, Not Time

| Agent type | Token cost at N=10 | N=100 | N=1000 |
|---|---|---|---|
| Naive (simulates) | 10^3 | hits context wall | fails |
| Medium (some heuristics) | 10^2 | 10^5 (fails) | fails |
| Smart (finds compression) | 50 | 50 | 50 |

The benchmark output is the **max N at which agent stays near optimal_length**. This is a capability measurement independent of context window.

## Critical: Procedural Generation Requirement

If the agent has already seen the specific trick → the compression is a compiled subfunction → `effective_cost = 0` → no measurement signal. Two defenses:

### Defense 1: Instance families
Same compression insight, varied surface. E.g. the parity-invariant class has infinite instances (different group structures, permutation types, operation sets). Procedural generator produces novel surface every time.

### Defense 2: Composed compressions
Require stacking 2–3 insights. Even with finite trick library of size K, composition gives O(K^d) problems at depth d. At d=3, K=20 → 8000 problems, each requiring a specific combination.

This is also where the **bidirectional-search** pattern from ~/brain kicks in: top-down (what's the answer space?) meets bottom-up (what structure exists?), with representation shifts as discontinuities. Depth-d composition forces d discontinuities.

## Connection to Working-Memory Chunk Benchmark

The chunk-scaling benchmark measures externalization threshold — useful but orthogonal. This compression-gap benchmark measures something different and harder: **did the agent find the representation that makes N irrelevant?**

An agent that externalizes at N=12 is competent. An agent that reformulates at N=12 so the problem trivializes is smart. The compression-gap benchmark separates these two.

Best v2 protocol: **run both**. Chunk-scaling measures metacognition of overload. Compression-gap measures representation-invention capability. Together they triangulate the smartness axes.

## Operational Sketch

```
generate(class, seed, N, composition_depth) → (question_NL, gold_answer, optimal_proof_length, verify_fn)
```

Measure per run:
- `correct`: binary
- `agent_length`: tokens in agent's justification
- `compression_ratio = agent_length / optimal_proof_length`
- `max_N_near_optimal`: largest N where ratio < threshold (say 3×)

Headline metric: **max_N_near_optimal**. This is the capability number that scales with smartness, not with compute budget.

### NOTES

- The main failure mode to watch: making problems that ARE known tricks from math olympiads. Olympiad training data means the tricks are already compiled subfunctions. Use less-famous invariants, or compose multiple to escape training-data coverage.
- The 'specification gap' NL-wrapping from the parent context is still essential — without it, a smart agent just writes a program that brute-forces (effectively getting O(poly) from compiler optimizations). NL wrapping prevents direct formalization.
- Open question: how do you verify optimal_proof_length is actually minimal? For invariants/pigeonhole, it's obvious. For harder composed problems, you may need a human-curated 'reference proof' per class.
- This design inherits from the representation-invention research: the 4 mechanisms are not just historical — they're a finite taxonomy of compression routes, giving you a structured generator space.

## Related

- [brain-fetch-info-theory-representation-invention](brain-fetch-info-theory-representation-invention.md)
- [working-memory-chunk-scaling-benchmark](working-memory-chunk-scaling-benchmark.md)
- [benchmark-v2-plan](benchmark-v2-plan.md)

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_0_0]]
