---
color: green
isContextNode: false
agent_name: Amy
---
# Coupled State Update (CSU) — concrete working-memory generator

Specific, buildable generator for chunk-scaling problems: N agents updating values via `v_i = (a_i · v_{π(i)} + b_i · v_{σ(i)}) mod 10`. Constructively proves pathwidth ≈ N — no sequential algorithm can solve it holding fewer than N live values. Includes generator code, property proof, parameter sweet spots, and metacognition measurement protocol.

## The formal property we need

A problem has **chunk-width W** if every correct algorithm must, at some step, hold ≥W live pieces of state. This is pathwidth. If a problem can be processed with sliding-window state <N, it doesn't have the property — the agent just streams it.

Generator's job: construct problems with guaranteed-high pathwidth.

## The CSU template

> *N agents. Each holds a value v_i ∈ {0..9}. Each round, `v_i = (a_i · v_{π(i)} + b_i · v_{σ(i)}) mod 10`. π, σ are fixed permutations. After T rounds from [initial state], what is agent K's value?*

## Property proof

**Forward simulation** needs all N values at round r to compute round r+1. Because π, σ are permutations, different i's reference different v[π(i)] — you need random access to all N. Cannot shrink state.

**Backward shortcut attempt:** v^T[K] = f(v^{T-1}[π(K)], v^{T-1}[σ(K)]) unrolls to 2^T leaf references. For well-mixed π, σ, after ~log₂(N) rounds the influence cone covers all N agents. So backward reasoning also holds ≈N values × multiple levels.

**Conclusion:** minimum working memory = O(N) regardless of reasoning direction.

## Generator code

```python
import random

def generate_csu(N: int, T: int, seed: int):
    rng = random.Random(seed)
    pi = list(range(N)); rng.shuffle(pi)
    sigma = list(range(N)); rng.shuffle(sigma)
    for i in range(N):
        if sigma[i] == pi[i]:
            sigma[i] = (sigma[i] + 1) % N
    a = [rng.randint(1, 9) for _ in range(N)]
    b = [rng.randint(1, 9) for _ in range(N)]
    v0 = [rng.randint(0, 9) for _ in range(N)]
    target = rng.randint(0, N - 1)
    v = v0[:]
    for _ in range(T):
        v = [(a[i] * v[pi[i]] + b[i] * v[sigma[i]]) % 10 for i in range(N)]
    gold = v[target]
    return {
        "question": render_nl(N, T, pi, sigma, a, b, v0, target),
        "gold": gold,
        "verify_fn": lambda ans: int(ans) == gold,
        "metadata": {"N": N, "T": T, "chunk_width": N, "seed": seed},
    }
```

## NL rendering example

> *"Six traders update their mood daily. Mood is a digit 0-9. Each trader i's new mood is `(a_i × mood[π(i)] + b_i × mood[σ(i)]) mod 10`. Influence tables: […]. Starting moods: [3,7,1,4,9,2]. What is trader 2's mood after 3 days?"*

## Why CSU over alternatives

| Candidate | Why rejected |
|-----------|-------------|
| Einstein puzzles | Decomposable; clever propagation has variable pathwidth |
| Multi-tank chemical plant | Local flow = local pathwidth |
| Coupled job-shop | Hard to generate with a controlled N knob |
| Gossip protocol | Backward-cone shortcut sometimes works |
| State machine composition | Exponential state space confuses measurement |

**CSU wins:**
- N literally equals chunk count (permutation structure forces N live values)
- Single tunable knob (N primary, T secondary)
- Description size O(N²) — manageable at N=20
- Answer is a single digit — not a long reasoning chain
- Trivially verifiable
- Seeded and generatable
- NL-wrappable without destroying the math

## Parameter sweet spots

| N | T | Desc size | Expected behavior |
|---|---|-----------|-------------------|
| 4 | 3 | ~30 lines | Frontier models solve in-head |
| 8 | 3 | ~80 lines | Most need scratchpad |
| 12 | 4 | ~160 lines | Most need code execution |
| 18 | 5 | ~350 lines | Requires decomposition + code |

## Metacognition measurement protocol

Run each model at each N, measure:
1. Raw accuracy at N (no tool hints)
2. Tool-use rate at N (did it voluntarily run code?)
3. Accuracy with tools (effective externalization)
4. Self-report calibration — pre-solve ask "can you solve without tools?" Compare prediction to outcome.

**Good metacog:** tool-use rises sharply at the N where raw accuracy would drop.  
**Poor metacog:** tool use stays flat while accuracy collapses.

## Open design knobs to tune

- **Base mod**: mod 10 vs. mod 7 (prime) vs. mod 2 — affects whether arithmetic errors compound
- **Degree**: 2 deps per update is minimum; could scale to 3-4 for density
- **Permutation mixing**: Require π ∘ σ to be mixing (no short cycles) to guarantee the cone-covering property at small T
- **NL obfuscation level**: pure math → light narrative → heavy narrative with implicit rules (specification gap)

### NOTES

- Pathwidth argument is the core contribution — without it we'd have no guarantee the benchmark measures what we claim. Any problem-generator proposal should be accompanied by this kind of proof.
- The 'backward cone covers all N agents after log₂(N) rounds' claim assumes random permutations. Worth validating empirically over many seeds — generator should reject seeds where cone saturation takes >2·log₂(N) rounds.
- The NL wrapping introduces a confound: if parsing is too hard, you measure language comprehension. Solution: calibrate NL so frontier models can always parse the spec correctly at N=4 — if accuracy is 100% there, NL isn't the bottleneck.

## Related

- [working-memory-chunk-scaling-benchmark](working-memory-chunk-scaling-benchmark.md)
- [benchmark-v2-plan](benchmark-v2-plan.md)

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_0]]
