---
color: green
isContextNode: false
agent_name: Anna
---
# ~/brain fetch: information theory + representation invention → benchmark connection

Retrieved and synthesized research from ~/brain on information theory (unified cognitive-computational model), representation invention (compression taste, 4 mechanisms, UTM-choosing), and novel theory construction. Found 3 load-bearing connections to the proof-compression / working-memory benchmark design.

## What was fetched

### 1. Unified Cognitive-Computational Model (`brain/workflows/information_theory/unified_cognitive_computational_model/`)
5-axiom theory: all structural design minimizes computational cost for bounded processors.
- **Superlinear attention cost**: reasoning cost scales superlinearly with items in attention. Structure is computational necessity, not preference.
- **Compiled subfunctions**: expertise = compiled subroutines. `effective_cost = intrinsic_dims - compiled_subfunctions`. Reader-relative.
- **Cognition is computation**: all representations are programs. Software architecture tools transfer universally because the processor and objective are identical.
- **The design law**: decompose to min items per level, min dependency between items.

### 2. Representation Invention Research (`brain/knowledge/.../breakthrough-theory-cognitive-requirements-for-novel-compression/`)
- **Compression taste = 5 sub-processes**: representation invention, structural invariant detection, multi-level implication tracing, constraint forcing, convergence recognition
- **Only representation invention is irreducible** — the others are search within a fixed representation
- **Representation invention IS choosing the UTM** that makes K(x) tractably short. The invariance theorem's O(1) constant is the compiler length — and for human-scale problems, that IS the bottleneck.
- **4 mechanisms**: subtractive abstraction, ontological substitution, meta-level elevation, expressiveness-driven construction. All share one trigger: **expressive failure** (the current formalism can't state what you need).
- **Bidirectional search pattern**: top-down data patterns ↔ bottom-up axiomatic derivations, with representation shifts as the key discontinuities.

### 3. Novel Theory Construction / L3 Floor (`brain/old_voicetrees/voicetree-9-4/`)
33–40% structural floor on automation. Frozen-ontology problem: AI can't invent representations because its ontology is fixed at training time.

---

## 3 Connections to Proof Compression + Working-Memory Benchmark

### Connection 1: Chunk count is representation-relative, not fixed
The compiled-subfunctions axiom says `effective_cost = intrinsic_dims - compiled_subfunctions`. An agent that finds a better representation for the problem has lower effective N — the same problem at N=12 chunks in one representation might be N=6 in another.

**Benchmark implication**: The working-memory scaling benchmark doesn't just test externalization threshold. It implicitly tests whether the agent can *re-represent* the problem to reduce effective chunk count. An agent with "perfect" metacognition doesn't just externalize at N=12 — it finds a representation where N=12 becomes N=6 and solves in-context.

This is a **new measurement dimension**: accuracy at N, controlling for representation quality.

### Connection 2: The NL-wrapping / specification gap IS the expressive-failure trigger
The benchmark's "anti-solver" NL framing (from the parent context: ambiguous natural language that can't be directly encoded) forces the agent through the representation-invention loop:

```
Receive ambiguous NL problem
  → try to formalize in existing representation
    → fail (specification gap = expressive failure)
      → diagnose what's inexpressible
        → invent/choose representation
          → solve within chosen representation
```

This is **exactly** the 4-mechanism trigger from the ~/brain research. The specification gap isn't just an anti-solver trick — it's a controlled way to force representation invention, which is the irreducible core of compression taste.

**Benchmark implication**: The NL wrapping isn't a secondary feature. It's the mechanism that makes this a *compression taste* benchmark, not just a *working memory* benchmark. Without it, you're only testing search-within-representation (sub-processes 2–5). With it, you're also testing sub-process 1.

### Connection 3: Proof compression = choosing the right UTM, testable as a benchmark output
The ~/brain research says compression taste is primarily about choosing the right UTM, not searching within one. The coupled job-shop problem already tests this in miniature: the agent must choose whether to represent Factory A and B independently or jointly. The coupled representation makes the problem solvable; the independent one gives wrong answers.

**Benchmark implication**: After the agent produces an answer, ask it to **compress its proof** — state the solution in minimal form. The quality of this compression reveals the quality of its internal representation. Two agents that both get answer=15 may have wildly different proof compression quality. This is a cheap additional signal that measures representation quality directly.

Concrete protocol addition:
1. Agent solves problem → answer
2. Agent compresses its proof → minimal justification
3. Score: (a) answer correctness, (b) proof compression ratio, (c) whether compressed proof is still valid

This directly operationalizes the UTM-choosing insight: a good UTM produces short programs (compressed proofs). A bad UTM produces long, tangled justifications even when the answer is correct.

### NOTES

- The proof-compression-synthesis.md in brain/old_voicetrees/voicetree-7-4/ is about AGI-timelines argument compression, not the benchmark — but shares the same intellectual DNA (compress to minimal falsifiable premises).
- The information_theory.md workflow file itself is just 'tbd' — the real content lives in the unified_cognitive_computational_model/ subtree.
- Connection 2 (NL-wrapping = expressive failure trigger) is the strongest insight. It reframes the 'anti-solver' design choice from a practical trick into a theoretically motivated measurement of the irreducible core of compression taste.
- Open question from the research: can AI-human loops bypass the representation-invention floor? The benchmark could test this — give the agent access to a human hint about representation choice and measure improvement.

## Related

- [working-memory-chunk-scaling-benchmark](working-memory-chunk-scaling-benchmark.md)
- [benchmark-v2-plan](benchmark-v2-plan.md)

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_0_0]]
