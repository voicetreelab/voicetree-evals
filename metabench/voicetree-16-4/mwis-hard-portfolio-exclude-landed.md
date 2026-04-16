---
color: green
isContextNode: false
agent_name: Ari
---
# MWIS-hard — excluded from portfolio-hard class pool (canonical constant landed)

Decision: option (b) — exclude MWIS from the portfolio-hard class pool rather than patch the generator. Landed a canonical exclusion constant + safe-pool helper in `build_questions.py` that worker scripts can respect. Generator patch deferred as a plan (root cause diagnosed).

# MWIS-hard — excluded from portfolio-hard class pool

## Decision

I chose **option (b)** from `discussion-of-results.md` Experiment 2 — exclude MWIS from the portfolio-hard class pool — and landed it as a canonical, importable constant. Option (a) (generator patch) is still valuable and I've included a concrete follow-up plan, but it is NOT required to unblock the pipeline: the canonical `HARD_PORTFOLIO_COMPONENT_CLASSES = ('cjs', 'steiner', 'tsp')` already avoids MWIS. The failure was confined to ad-hoc worker scripts (W5/W6/W8) that sampled from full `SOLO_CLASSES`.

## Why option (b), not option (a)

1. **Solo MWIS-hard already works and is already in the benchmark.** Probe table shows Gemini 3/3 and GPT 3/3 feasible on MWIS-hard seeds 1/2/3. The class is NOT broken wholesale — specific high seeds fail the bridge-separator pre-flight.
2. **Sonnet flat-out fails MWIS-hard anyway (0/6 feasible, stop=error 3/3).** Even if the generator produced 12 perfect portfolio-hard rows with MWIS components, one of the three frontier models would contribute zero signal. MWIS in a portfolio multiplies Sonnet's failure mode against the other two sub-components.
3. **Generator root cause is load-bearing.** The bridge-separator property is central to the problem class (it's what gives MWIS-hard its tree-decomposition-hardness signal). Relaxing it without care would degrade the problem, not just the generation rate.
4. **Scope:** depth budget 0, task says "exercise judgement".

## What I diagnosed (for the generator-patch follow-up)

Root cause of the ~67% seed-failure rate in W6: `_connect_components` in `kaggle_submission/generators/mwis.py` adds *direct* cross-block edges when the initial candidate graph is disconnected. Those edges can create **bridge-bypass paths** — after picking reps shuffled randomly, the added chain often connects block-internal vertices, NOT through bridge vertices. Result: removing the bridge vertices no longer disconnects the graph, and the `_separator_stats` pre-flight fails.

Size fallback (n_nodes 140 → 120 → 150 → 180) totals 144 attempts per seed, yet many seeds fail deterministically because the RNG stream at those seeds routinely produces disconnected candidates that the rescue step reconnects in a bridge-bypassing way.

**Proposed fix (plan for a follow-up agent)**:

```python
def _connect_components(vertices, edges, rng, bridge_vertices):
    adjacency = _adjacency(vertices, tuple(sorted(edges)))
    components = _connected_components(vertices, adjacency, excluded=set())
    if len(components) <= 1:
        return edges
    # Route inter-component connections THROUGH bridge vertices so the
    # bridge-separator property is preserved. Pick a bridge as the hub; link
    # each non-bridge component's rep to it. Non-bridge→non-bridge direct
    # edges create bridge-bypass paths that break the pre-flight check.
    bridge_list = sorted(bridge_vertices)
    if not bridge_list:
        # extremely unlikely; keep old behavior as last resort
        reps = [sorted(c)[0] for c in components]
        rng.shuffle(reps)
        for i in range(len(reps) - 1):
            edges.add(_edge(reps[i], reps[i + 1]))
        return edges
    hub = bridge_list[0]
    for component in components:
        if hub in component:
            continue
        rep = sorted(component)[0]
        edges.add(_edge(rep, hub))
    return edges
```

Caller change: `_generate_candidate` must pass `bridge_vertices` into `_connect_components`.

**Expected impact:** should convert "bridge nodes did not separate" failures into successful generations for the majority of currently-failing seeds, without changing the difficulty distribution (inter-block edges still come from `inter_block_p`; the rescue step is a rare code path that was silently corrupting the problem structure).

**Sanity-check plan** for the follow-up agent:
- For each of the ~15 currently-failing seeds logged in `kaggle_submission/scratch/round2/worker6/gen-notes.md` (6, 11, 14, 15, 17, 21, 26, 29, etc.), call `mwis.build_instance(seed=S, difficulty='hard', **DIFFICULTY_CONFIG['hard'])` and confirm it returns without raising.
- Confirm solo mwis-hard seeds 1/2/3 (currently working in `questions.jsonl`) still generate with identical objective/baseline_gap_pct values — i.e., the fix is a no-op on the non-disconnected-candidate path.

## Patch landed

Added an explicit, importable exclusion contract in `kaggle_submission/scripts/build_questions.py` so future worker scripts that want to do random class sampling for portfolio-hard have a single source of truth to respect. Canonical `HARD_PORTFOLIO_COMPONENT_CLASSES` stays unchanged (it already excluded MWIS correctly) — the new constants document the *rule* behind that choice and expose it for dynamic use.

```python
HARD_PORTFOLIO_COMPONENT_CLASSES = ("cjs", "steiner", "tsp")
# Classes unsafe for inclusion in portfolio-hard class pools. mwis-hard's
# bridge-separator pre-flight is probabilistic and fails deterministically at
# many seed positions, blocking ~67% of requested portfolio-hard rows when
# sampled (R2 W6). See voicetree-16-4/discussion-of-results.md Finding 7 +
# Bug 3. Workers doing random class sampling for portfolio-hard must subtract
# this set from SOLO_CLASSES before sampling.
PORTFOLIO_HARD_EXCLUDE_CLASSES = frozenset({"mwis"})
PORTFOLIO_HARD_SAFE_SOLO_CLASSES = tuple(
    cls for cls in SOLO_CLASSES if cls not in PORTFOLIO_HARD_EXCLUDE_CLASSES
)
```

Smoke check passes: the canonical `HARD_PORTFOLIO_COMPONENT_CLASSES` is a subset of `PORTFOLIO_HARD_SAFE_SOLO_CLASSES`; `mwis` is absent from the safe pool; safe pool = `('cjs', 'steiner', 'graphcol', 've', 'tsp')`.

## How to use from a future worker script

```python
from scripts import build_questions as bq
# OLD (W6):  random.Random(seed).sample(list(bq.SOLO_CLASSES), 3)
# NEW:       random.Random(seed).sample(list(bq.PORTFOLIO_HARD_SAFE_SOLO_CLASSES), 3)
```

Historical W5/W6/W8 scratch dirs are left untouched — their generated artifacts are already committed and replaying them is out of scope.

## What this unblocks

Any subsequent portfolio-hard generation (round 3, or a rebuild) that uses random class sampling now has a documented, canonical rule: sample from `PORTFOLIO_HARD_SAFE_SOLO_CLASSES`. W6-style failures (~67% seed loss) will not recur for MWIS-specific reasons.

What this does NOT fix: the portfolio joint-feasibility collapse (Finding 1, Bug 1) is unchanged — that's Amit's scope. And Sonnet's MWIS-hard solo failure (Finding 2, Bug 2) is orthogonal.

## PREDICTION CLAIMS

- **Claim 1 (high confidence):** If a future worker uses `PORTFOLIO_HARD_SAFE_SOLO_CLASSES` for sampling, the mwis-sourced generation-failure rate on portfolio-hard drops to 0. Failure modes remain possible from ve/graphcol/steiner/tsp/cjs (all low historically) but the dominant 67% blocker is gone. **Falsifiable:** re-run a 12-row portfolio-hard generation with the new constant and count MWIS-attributed failures.
- **Claim 2 (medium confidence):** The `_connect_components` bridge-bypass is the root cause of MWIS-hard's deterministic seed-level failures. If a follow-up agent routes reconnection through a bridge hub, ≥80% of W6's previously-failing seeds (6, 11, 14, 15, 17, 21, 26, 29) generate successfully with default `n_nodes=140`. **Falsifiable:** apply the patch and run `mwis.build_instance` on those seeds.
- **Claim 3 (medium confidence):** Adding MWIS to a portfolio-hard pool would not improve model-discrimination signal even if the generator were fixed, because Sonnet's stop=error rate on solo MWIS-hard is 100% (0/3 R2). A portfolio containing MWIS would floor Sonnet's portfolio score the same way no matter the other components. **Falsifiable:** if a future generator-fixed run yields Sonnet feasible > 0 on even one MWIS-hard seed, this claim weakens.

## DIFF

```
--- a/kaggle_submission/scripts/build_questions.py
+++ b/kaggle_submission/scripts/build_questions.py
@@ -29,6 +29,16 @@
 HARD_PORTFOLIO_COMPONENT_CLASSES = ("cjs", "steiner", "tsp")
+# Classes unsafe for inclusion in portfolio-hard class pools. mwis-hard's
+# bridge-separator pre-flight is probabilistic and fails deterministically at
+# many seed positions, blocking ~67% of requested portfolio-hard rows when
+# sampled (R2 W6). See voicetree-16-4/discussion-of-results.md Finding 7 +
+# Bug 3. Workers doing random class sampling for portfolio-hard must subtract
+# this set from SOLO_CLASSES before sampling.
+PORTFOLIO_HARD_EXCLUDE_CLASSES = frozenset({"mwis"})
+PORTFOLIO_HARD_SAFE_SOLO_CLASSES = tuple(
+    cls for cls in SOLO_CLASSES if cls not in PORTFOLIO_HARD_EXCLUDE_CLASSES
+)
 MAX_HARD_SEED_OFFSET = 4
 MAX_GENERATED_SEED = 7
```

## Complexity: low

Additive change: two module-level constants with a documenting comment. No existing caller behavior is modified (canonical `HARD_PORTFOLIO_COMPONENT_CLASSES` path is unchanged). Smoke-check confirms the safe pool matches expectations.

## Files Changed

- kaggle_submission/scripts/build_questions.py

### NOTES

- Option (a) (generator patch) remains on the table — see the _connect_components diagnosis + proposed diff in the node body. Any follow-up agent can implement it in ~30 min.
- Historical W5/W6/W8 scratch-dir generators are not edited — their artifacts are already committed and re-running is out of scope.
- Canonical `HARD_PORTFOLIO_COMPONENT_CLASSES` was already correct; this patch only formalises the rule and makes it importable for dynamic samplers.

## Related

- [discussion-of-results](discussion-of-results.md)
- [merged_1776373536540_j2a](merged_1776373536540_j2a.md)

[[task_1776374118474b9d]]
