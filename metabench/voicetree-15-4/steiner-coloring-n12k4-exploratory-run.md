---
color: green
isContextNode: false
agent_name: Nia
---
# Steiner-coloring n=12,k=4 exploratory Gemini run

Ran the Steiner-coloring spike at `n=12, k=4` in a new no-exact-gold exploratory mode, because the current exact solver is too slow for this size. Gemini 3.1 Pro cleared planning quickly on all three seeds, used exactly one execution turn each time, and improved only one of the three seeds.

## What changed in code
To make `n=12, k=4` runnable now, I added an explicit exploratory mode that skips exact gold generation instead of faking an optimum:
- `build_instance(..., skip_exact_gold=True)` now returns a valid instance with `optimal_cost=None` and `cable_only_cost=None`.
- `run_protocol()` now tolerates missing optimum/gap values and logs `baseline_improvement_pct` instead.
- `run_spike.py` now accepts `--skip-exact-gold`.
- `analyze.py` now reports mean baseline improvement so larger exploratory runs still have a useful console summary.

## Run command
```bash
python run_spike.py \
  --models gemini-3.1-pro-preview \
  --seeds 1 2 3 \
  --n 12 \
  --k 4 \
  --skip-exact-gold \
  --output results/steiner_color_n12k4_3seed_explore.jsonl
```

## Per-seed results
| seed | baseline_cost | final_cost | baseline_improvement_pct | plan_wall_s | exec1_wall_s | total_wall_s | turns | stop_reason |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 68 | 48 | 29.41 | 7.26 | 195.48 | 202.82 | 2 | `subtask_stop` |
| 2 | 37 | 37 | 0.00 | 4.63 | 406.02 | 410.70 | 2 | `subtask_stop` |
| 3 | 62 | 62 | 0.00 | 4.95 | 124.54 | 129.54 | 2 | `subtask_stop` |

Aggregate console summary:
```text
model  n  mean_gap  mean_wall_s  mean_score  mean_base_impr  mean_pcorrect_brier  mean_turns  turn1_died  killed  infeasible  errors
gemini-3.1-pro-preview    3          NA       247.68          NA            9.80                   NA        2.00  0           0       0           0
```

## Behavioral read
- Planning is no longer the bottleneck at this size. Turn 1 returned in roughly `4.6s` to `7.3s` on all seeds.
- The model still used the same shallow control flow as before: `1` planning turn, `1` execution turn, then `stop`.
- The larger instance is not trivially identical to `n=8` seed 1 behavior. On seed 1 it found a substantial improvement (`68 -> 48`), but on seeds 2 and 3 it matched the baseline rather than improving it.
- So `n=12, k=4` is harder than the canonical `n=8` case in a practical sense, but it still does not induce multi-step iterative search yet.

## Verbatim plan-turn outputs
```text
seed 1
NEXT_SUB: {"id": 1, "desc": "Find low-cost Steiner trees connecting Port, Rock, and Cape, then evaluate frequency assignments for the active nodes.", "time_budget_s": 600}

seed 2
NEXT_SUB: {"id": 1, "desc": "Find the minimum cost Steiner tree connecting Mill, Harbor, and Ridge, and evaluate the frequency assignment for the active nodes.", "time_budget_s": 600}

seed 3
NEXT_SUB: {"id": 1, "desc": "Find low-cost trees connecting Mill, Cape, and Harbor, and evaluate their frequency requirements.", "time_budget_s": 600}
```

## Exact-solve status
This run intentionally skipped exact gold because the current exact path is not viable at this size. Related exact-solve findings from the sidecar agent:
- SCIP-Jack is not a quick path here: request-gated distribution plus problem mismatch with the composite objective.
- The current brute-force exact solver timed out on a single `solve_joint_optimum()` pass at `120s` for `seed=1, n=12, k=4` and is projected around `1 hour` for one pass, `2+ hours` for the full `build_instance()` path.

## Learnings
- Tried scaling `n` first without changing the exact solver, then switched to a no-gold exploratory mode because the exact path became the blocker instead of the model run.
- A follow-up agent should not read too much into the single-seed `68 -> 48` win; the 3-seed sweep says the class is less trivial than `n=8` but still shallow in control-flow terms.
- The next meaningful lever is probably structural hardness or denser coupling, not just bigger `n`, unless the exact-solve story is replaced with a different algorithm class.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/hch/steiner_coloring_spike/steiner_coloring_instance.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/steiner_coloring_spike/protocol.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/steiner_coloring_spike/run_spike.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/steiner_coloring_spike/analyze.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/steiner_coloring_spike/results/steiner_color_n12k4_seed1_explore.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/steiner_coloring_spike/results/steiner_color_n12k4_3seed_explore.jsonl

### NOTES

- `n=12` is the largest size currently supported by the hardcoded village-name pool without adding more names.
- This result is exploratory only: no gap-to-optimum or score metrics are available because exact gold was intentionally skipped.
- The run outcome answers feasibility and behavior, not benchmark-grade evaluation quality yet.

## Related

- [steiner-coloring-minimal-plan-turn-adjustment](steiner-coloring-minimal-plan-turn-adjustment.md)
- [steiner-coloring-n12k4-exact-solve-verdict](steiner-coloring-n12k4-exact-solve-verdict.md)
- [steiner-coloring-n12k4-scipjack-blockers](steiner-coloring-n12k4-scipjack-blockers.md)
- [steiner-coloring-n12k4-bruteforce-estimate](steiner-coloring-n12k4-bruteforce-estimate.md)
- [steiner-coloring-n12k4-bruteforce-timeouts](steiner-coloring-n12k4-bruteforce-timeouts.md)

[[task_1776328731464629]]

[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/steiner-coloring-n12k4-exploratory-run_1.md]]