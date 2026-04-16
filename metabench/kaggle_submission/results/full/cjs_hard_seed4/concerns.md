# Concerns — cjs_hard_seed4

## Parse
- `gemini-flash-latest`: parse_path=`not_run`; n_exec_turns=0; error=skipped after ve_medium_seed5 because repeating this model's observed row-1 wall time (417.9s) across the remaining rows would blow past the worker's 15-20 minute budget
- `claude-sonnet-4.6`: parse_path=`not_run`; n_exec_turns=0; error=skipped after ve_medium_seed5 because repeating this model's observed row-1 wall time (367.2s) across the remaining rows would blow past the worker's 15-20 minute budget
- `gpt-5.4-mini`: parse_path=`strict_protocol_cf`; n_exec_turns=1; error=-

## Feasibility
- `gemini-flash-latest`: feasible=False; reason=skipped after ve_medium_seed5 because repeating this model's observed row-1 wall time (417.9s) across the remaining rows would blow past the worker's 15-20 minute budget
- `claude-sonnet-4.6`: feasible=False; reason=skipped after ve_medium_seed5 because repeating this model's observed row-1 wall time (367.2s) across the remaining rows would blow past the worker's 15-20 minute budget
- `gpt-5.4-mini`: feasible=True; reason=-

## Score vs Baseline
- `gemini-flash-latest`: score=-; gap_pct=-; baseline_objective=197.00
- `claude-sonnet-4.6`: score=-; gap_pct=-; baseline_objective=197.00
- `gpt-5.4-mini`: score=-0.18; gap_pct=123.86; baseline_objective=197.00

## Transcript Coherence
- `gemini-flash-latest`: transcript_len=0; stop_reason=model_skipped_by_parent_budget_guardrail; final_submission_source=-
- `claude-sonnet-4.6`: transcript_len=0; stop_reason=model_skipped_by_parent_budget_guardrail; final_submission_source=-
- `gpt-5.4-mini`: transcript_len=3; stop_reason=decision_stop; final_submission_source=cf_parsed

## Suggested Fixes
- Prompt contract is still brittle on at least one model; inspect label emission and NEXT_SUB control fields.
- At least one model ended infeasible or skipped; inspect the final submission against the verifier-specific failure reason.
- One or more models failed to capture useful headroom; compare transcript decisions against the baseline and gold gap.
