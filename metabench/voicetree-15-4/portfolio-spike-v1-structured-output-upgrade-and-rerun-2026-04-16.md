---
color: green
isContextNode: false
agent_name: Uma
---
# Portfolio spike v1 structured-output upgrade and rerun

Replaced the portfolio spike's regex label-block protocol with Gemini structured-output schemas for plan/exec control state, kept candidate answers as permissive raw JSON, and executed the single allowed rerun on April 16, 2026. The rerun failed before turn 1 with a Gemini API 400 because the SDK-generated response schema included unsupported `additional_properties` fields, so no model output or result JSON was produced.

## Protocol Diff Summary
- Added per-call `response_schema` support to `GeminiChatSession.send()` and surfaced SDK-parsed JSON alongside raw text.
- Replaced the regex label-block parser in `protocol.py` with Pydantic schemas for `PLAN`, `NEXT_SUB_ID`, `FORECAST`, and `REVISED_PLAN`.
- Kept `candidate_answer` permissive as raw JSON (`dict | list`) and continued downstream verification through the existing per-problem `verify_*` functions.
- Switched prompts from label-block instructions to strict JSON-object instructions and set the run default to `models/gemini-3-pro-preview`.

## Pre-flight Gap Table
| id | problem | baseline | gold | gap_pct | gold_method | gold_s |
|---|---|---:|---:|---:|---|---:|
| P1 | Coupled jobshop 5x6 | 155 | 90 | 72.22 | CP-SAT exact schedule | 0.01 |
| P2 | Steiner x coloring N=8 K=4 | 72 | 59 | 22.03 | Exact joint enumeration | 0.94 |
| P3 | Euclidean TSP-20 | 588.221 | 470.146 | 25.11 | CP-SAT exact circuit | 0.02 |
| P4 | Slack graph coloring 30 nodes | 20 | 4 | 400.00 | CP-SAT exact min-conflict coloring | 0.02 |

## Per-problem Result Table
| id | baseline | gold | model_final | value_captured | subtasks_executed |
|---|---:|---:|---:|---:|---:|
| P1 | 155 | 90 | 155 | 0.00 | 0 |
| P2 | 72 | 59 | 72 | 0.00 | 0 |
| P3 | 588.221 | 470.146 | 588.221 | 0.00 | 0 |
| P4 | 20 | 4 | 20 | 0.00 | 0 |

These stayed at baseline because the API rejected the plan-turn schema before Gemini returned any model output.

## Plan Evolution Trace
| turn | phase | plan_size | additions | revisions | status_flips | per-turn wall | cumulative wall | note |
|---|---|---:|---|---|---|---:|---:|---|
| 1 | plan_request | N/A | N/A | N/A | N/A | N/A | N/A | Gemini API rejected the generated `response_schema` before any turn-1 plan was produced |

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
| cost | N/A |
| net | N/A |
| stop_reason | api_schema_invalid_argument_pre_turn1 |
| wall_time_s | N/A |
| turn1_wall_s | N/A |

No result JSON was written because `run_protocol()` raised before returning.

## Last API Error
```text
google.genai.errors.ClientError: 400 INVALID_ARGUMENT. {
  'error': {
    'code': 400,
    'message': 'Invalid JSON payload received. Unknown name "additional_properties" at \'generation_config.response_schema\': Cannot find field.\nInvalid JSON payload received. Unknown name "additional_properties" at \'generation_config.response_schema.properties[0].value.items\': Cannot find field.',
    'status': 'INVALID_ARGUMENT'
  }
}
```

## Interpretation
Structured output was the right architectural direction, and the harness-side regex parser is now fully gone from the portfolio protocol. The failure mode moved from post-generation parsing fragility to request-construction fragility: Gemini never got to answer because the SDK-expanded schema for dict-shaped fields serialized unsupported `additional_properties` keys. That means this rerun did not test multi-subtask behavior, plan revision, calibration, or economic stopping; it failed strictly at request validation. The permissive `candidate_answer` choice was not itself the conceptual problem, but its schema representation through the current SDK/Pydantic path was incompatible with this API surface. The benchmark remains viable at the problem/scoring level, but the structured-output path needs a schema encoding that Gemini accepts before Otto should inherit it for Kaggle.

## Learnings
1. Tried the lighter structured-output design with Pydantic models for the control envelope and raw JSON for `candidate_answer`; changed course only insofar as the single live run showed the SDK-generated schema is not accepted by Gemini because it emits unsupported `additional_properties` fields.
2. A future agent will likely assume that "structured output supported by the SDK" implies any Pydantic model is safe to send. Do not assume that here: dict-shaped fields in the generated schema can produce request-level 400s before the model ever answers.
3. The key mental model now is: the portfolio harness is no longer blocked by label parsing, but the next unblocker is schema wire-format compatibility, not benchmark design. The clean path forward is likely a Gemini-compatible manual JSON schema or narrower typed candidate payloads, followed by one fresh rerun in a new task rather than patching this run retroactively.

## Files Changed

- hch/portfolio_spike/gemini_client.py
- hch/portfolio_spike/protocol.py
- hch/portfolio_spike/prompt.py
- hch/portfolio_spike/run_spike.py

### NOTES

- Single-run constraint respected: after the API-level failure, I did not patch and rerun.
- The failure happened before any model output, so the raw diagnostic artifact is the API error body rather than a malformed model response.
- Result file `hch/portfolio_spike/results/portfolio_spike_structured_seed1_20260416.json` was not created because the runner raised before writing output.

## Related

- [task_1776337535298wih](task_1776337535298wih.md)
- [portfolio-spike-v1-local-harness-and-run-2026-04-16](portfolio-spike-v1-local-harness-and-run-2026-04-16.md)
- [portfolio-spike-structured-output-simplification-decision-2026-04-16](portfolio-spike-structured-output-simplification-decision-2026-04-16.md)

[[task_1776337535298wih]]
