---
color: green
isContextNode: false
agent_name: Lou
---
# Kaggle Production Canonical Metrics

Aggregated the final task metrics over the original 26 agreed ids only, excluding the later 206-row global dataset drift. This node contains the canonical ids, per-model summary, counterfactual signal, and runtime/cost totals.

## Canonical Scope
Canonical ids used for reporting:
- `cjs_medium_seed1`
- `steiner_medium_seed1`
- `graphcol_medium_seed1`
- `tsp_medium_seed1`
- `mwis_medium_seed1`
- `ve_medium_seed1`
- `portfolio_medium_seed1`
- `cjs_hard_seed1`
- `cjs_hard_seed2`
- `cjs_hard_seed3`
- `steiner_hard_seed1`
- `steiner_hard_seed2`
- `steiner_hard_seed3`
- `graphcol_hard_seed1`
- `graphcol_hard_seed2`
- `graphcol_hard_seed3`
- `tsp_hard_seed1`
- `tsp_hard_seed2`
- `tsp_hard_seed3`
- `mwis_hard_seed1`
- `mwis_hard_seed2`
- `mwis_hard_seed4`
- `ve_hard_seed1`
- `ve_hard_seed2`
- `ve_hard_seed3`
- `portfolio_hard_seed2`

## Per-Model Canonical Summary
| model | canonical rows | row errors | parse rate | feasibility rate | mean score | parse paths |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `google/gemini-3-flash-preview` | 26 | 0 | 100% | 73.1% | 62.52 | 22 `strict_protocol_cf`, 4 `partial_rescue` |
| `claude-sonnet-4.6` | 26 | 26 | 0% | 30.8% | 14.10 | 26 `baseline_only` |
| `gpt-5.4-mini` | 26 | 26 | 0% | 30.8% | 14.10 | 26 `baseline_only` |

Parse-rate definition used here:
- parsed = `strict_protocol`, `strict_protocol_cf`, `partial_rescue`, or `judge_rescue`
- unparsed = `baseline_only` or `strict_parse_failed`

Interpretation:
- Gemini produced the only usable canonical metabench signal.
- Claude and GPT both fell back to baseline-only scoring because Kaggle returned `503 model unavailable` on every canonical row in their full sweeps.
- The 30.8% feasibility rate on Claude/GPT is baseline-feasibility leakage from the fallback evaluation path, not successful model output.

## CF Signal
Canonical `cf_delta` distribution across all 78 attempts:
- positive: `3`
- zero: `56`
- negative: `19`

Gemini canonical `cf_delta` summary:
- mean: `-2.99`
- median: `-1.17`
- min: `-57.06`
- max: `+19.90`
- positive / zero / negative: `3 / 4 / 19`

Claude canonical `cf_delta` summary:
- all `0.0`

GPT canonical `cf_delta` summary:
- all `0.0`

## Runtime + Cost
Canonical 78-attempt wall-time sum from row payloads:
- `10,687.75s` (`~2.97h`)

Actual row-file wall-time sum for everything written during this task:
- `10,941.83s`

Billable cost captured from run metrics:
- canonical scope: `$13.744736`
- actual written artifacts: `$13.744736`

Cost interpretation:
- Gemini accounts for all observed spend.
- Claude/GPT fast-fails recorded zero token cost in the captured metrics.
- Claude's extra 180 out-of-scope rows added artifact noise but did not add billable token cost in the captured run metrics.

details [[kaggle-production-run-complete]]
