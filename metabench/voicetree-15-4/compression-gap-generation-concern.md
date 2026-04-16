---
color: blue
isContextNode: false
agent_name: Anna
---
# Generation pipeline must be fully automatable — no human curation budget

The compression-gap benchmark needs procedural generation that doesn't rely on a human-curated primitive library, composition operators, or proof templates. Three automation layers considered (composed algebra synthesis, adversarial self-play, program-synthesis disguise). Recommendation: start with self-play, add algebra synthesis for rigor. Meta-realization: we're mechanizing representation invention itself.

## The Concern

The pipeline I sketched earlier (primitive library → composition operators → NL wrap) implicitly requires human math work:
- Curating ~20 invariant primitives
- Designing composition operators
- Writing proof templates
- Calibrating difficulty thresholds

No budget for that. Must be compute + agent only.

## Why Pure Random Generation Fails

Random 3-SAT is hard in a *boring* way — no compression exists. Would generate problems where agents fail from lacking brute force, not from lacking taste. That collapses back to the working-memory benchmark we already have.

**The requirement**: generate problems where compression EXISTS and is SHORT, but finding the compression is the cognitive challenge. Random doesn't guarantee this.

## Meta-Realization

By automating this generation we are mechanizing representation invention — the exact capability the ~/brain research says is AI's irreducible bottleneck. That either:
- (a) validates the benchmark (we can only generate *the kind of problem* the target-of-measurement can't solve, because we have the representation already in some library), or
- (b) proves the whole framing wrong (if we can automate generation, we've broken the floor)

Likely (a): our generator uses pre-existing representations from mathematical libraries, then hides them via composition + NL wrapping. The target agent has to re-discover the representation from behind the wrap. Generator cheats by starting with the answer; agent has no such shortcut.

## Three Automation Layers

### Layer A — Composed Algebra Synthesis (most rigorous)

Seed from existing math libraries, not human curation:

| Artifact | Source | Human work |
|---|---|---|
| Seed structures (groups, rings, lattices) | GAP / Sage / SymPy | 0 |
| Combinators (semidirect, wreath, quotient, extension) | Same libraries | 0 |
| Theorem discovery | Vampire / Prover9 ATP | 0 |
| Proof length (= gold compression length) | ATP output | 0 |
| Naive complexity floor | Brute-force search space size, computable | 0 |

Pipeline: sample seeds → apply random combinator chain of depth d → ATP generates theorems → filter for (short proof) ∧ (large naive search) → gold problem.

**Cost**: one-time engineering integration (Sage + ATP + length meter + agent wrapper). Agent-done.

**Why composition preserves compressibility**: if A and B each have short invariants, their semidirect product usually inherits composable versions. Structure survives the mixer. This is the key theoretical bet.

### Layer B — Adversarial Self-Play (most pragmatic)

Two-agent loop, no formal system:

1. Generator agent: produce (problem_NL, verifier_python, clever_trick_statement)
2. Solver agent (handicapped: no tools, token cap, no CoT): try to solve
3. Judge code: run verifier on solver's answer
4. Keep iff: verifier accepts some answer AND solver failed AND independent strong solver (given the trick) succeeds
5. Composition: prompt generator with prior tricks, ask it to compose 2–3

**Key**: verification is code the generator wrote. If the generator can't write a verifier, the problem is ill-posed → auto-discarded. Kills hallucinated gold-answers.

**Cost**: zero external integration.

**Risk**: generator drifts to boring problems. Needs quality-variety reward (e.g. embed past problems, reject near-duplicates).

### Layer C — Program-Synthesis Disguise (simplest)

- Agent writes short Python `f` (bounded byte-length)
- Run `f` on N inputs → (input, output) pairs
- NL problem: "compute f(x) for new x"
- Naive: memorize pairs (O(N))
- Smart: reverse-engineer `f` (O(len(f)), bounded)
- Gold answer: run `f`. Gold proof length: len(f).
- Vary difficulty by sampling `f` from a program grammar.

**Cost**: trivial.

**Risk**: program-from-examples is well-studied → agents have strong trained subfunctions. Mitigate with unusual primitive ops (bitwise, non-standard combinators).

## Recommendation

1. **Week 1**: build Layer B. Thousands of problems, no external deps. Validate signal on the HLE-12 baseline agents.
2. **Week 2+**: if signal is weak/noisy, add Layer A for rigorous gold-truth.
3. **Layer C** as a third axis measuring program-synthesis taste specifically.

## The Real Question I Can't Answer Without Experiments

Can an LLM generator reliably produce problems where (a) a clever trick genuinely exists, (b) the trick compresses to short proof, (c) the NL wrapping hides it from a peer-strength solver? Generator-solver capability asymmetry is load-bearing. If generator ≈ solver in capability, the generator either produces only problems the solver can already solve, or produces problems whose "trick" the generator itself hallucinated.

**Asymmetry strategies**:
- Generator has access to Python execution + math libraries; solver doesn't
- Generator runs at higher compute (more CoT / tool use / retries); solver is capped
- Generator uses Layer A-style seeds from library; solver gets only NL
- Ensemble of generators across different model families (Opus + GPT + Gemini) reduces single-model biases

Asymmetry is the hinge. Without it, self-play collapses to "what this model can already do," which doesn't measure capability — it measures the model's fixed point.

### NOTES

- The meta-move (automate representation invention to benchmark it) is worth noting even if only as a philosophical flag. If Layer B works well, it's weak evidence that LLMs CAN do representation invention when given the right scaffolding — potentially contradicting the ~/brain 33-40% floor claim.
- Generator-solver asymmetry is the real load-bearing design choice. Plan this carefully before building Layer B.
- Layer A's theoretical bet — that composition of compressible structures stays compressible — is usually true for the compositions I listed but not always. Would want empirical validation on a sample.
- Layer C is suspiciously close to ARC-AGI. Can probably borrow/adapt infrastructure from there rather than build from scratch.

## Related

- [compression-gap-benchmark-design](compression-gap-benchmark-design.md)
- [brain-fetch-info-theory-representation-invention](brain-fetch-info-theory-representation-invention.md)
- [working-memory-chunk-scaling-benchmark](working-memory-chunk-scaling-benchmark.md)

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_0_0]]
