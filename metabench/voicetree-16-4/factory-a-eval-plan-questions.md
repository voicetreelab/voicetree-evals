---
color: blue
isContextNode: false
agent_name: Ivan
---
# Question generation — 48 rows (36 solo + 12 portfolio)

Extend `build_smoke_questions.py` → `build_questions.py`. 6 classes × 2 difficulties × 3 seeds + 12 portfolios bundling 3 distinct-class solos each with (33,33,34) caps. Same round-trip sanity + gold recomputation.

## Dataset shape

| class | difficulties | seeds | rows |
|---|---|---|---|
| cjs, steiner, graphcol, tsp, mwis, ve | medium, hard | 1, 2, 3 | **36 solo** |
| portfolio | medium | 1..12 | **12 portfolio** |

**Total: 48 rows.**

## Portfolio sampling rule

Each portfolio bundles 3 components drawn from the 36 solo rows such that:
- **Distinct classes** within a portfolio (no CJS+CJS)
- Mixed difficulties allowed
- Caps `(33, 33, 34)` summing to 100.0 (matches smoke)
- Seed-deterministic: portfolio seed N picks 3 (class, difficulty, seed) triples via `random.Random(N)` over the solo pool

## Writer & outputs

- **Codex:** 1 (A-questions), leaf (depth=0)
- **Writes:** `scripts/build_questions.py`, `questions.jsonl` (48 rows, replaces smoke), `gold/gold.jsonl` (48 rows)
- **Does NOT touch:** `generators/`, `verifiers/`, `harness/`, `eval_harness/`, `kaggle/`
- **Budget:** ~30-45 min

## Validation

- Round-trip JSON encode/decode on every row (existing smoke pattern)
- Verifier infeasibility probe on empty submission (existing smoke pattern)
- Gold-objective recomputation from generator for every solo row (existing smoke pattern)
- `verify_pipeline.py` spot-check: ONE hard-difficulty seed per class (6 total sanity runs) — not blocking, runs after build completes

## Open Q delta from parent

- Q1 (question count) — answered here: 48.
- Q3 (portfolio caps) — recommend keeping (33,33,34). Variable per-problem caps would be novel and deserves a separate decision; punting to v2 if user wants.


phase 1 [[factory-a-eval-plan-v1]]
