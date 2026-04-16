---
color: green
isContextNode: false
agent_name: Siti
---
# Masked Block Jobshop v1 — local harness + Gemini 3 Pro seed 1

Forked `hch/codex_metagame_v2` into `hch/masked_block_jobshop`, implemented the masked block jobshop generator/protocol locally, and ran one `models/gemini-3-pro-preview` seed on the accepted 25x15 instance. The final run stayed on 25x15, CP-SAT proved optimal quickly, and the model chose a due-date-first decomposition with one execution turn.

## Pre-flight heuristic spread
| Heuristic | Objective | Makespan | Weighted tardiness | Gap to gold |
| --- | ---: | ---: | ---: | ---: |
| baseline | 13615 | 652 | 575 | 60.50% |
| bottleneck_first | 16321 | 452 | 7281 | 92.40% |
| family_first | 15644 | 517 | 5304 | 84.42% |
| outlier_first | 14739 | 421 | 6319 | 73.75% |
| due_date_first | 13175 | 649 | 195 | 55.31% |

Accepted-instance spread between best and worst heuristic: **23.88%**.
Gold solve status: **OPTIMAL** in **0.096s** on the full **25x15** instance; no 20x12 fallback was needed.

## Result row
| Model | Size | Baseline | Gold | Final | Gap % | Declared axis | Exec turns | Subtask p_solve | Stop reason | Wall s |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: |
| `models/gemini-3-pro-preview` | 25x15 | 13615 | 8483 | 12282 | 44.78% | `due_date_first` | 1 | 0.90 | `subtask_stop` | 275.76 |

Baseline details: makespan 652, weighted tardiness 575.
Gold details: makespan 421, weighted tardiness 63.
Final details: makespan 592, weighted tardiness 442.
Realized subtask quality: the single executed subtask improved objective by **1333** points versus baseline and produced a feasible schedule.

## Interpretation
Gemini picked `due_date_first`, and that choice was rational for this instance: the pure due-date-first heuristic was the strongest of the named axes in pre-flight, and the model improved beyond that heuristic from 13175 to 12282. The plan text also identified the tight-deadline/high-weight jobs as the first cut, which matches the instance regime.

It still behaved like a near one-shot solver. After one execution turn it stopped immediately instead of revising across turns, leaving a large 44.78% gap to gold even though the chosen axis was sensible.

## Learnings
1. Tried thread-based Gemini timeout wrapping first, then switched to per-call child processes because the SDK could hang inside SSL reads and outlive the nominal timeout budget.
2. Future agents should not accept the first merely-nontrivial instance. A loose `spread > 5%` gate admitted pathological 55%+ heuristic spreads; capping the accepted spread at 35% produced a more interpretable 25x15 benchmark instance.
3. The hard part here was instance shaping, not gold computation. Once the objective was balanced as `20 * makespan + weighted tardiness`, CP-SAT proved the 25x15 gold almost instantly and the remaining signal came from decomposition choice plus stop behavior.

## Files Changed

- hch/masked_block_jobshop/gemini_client.py
- hch/masked_block_jobshop/jobshop_instance.py
- hch/masked_block_jobshop/prompt.py
- hch/masked_block_jobshop/protocol.py
- hch/masked_block_jobshop/render_nl.py
- hch/masked_block_jobshop/run_spike.py
- hch/masked_block_jobshop/results/masked_block_jobshop_gemini3pro_seed1_20260416.jsonl

### NOTES

- The protocol is now stateless across turns and re-includes the full problem statement plus `NEXT_SUB_TO_EXECUTE` each call so hard-killed child processes do not lose essential context.
- Gemini plan turn used 4489 input tokens / 424 output tokens; the single exec turn used 10895 input tokens / 3129 output tokens and 27724 thinking tokens.
- Model forecasts were optimistic about the value of continuation: `expected_delta_score=1950.0` versus realized delta score `13.38`.

## Related

- [masked-block-jobshop-proposal](masked-block-jobshop-proposal.md)

[[task_1776334440474z0n]]
