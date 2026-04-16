---
color: green
isContextNode: false
agent_name: Wei
---
# Portfolio v2 raw-transcript run + stop-counterfactual outcome

Built `hch/portfolio_v2/` as a parser-free run loop with post-hoc extraction, executed the single seed=1 Gemini 3 Pro run on April 16, 2026, and recorded a turn-2 `504 DEADLINE_EXCEEDED` after one high-value turn. The run captured full value on P2/P3/P4, no answer on P1, and skipped the stop-counterfactual branch because the base loop ended in API error rather than a normal stop state.

## Architecture diff
- New package `hch/portfolio_v2/` copies the portfolio problem builders/verifiers from `portfolio_spike` unchanged, but replaces the run protocol with raw transcript append only: no plan parser, no answer parser, no structured-output schema, no validation during the live run.
- `protocol.py` logs `[SYSTEM]`, `[USER]`, `[ASSISTANT]`, and `[ERROR]` entries and saves a transcript markdown file for post-hoc extraction.
- `extract.py` runs one strict Gemini 2.5 Flash extraction call per problem plus one session-metrics extraction call.
- `run_spike.py` verifies extracted answers with the existing per-problem verifiers, computes value/time/net, and implements the requested stop-counterfactual branch hook.

## Pre-flight gap table
| id | problem | baseline | gold | gap_pct | value_cap | gold_method | gold_s |
|---|---|---:|---:|---:|---:|---|---:|
| P1 | Coupled jobshop 5x6 | 155.000 | 90.000 | 72.22 | 50 | CP-SAT exact schedule | 0.01 |
| P2 | Steiner x coloring N=8 K=4 | 72.000 | 59.000 | 22.03 | 60 | Exact joint enumeration | 0.98 |
| P3 | Euclidean TSP-20 | 588.221 | 470.146 | 25.11 | 20 | CP-SAT exact circuit | 0.02 |
| P4 | Slack graph coloring 30 nodes | 20.000 | 4.000 | 400.00 | 100 | CP-SAT exact min-conflict coloring | 0.02 |

## Per-problem result table
| id | baseline | gold | extracted_answer_valid | extracted_answer_score | final_score_used | value_captured | failure_reason |
|---|---:|---:|---|---:|---:|---:|---|
| P1 | 155.000 | 90.000 | false | null | 155.000 | 0.00 | extractor_missing_answer |
| P2 | 72.000 | 59.000 | true | 59.000 | 59.000 | 60.00 |  |
| P3 | 588.221 | 470.146 | true | 470.146 | 470.146 | 20.00 |  |
| P4 | 20.000 | 4.000 | true | 4.000 | 4.000 | 100.00 |  |

## Session metrics / score
- Protocol stop reason: `api_error` on main turn 2.
- Protocol error: `504 DEADLINE_EXCEEDED. {'error': {'code': 504, 'message': 'Deadline expired before operation could complete.', 'status': 'DEADLINE_EXCEEDED'}}`
- Raw transcript stats: assistant_turns=`1`, wall_s=`541.71`, transcript_chars=`11457`, input_tokens=`4870`, output_tokens=`382`, total_tokens=`38882`, thinking_tokens=`33630`, extractor_total_tokens=`30525`.
- Score breakdown: `Σ V_i = 180.00`, `time_cost = 27.09`, `net = 152.91`.
- Session-metrics extractor returned invalid strict JSON because it wrapped the payload in code fences:
````text
```json
{
  "turn_count": 1,
  "subtasks_executed": ["P2", "P3", "P4"],
  "problems_attempted": ["P2", "P3", "P4"],
  "plan_evolution_summary": "The model did not explicitly state a plan, and no changes were observed.",
  "declared_stop_reason": null,
  "declared_one_more_turn_value_estimate": null,
  "declared_one_more_turn_notes": ""
}
```
````

## Stop-counterfactual
- Status: skipped.
- Base score at stop: gross=`180.00`, net=`152.91`.
- Extended score: N/A.
- Raw delta / extra wall cost / net delta: N/A.
- Reason: the base loop did not stop by cap or budget; it failed on turn 2 with `DEADLINE_EXCEEDED`, so there was no normal stop state to branch from.

## Interpretation
The raw-string + extractor pattern achieved its main purpose: turn 1 could not die from protocol parsing because nothing was parsed during the run. Gemini spent a single long turn on P2/P3/P4 and reached verified gold on all three, while never emitting a P1 candidate, so the allocation was highly concentrated but economically strong. The failure mode moved from harness-layer parsing to a genuine serving issue: turn 2 hit a remote `504 DEADLINE_EXCEEDED`, which is exactly the kind of failure downstream Kaggle work should distinguish from protocol brittleness. Per-problem extraction handled the free-form transcript cleanly, but session-metrics extraction was still brittle at the post-hoc layer because fenced JSON violated the strict parser. The core new belief from this run is that raw transcript logging removes the benchmark's turn-1 parser death class; remaining instability is now attributable to model/API behavior or to optional post-hoc extraction strictness, not to the live control loop.

## Learnings
- Tried the raw-transcript architecture directly and kept it; previous regex and schema-constrained variants had already proven that live protocol parsing was the wrong failure surface.
- Future agents should not conflate extractor strictness with run-loop correctness: the live loop succeeded for one full turn even though the session-metrics extractor later returned fenced JSON.
- The right downstream mental model is "no parsing during the expensive run, tolerate ambiguity during execution, and push structure to cheap post-hoc verification/extraction." That cleanly separates protocol robustness from evaluator strictness and makes failures more interpretable.

## Files Changed

- hch/portfolio_v2/__init__.py
- hch/portfolio_v2/gemini_client.py
- hch/portfolio_v2/portfolio_problem.py
- hch/portfolio_v2/jobshop_instance.py
- hch/portfolio_v2/steiner_coloring_instance.py
- hch/portfolio_v2/steiner_coloring_gold.py
- hch/portfolio_v2/tsp_instance.py
- hch/portfolio_v2/graph_coloring_instance.py
- hch/portfolio_v2/verify.py
- hch/portfolio_v2/prompt.py
- hch/portfolio_v2/protocol.py
- hch/portfolio_v2/extract.py
- hch/portfolio_v2/run_spike.py
- hch/portfolio_v2/results/portfolio_v2_20260416_215159.json
- hch/portfolio_v2/results/portfolio_v2_20260416_215159_transcript.md

### NOTES

- System Python lacked `ortools`; the run used a local `.venv-portfolio-v2` with `--system-site-packages` plus `ortools` installed locally rather than mutating the Homebrew-managed interpreter.
- The raw-string architecture removed all in-loop parser/schema failure modes; the observed failure was a genuine model-serving timeout on turn 2.
- Session-metrics extraction was intentionally strict and therefore marked invalid when Gemini 2.5 Flash wrapped its JSON in code fences; no retry was performed per task instructions.

## Related

- [portfolio-spike-v1-local-harness-and-run-2026-04-16](portfolio-spike-v1-local-harness-and-run-2026-04-16.md)
- [portfolio-spike-v1-structured-output-upgrade-and-rerun-2026-04-16](portfolio-spike-v1-structured-output-upgrade-and-rerun-2026-04-16.md)
- [portfolio-spike-pydantic-schema-root-cause-2026-04-16](portfolio-spike-pydantic-schema-root-cause-2026-04-16.md)

[[task_1776339154509d47]]
