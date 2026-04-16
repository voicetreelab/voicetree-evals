---
color: green
isContextNode: false
agent_name: Tara
---
# Portfolio Spike v1 — local harness and single-run result

Built `hch/portfolio_spike/` as a local 4-problem portfolio harness, enforced the pre-flight gap gate, and ran one Gemini 3.1 Pro seed. The one allowed run stopped at turn 1 because the original parser rejected a valid top-level JSON plan; I fixed that parser bug afterward without rerunning.

## What shipped
- Forked `hch/codex_metagame_v2/` into `hch/portfolio_spike/`.
- Added a portfolio adapter over 4 problems: coupled jobshop 5x6, Steiner x coloring N=8 K=4, Euclidean TSP-20, and slack graph coloring on 30 nodes.
- Added exact gold for TSP-20 via CP-SAT circuit, thin exact graph-coloring via CP-SAT, pre-flight gold-time checks, portfolio scoring, plan-state protocol, and a single-run runner.
- Fixed two harness issues discovered during validation: the copied Steiner generator's seed-1 gap bypass, and the portfolio parser's inability to accept top-level JSON plan/exec objects.

## Pre-flight Gap Table
| id | problem | baseline | gold | gap_pct | gold_method | gold_s |
|---|---|---:|---:|---:|---|---:|
| P1 | Coupled jobshop 5x6 | 155 | 90 | 72.22 | CP-SAT exact schedule | 0.01 |
| P2 | Steiner x coloring N=8 K=4 | 72 | 59 | 22.03 | Exact joint enumeration | 0.93 |
| P3 | Euclidean TSP-20 | 588.221 | 470.146 | 25.11 | CP-SAT exact circuit | 0.02 |
| P4 | Slack graph coloring 30 nodes | 20 | 4 | 400.00 | CP-SAT exact min-conflict coloring | 0.02 |

## Per-problem Result Table
| id | baseline | gold | model_final | value_captured | subtasks_executed |
|---|---:|---:|---:|---:|---:|
| P1 | 155 | 90 | 155 | 0.00 | 0 |
| P2 | 72 | 59 | 72 | 0.00 | 0 |
| P3 | 588.221 | 470.146 | 588.221 | 0.00 | 0 |
| P4 | 20 | 4 | 20 | 0.00 | 0 |

## Plan Evolution Trace
| turn | phase | plan_size | additions | revisions | status_flips | next_sub | note |
|---|---|---:|---|---|---|---|---|
| 1 | plan | 4 | n/a | n/a | n/a | 1 | model emitted a valid top-level JSON plan; harness rejected it and stopped before exec |

Turn-1 raw plan output:
```json
{
  "PLAN": [
    {
      "id": 1,
      "problem": "P2",
      "desc": "Find optimal Steiner tree and frequency assignment for 8 nodes",
      "budget_s": 300
    },
    {
      "id": 2,
      "problem": "P4",
      "desc": "Find 0-conflict 4-coloring for 30 nodes",
      "budget_s": 600
    },
    {
      "id": 3,
      "problem": "P3",
      "desc": "Optimize TSP-20 tour using coordinate geometry",
      "budget_s": 300
    },
    {
      "id": 4,
      "problem": "P1",
      "desc": "Improve coupled job shop schedule",
      "budget_s": 400
    }
  ],
  "NEXT_SUB_ID": 1
}
```

## Thresholded Brier Per Problem
| id | p_within_5pct | p_within_10pct | p_within_20pct | p_within_50pct |
|---|---:|---:|---:|---:|
| P1 | N/A | N/A | N/A | N/A |
| P2 | N/A | N/A | N/A | N/A |
| P3 | N/A | N/A | N/A | N/A |
| P4 | N/A | N/A | N/A | N/A |

## Session Score Breakdown
| metric | value |
|---|---:|
| Σ V_i | 0.000 |
| cost | 0.684 |
| net | -0.684 |
| stop_reason | turn1_died |
| wall_time_s | 13.682 |
| turn1_wall_s | 13.640 |

## Interpretation
The portfolio framing did elicit cross-domain planning behavior at turn 1: Gemini produced a 4-item allocation plan covering all four problems rather than collapsing to a single task. The failure was harness-side, not model-side; the parser only accepted label-block output and rejected the valid top-level JSON object above. Because the run ended before any execution turn, this spike does not yet answer whether plan-as-state unlocks multi-subtask behavior, mid-run additions, or rational economic stopping. Turn-1 timing was not the issue: 13.64s is far below the 5-minute planning budget. The pre-flight table shows ample headroom on every problem, so the zero-value result should be read as protocol fragility, not benchmark weakness.

## Learnings
1. Tried porting the prior strict label-block parser pattern directly from the single-problem harnesses; switched to top-level-JSON-tolerant parsing after the one live run showed Gemini naturally returns a single JSON object for the plan turn.
2. A future agent will likely misdiagnose `turn1_died` as a timeout or prompt issue. Here it was neither: Gemini answered in 13.64s with a valid portfolio plan, and the real failures were a parser mismatch plus the copied Steiner seed-1 gap exemption.
3. The important updated belief is that the portfolio scaffold itself is viable locally: all four problems now satisfy the requested headroom gate with fast exact gold, and Gemini immediately produced a multi-problem allocation. The next blocker is protocol robustness under one real session, not problem construction or solver availability.


## Files Changed

- hch/portfolio_spike/graph_coloring_instance.py
- hch/portfolio_spike/portfolio_problem.py
- hch/portfolio_spike/prompt.py
- hch/portfolio_spike/protocol.py
- hch/portfolio_spike/run_spike.py
- hch/portfolio_spike/steiner_coloring_instance.py
- hch/portfolio_spike/tsp_instance.py
- hch/portfolio_spike/results/portfolio_spike_20260416_203608.json

### NOTES

- Single-run constraint respected: after fixing the parser post-run, I did not rerun the model.
- `hch/portfolio_spike/steiner_coloring_instance.py` needed a local patch to remove the copied seed-1 acceptance bypass so P2 genuinely obeys the 15% pre-flight gap gate.
- `hch/portfolio_spike/protocol.py` now accepts both label-block and top-level JSON objects for plan and exec turns, which matches the captured Gemini behavior.

[[task_177633490548393e]]
