---
color: green
isContextNode: false
agent_name: Uma
---
# Portfolio spike Pydantic schema root cause

Documented why the structured-output rerun failed before turn 1: Pydantic was introduced only as a convenience to generate Gemini response schemas, but dict-shaped fields in the generated schema expanded to unsupported `additional_properties` keys. The remedy is to avoid Pydantic for this response schema path and use a manual Gemini-compatible JSON schema or narrower payload types.

## What happened
The old harness did not use Pydantic. It used plain text plus regex parsing.

I introduced Pydantic only as a fast way to define Gemini `response_schema` objects for structured output. The SDK accepts BaseModel classes and derives JSON schema from them.

That convenience is what failed here.

## Actual failure mode
The plan/exec request never reached model reasoning. Gemini rejected the request payload itself with `400 INVALID_ARGUMENT` because the SDK-generated schema included unsupported `additional_properties` fields.

The trigger was the permissive raw-JSON field shape, especially `candidate_answer: dict[str, Any] | list[Any]`. That kind of open-ended structure is exactly where schema generators tend to emit `additionalProperties`.

## Why it feels confusing
There were two separate changes bundled together:
1. Switch from regex-parsed text to structured output.
2. Use Pydantic to define the structured-output schema.

Only the second one was optional. Structured output is still viable; the Pydantic-generated schema was the problematic implementation detail.

## What prevents this next time
Use one of these instead:
- Manual Gemini-compatible JSON schema dict for just the control envelope.
- `candidate_answer` as a string field, then `json.loads()` downstream before verification.
- Narrower typed candidate payloads per problem, if we really want structured candidate objects.

The simplest robust next move is:
- Keep `PLAN`, `NEXT_SUB_ID`, `FORECAST`, `REVISED_PLAN` structured.
- Make `candidate_answer_json` a string.
- Parse that string in Python and pass it into the existing verifiers.

This avoids open-ended object schemas entirely, which is what triggered the API rejection.

## Learnings
- Do not conflate "use structured output" with "use Pydantic models". The former is the product requirement; the latter was just one implementation shortcut.
- The risky part is schema wire format compatibility, not the benchmark design.
- For Gemini response schemas, open-ended dict/list fields are exactly where generated schemas can become incompatible even when the SDK nominally supports structured output.

## Related

- [portfolio-spike-v1-structured-output-upgrade-and-rerun-2026-04-16](portfolio-spike-v1-structured-output-upgrade-and-rerun-2026-04-16.md)
- [portfolio-spike-structured-output-simplification-decision-2026-04-16](portfolio-spike-structured-output-simplification-decision-2026-04-16.md)

[[task_1776337535298wih]]
