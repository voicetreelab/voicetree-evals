# Concerns — ve_medium_seed8

## Parse
- `gemini-flash-latest`: parse_path=`not_run`; n_exec_turns=0; error=skipped after ve_medium_seed5 because repeating this model's observed row-1 wall time (417.9s) across the remaining rows would blow past the worker's 15-20 minute budget
- `claude-sonnet-4.6`: parse_path=`not_run`; n_exec_turns=0; error=skipped after ve_medium_seed5 because repeating this model's observed row-1 wall time (367.2s) across the remaining rows would blow past the worker's 15-20 minute budget
- `gpt-5.4-mini`: parse_path=`partial_rescue`; n_exec_turns=4; error=-

## Feasibility
- `gemini-flash-latest`: feasible=False; reason=skipped after ve_medium_seed5 because repeating this model's observed row-1 wall time (417.9s) across the remaining rows would blow past the worker's 15-20 minute budget
- `claude-sonnet-4.6`: feasible=False; reason=skipped after ve_medium_seed5 because repeating this model's observed row-1 wall time (367.2s) across the remaining rows would blow past the worker's 15-20 minute budget
- `gpt-5.4-mini`: feasible=True; reason=-

## Score vs Baseline
- `gemini-flash-latest`: score=-; gap_pct=-; baseline_objective=0.50
- `claude-sonnet-4.6`: score=-; gap_pct=-; baseline_objective=0.50
- `gpt-5.4-mini`: score=96.23; gap_pct=3.51; baseline_objective=0.50

## Transcript Coherence
- `gemini-flash-latest`: transcript_len=0; stop_reason=model_skipped_by_parent_budget_guardrail; final_submission_source=-
- `claude-sonnet-4.6`: transcript_len=0; stop_reason=model_skipped_by_parent_budget_guardrail; final_submission_source=-
- `gpt-5.4-mini`: transcript_len=6; stop_reason=decision_stop; final_submission_source=cf_parsed

## Suggested Fixes
- Prompt contract is still brittle on at least one model; inspect label emission and NEXT_SUB control fields.
- At least one model ended infeasible or skipped; inspect the final submission against the verifier-specific failure reason.
