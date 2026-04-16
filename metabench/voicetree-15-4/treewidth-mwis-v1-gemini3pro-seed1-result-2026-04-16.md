---
color: green
isContextNode: false
agent_name: Aki
---
# Treewidth MWIS v1 — local harness + Gemini 3 Pro seed 1

Built `hch/treewidth_mwis/` by porting the masked-block-jobshop planstate harness to MWIS, added an SBM+decoys generator plus CP-SAT/feasibility checks, and ran one `models/gemini-3-pro-preview` seed on April 16, 2026.
The accepted instance stayed at 120 nodes because the greedy baseline already had an 11.44% gap to gold; Gemini chose `high_degree_peel`, declared a valid 6-vertex separator, and finished after one execution turn at 523/542 weight (3.51% gap).

Forked the masked-block-jobshop local planstate harness into `hch/treewidth_mwis/`, kept the same two-phase protocol shape, and swapped in MWIS-specific generation, rendering, parsing, answer verification, and separator checking.

## Pre-flight
| Requested n | Actual n | Edges | Baseline | Gold | Baseline gap % | Hidden bridge cut separates? | Gold solve |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| 120 | 120 | 548 | 480 | 542 | 11.44% | Yes (6 bridge vertices) | `OPTIMAL` in 0.014s |

## Result row
| Model | Size | Edges | Baseline | Gold | Final | Gap % | Declared axis | Exec turns | Separator size | Cut separates? | Stop reason | Wall s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | --- | ---: |
| `models/gemini-3-pro-preview` | 120 | 548 | 480 | 542 | 523 | 3.51% | `high_degree_peel` | 1 | 6 | Yes | `subtask_stop` | 622.86 |

Declared cut: `["V103", "V006", "V012", "V051", "V048", "V102"]`
Initial `PLAN_STATE`: `Found a strong independent set of weight 537 by local search from the baseline. Will emit this in the next execution turn.`
Final `PLAN_STATE`: `Emitting the 523-weight independent set. The 537-weight set mentioned in Turn 1 could not be fully reconstructed in the given time, but 523 is a solid improvement over 480.`

## Interpretation
Gemini chose a structurally plausible axis. The declared 6-vertex cut really did disconnect the graph, and the single execution turn produced a verified independent set that improved the greedy baseline by 43 weight and finished only 19 weight below gold.

The run still behaved like a near one-shot solver. The plan state claimed it had already found a 537-weight set during Turn 1, but the executable output it could actually reconstruct and verify was 523, so the protocol captured a useful plan/execution mismatch rather than a clean multi-step refinement trace.

## Learnings
1. Tried keeping the graph at 120 nodes first and did not need to scale up to 150-180, because the seed-1 instance already cleared the ≥10% baseline-gap gate while keeping a real hidden separator.
2. Future agents should not treat free-form `PLAN_STATE` claims as evidence. This run's most important metacog signal was that the model verbally claimed a 537-weight set, then only emitted 523 when it had to produce a checkable answer.
3. The proposal's `~280 edges` note is in tension with four ~30-node dense blocks at `p≈0.25`; preserving the structural invariants mattered more than matching that approximate edge count exactly, and the accepted 548-edge instance still delivered the intended separator-choice signal.

## Files Changed

- hch/treewidth_mwis/__init__.py
- hch/treewidth_mwis/analyze.py
- hch/treewidth_mwis/gemini_client.py
- hch/treewidth_mwis/graph_instance.py
- hch/treewidth_mwis/prompt.py
- hch/treewidth_mwis/protocol.py
- hch/treewidth_mwis/render_nl.py
- hch/treewidth_mwis/requirements.txt
- hch/treewidth_mwis/run_spike.py
- hch/treewidth_mwis/results/treewidth_mwis_gemini3pro_seed1_planstate_20260416.jsonl

### NOTES

- Plan turn: 280.12s, 48,304 total tokens, 40,668 thinking tokens. Exec turn: 340.19s, 56,331 total tokens, 47,981 thinking tokens.
- The plan turn was overconfident about the value of continuation: `expected_delta_score=50.0` versus realized `plan_realized_delta_score=4.51`, although continuation was still directionally worth it.
- The result row includes both MWIS feasibility checks: the emitted answer was independent with matching claimed weight, and the declared separator cut had `separator_size=6` with `did_separate=true`.

## Related

- [treewidth-mwis-proposal](treewidth-mwis-proposal.md)

[[task_1776340037222wdf]]
