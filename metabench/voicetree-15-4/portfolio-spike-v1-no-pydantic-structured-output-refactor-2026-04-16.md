---
color: green
isContextNode: false
agent_name: Uma
---
# Portfolio spike v1 no-Pydantic structured-output refactor

Replaced the failed Pydantic-based structured-output path with manual Gemini JSON schemas and a stringified candidate payload. The control envelope stays structured (`PLAN`, `NEXT_SUB_ID`, `FORECAST`, `REVISED_PLAN`), while `candidate_answer_json` is decoded downstream and verified by the existing per-problem verifiers.

## What changed
- Removed Pydantic from the Gemini structured-output path entirely.
- Switched the Gemini client to accept manual `response_json_schema` dicts.
- Kept the plan-state envelope structured, but changed the candidate payload to `candidate_answer_json: string`.
- Decoded `candidate_answer_json` with `json.loads()` before calling the existing verifier for the touched problem.

## Why this fixes the prior failure
The April 16, 2026 failure came from the SDK-generated `response_schema` adding unsupported `additional_properties` entries for open-ended object fields. The new path avoids schema generation entirely and avoids open-ended object fields in the response schema.

## Runtime contract now
- Plan turn returns one JSON object with `PLAN` and `NEXT_SUB_ID`.
- Exec turn returns one JSON object with `SUB_N_RESULT`, `candidate_answer_json`, `FORECAST`, `REVISED_PLAN`, and `NEXT_SUB_ID`.
- Verification, value capture, plan deltas, and Brier scoring still use Tara's existing portfolio logic.

## Learnings
1. Tried using Pydantic only as a convenience layer for Gemini structured output; switched to manual JSON schema because the generated schema wire format was the real incompatibility.
2. The pitfall is not structured output itself. The pitfall is feeding Gemini an SDK-expanded schema for open-ended dict/list fields and assuming it will be accepted.
3. The stable mental model is: schema the control state, stringify the artifact payload, decode it locally, then let the verifier own shape validation.

## DIFF

```
diff --git a/hch/portfolio_spike/gemini_client.py b/hch/portfolio_spike/gemini_client.py
@@
-from pydantic import BaseModel
@@
-        *,
-        response_schema: Any | None = None,
-        response_mime_type: str | None = None,
+        *,
+        response_schema: Any | None = None,
+        response_json_schema: Any | None = None,
+        response_mime_type: str | None = None,
@@
-        elif response_mime_type is not None:
+        elif response_json_schema is not None:
+            config_updates["response_json_schema"] = response_json_schema
+            config_updates["response_mime_type"] = response_mime_type or "application/json"
+        elif response_mime_type is not None:
             config_updates["response_mime_type"] = response_mime_type
@@
-        parsed = getattr(response, "parsed", None)
-        if isinstance(parsed, BaseModel):
-            parsed = parsed.model_dump(mode="python", exclude_none=True)
+        parsed = getattr(response, "parsed", None)
```

```
diff --git a/hch/portfolio_spike/protocol.py b/hch/portfolio_spike/protocol.py
@@
-from pydantic import BaseModel, ConfigDict, Field, model_validator
+PROBLEM_IDS = ("P1", "P2", "P3", "P4")
@@
-class ExecTurnOutput(BaseModel):
-    SUB_N_RESULT: str
-    candidate_answer: dict[str, Any] | list[Any]
-    FORECAST: ForecastCDF
-    REVISED_PLAN: list[RevisedPlanItem]
-    NEXT_SUB_ID: int | Literal["stop_economic", "stop_budget"]
+def _parse_candidate_answer_json(raw: Any) -> dict[str, Any] | list[Any] | None:
+    ...
+
+def _plan_turn_json_schema(problem_ids: set[str]) -> dict[str, Any]:
+    ...
+
+def _exec_turn_json_schema(problem_ids: set[str]) -> dict[str, Any]:
+    ...
@@
-    candidate_answer = payload.get("candidate_answer")
+    candidate_answer = _parse_candidate_answer_json(payload.get("candidate_answer_json"))
@@
-        response_schema=PlanTurnOutput,
+        response_json_schema=_plan_turn_json_schema(problem_ids),
@@
-            response_schema=ExecTurnOutput,
+            response_json_schema=_exec_turn_json_schema(problem_ids),
@@
-        f"- candidate_answer must be a full valid JSON answer for {target_problem.problem_id}.\n"
+        f"- candidate_answer_json must be a JSON string whose decoded value is the full valid answer for {target_problem.problem_id}.\n"
```

## Complexity: medium

Moderate protocol refactor: changed the schema transport path, prompt contract, retry call sites, and candidate decoding without disturbing the existing verification/scoring flow.

## Files Changed

- hch/portfolio_spike/gemini_client.py
- hch/portfolio_spike/protocol.py
- hch/portfolio_spike/prompt.py
- hch/portfolio_spike/run_spike.py

### NOTES

- This refactor intentionally kept the rest of Tara's implementation intact: pre-flight gap gate, economic scoring, plan-as-state semantics, and per-problem Brier.
- `run_spike.py` still defaults to `models/gemini-3-pro-preview` for the portfolio spike.

[[task_1776337535298wih]]
