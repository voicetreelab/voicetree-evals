---
color: green
isContextNode: false
agent_name: Bob
---
# MBJ spike — mbj_medium_seed1 landed end-to-end

Ported masked_block_jobshop as a 7th class for a single-row spike. mbj_medium_seed1 in questions.jsonl, round-trip passes, prompt renders, protocol parses a stubbed gold BEST_GUESS with gap=0.0%. Generator produces in ~30ms on 8 jobs × 8 machines.

# MBJ port spike — landed

## Scope

Single-row spike to prove the port path. `mbj_medium_seed1` only (no hard, no portfolio integration, no seeds 2..n). MBJ is kept **out** of `SOLO_CLASSES` intentionally so portfolio assembly, hard-seed fallback, and worker sampling code remain untouched.

## Acceptance criteria — all verified

1. ✅ **`mbj_medium_seed1` in `questions.jsonl`** — `python scripts/build_questions.py` wrote 27 rows (was 26). Inspection: `id=mbj_medium_seed1 difficulty=medium seed=1 gold=5700.0 baseline=7167.0`. Classes present: `['cjs', 'graphcol', 'mbj', 'mwis', 'portfolio', 'steiner', 'tsp', 've']`.

2. ✅ **`_sanity_check_round_trip` passes** — script printed `Verified schema round-trip.`. The round-trip also exercises the infeasibility path: `verifier(instance, {})` returns `feasible=False, reason="schedule must contain a machines object"`.

3. ✅ **Harness can construct the prompt without crashing.** Verified all three prompt-builders:
   - `render_nl(instance, 'mbj')` → 2604 chars (uses embedded `problem_statement`)
   - `build_turn1_prompt(nl, cls='mbj')` → 3967 chars (display name renders as "Masked Block Job-Shop")
   - `build_exec_prompt(..., cls='mbj', ...)` → 8064 chars (includes the BEST_GUESS schema block for `mbj` verbatim)

4. ✅ **Stretch: protocol parses a stubbed MBJ response.** Mocked an LLM response with the gold schedule as `BEST_GUESS`. `parse_exec_turn` returned all 8 expected keys; `mbj_v.verify(instance, parsed['best_guess'])` returned `feasible=True, gap_pct=0.000`.

## Verifier behaviour (exhaustive)

| Submission | feasible | gap_pct | reason |
|---|---|---|---|
| baseline schedule | True | 25.737 | — |
| gold schedule | True | 0.000 | — |
| `{}` | False | 100.0 | `schedule must contain a machines object` |
| `None` | False | 100.0 | `schedule must be an object` |

## One-line repro

From `metabench/kaggle_submission/`:

```bash
python scripts/build_questions.py   # writes 27 rows including mbj_medium_seed1
```

## Blockers / skipped

- **No LLM calls** (per brief). Exercised the parse + verify path with a mocked response.
- **MBJ not added to `SOLO_CLASSES`.** Intentional — adding it would propagate into portfolio sampling, hard-seed fallbacks, and worker scripts. Follow-up scope.
- **`hch/masked_block_jobshop/` untouched.** Pilot code stays as reference; I copied load-bearing logic rather than cross-import.
- **Heuristic spread bounds relaxed** (3–60% vs pilot 5–35%) because 8×8 has tighter natural spread than 25×15. Retune if MBJ graduates to full benchmark status.

See child nodes for distinctness analysis, file-by-file diffs, and prediction claims.

## Files Changed

- kaggle_submission/generators/mbj.py
- kaggle_submission/verifiers/mbj.py
- kaggle_submission/verifiers/__init__.py
- kaggle_submission/harness/prompt.py
- kaggle_submission/harness/render_nl.py
- kaggle_submission/scripts/build_questions.py
- kaggle_submission/questions.jsonl

[[task_1776376871106qte]]
