---
color: green
isContextNode: false
agent_name: Ama
---
# Bayesian VE v1 — local harness + Gemini 3 Pro seed 1

Built `hch/bayesnet_ve/` as a local planstate spike with deterministic block-DAG generation, exact VE, heuristic/random-order pre-flight, and a Gemini protocol loop. Ran one `models/gemini-3-pro-preview` seed-1 evaluation on the accepted 22-variable instance; Gemini chose `min_fill`, took one execution turn, and finished with a `0.0002955`-nat log-gap.

## Implementation
- Added `hch/bayesnet_ve/bayesnet_instance.py` with a deterministic block-DAG generator, CPT rendering, exact variable elimination, heuristic/random-order pre-flight, and strict validation for `BEST_GUESS` posterior/order/peak fields.
- Added `hch/bayesnet_ve/protocol.py` to mirror the masked-block-jobshop planstate contract while adapting execution-turn verification to posterior log-gap and true-vs-self-reported peak-factor size.
- Added `hch/bayesnet_ve/run_spike.py`, `prompt.py`, `render_nl.py`, `gemini_client.py`, and `__init__.py` so the spike runs locally with the required `models/gemini-3-pro-preview` default and writes the dated JSONL result file.
- Reused the masked-block-jobshop timeout/process-kill pattern, but removed the misleading deterministic-incumbent semantics: exact VE makes every solver-computed ordering return the same posterior, so the harness now treats “best so far” as the model estimate with the smallest realized log-gap.

## Pre-flight heuristic peaks
| Ordering | Peak factor size |
| --- | ---: |
| baseline | 11 |
| min_neighbors | 6 |
| min_weight | 7 |
| min_fill | 6 |
| random_best_of_1000 | 7 |

Accepted instance facts:
- Total variables: `22`
- Accepted attempt: `5`
- Size escalated: `False`
- Gold source: `min_fill`
- Gold peak factor size: `6`
- Exact posterior `P(B7=1 | evidence)`: `0.49014481565752194`

## Result row
| Model | Vars | p_hat | p* | Gap nats | Declared axis | Declared ordering prefix | Self peak | True peak | Exec turns | Stop reason | Wall s |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | ---: | --- | ---: |
| `models/gemini-3-pro-preview` | 22 | 0.490000 | 0.490145 | 0.0002955 | `min_fill` | `["B6", "B5", "A1", "C1", "C5", "BR01", "A4"]` | 6 | 6 | 1 | `subtask_stop` | 408.14 |

Declared axis rationale:
`The min-fill heuristic minimizes the number of new edges added to the interaction graph during variable elimination. This directly minimizes the size of the largest clique created, which corresponds to the maximum intermediate factor size. By using min-fill, the maximum scope size is kept to 6 variables (64 entries), making exact computation highly tractable.`

Full validated `ordering_used` from the execution turn:
`["B6", "B5", "A1", "C1", "BR01", "C5", "A4", "A5", "C4", "C3", "B2", "BR12", "A2", "A3", "B3", "D0"]`

Initial `PLAN_STATE`:
`Elimination order: B6, B5, A1, C1, C5, BR01, A4, A5, C4, C3, B2, BR12, A2, A3, B3, D0. Max scope size is 6. Subtasks: 1. Eliminate B6, B5 (barren). Compute F_A1(A2, A3) and F_C1(B2, C3). 2. Compute F_C5(B3, C3, C4, D0) and F_BR01(A2, B2, B3). 3. Compute F_A4(A2, A3, D0, A5). 4. Compute F_A5(A2, A3, D0, BR12, B7). 5. Compute F_C4(B2, B3, C3, D0, BR12). 6. Compute F_C3(A3, B2, B3, D0, BR12). 7. Compute F_B2(A2, A3, B3, D0, BR12). 8. Compute F_BR12(A2, A3, B3, D0, B7). 9. Compute F_A2(A3, B3, D0, B7) and F_A3(B3, D0, B7). 10. Compute F_B3(D0, B7), F_D0(B7), and normalize to find P(B7=1 | evidence).`

Final `PLAN_STATE`:
`Exact inference completed successfully. All variables eliminated. Peak factor size was 6. Final probability computed.`

Turn timings:
- Plan turn wall time: `133.61832695803605` s
- Exec turn wall time: `272.8822552089114` s

## Interpretation
Gemini picked the same axis as the pre-flight gold (`min_fill`), produced a valid full elimination order, and self-reported the true peak factor size exactly (`6`). The answer quality was essentially exact on the first execution turn, with only a `0.0002955`-nat log-gap from the deterministic posterior.

Behaviorally, it still looked like a one-shot solver: one long execution turn and then immediate stop once it had a confident final probability. That means the spike succeeded as a decomposition-quality benchmark, but it did not elicit multi-turn self-correction on this seed.

## Learnings
1. Tried to port the masked-block-jobshop loop literally, then changed approach because exact VE breaks the notion of a deterministic incumbent: any exact solver order yields the same posterior, so the harness has to rank model turns by realized log-gap, not by “improving” a solver-provided baseline answer.
2. Future agents should not implement `min_weight` as pure domain-product on this binary-only problem. That collapses onto min-neighbors. The harness instead uses current incident factor mass so the declared-axis space stays non-degenerate.
3. A future agent diagnosing a long run should not assume the parent Python process is hung just because the terminal is quiet. The runner prints only at start and finish; each model call happens in a spawned subprocess, so the process table is the reliable way to tell whether the spike is inside a live exec turn or actually stuck.

## Files Changed

- hch/bayesnet_ve/__init__.py
- hch/bayesnet_ve/bayesnet_instance.py
- hch/bayesnet_ve/gemini_client.py
- hch/bayesnet_ve/prompt.py
- hch/bayesnet_ve/protocol.py
- hch/bayesnet_ve/render_nl.py
- hch/bayesnet_ve/run_spike.py
- hch/bayesnet_ve/results/bayesnet_ve_gemini3pro_seed1_planstate_20260416.jsonl

### NOTES

- A `requests` dependency warning from the local Python environment appeared during the live run but did not block the Gemini API call or corrupt the result.
- The accepted instance stayed at 22 variables on attempt 5, so the 26-28 variable fallback path was implemented but not used for this seed.
- Gemini returned `p_solve=0.0` for the queued subtask even though the same turn produced an essentially exact answer; that makes the continuation-calibration fields worth revisiting later.

## Related

- [bayesnet-ve-proposal](bayesnet-ve-proposal.md)

[[task_1776340059062d0k]]
