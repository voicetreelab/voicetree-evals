# Concerns — cjs_hard_seed7

## Parse
- `gemini-flash-latest`: parse_path=`partial_rescue`; n_exec_turns=1; error=exec turn 2 parse failed
- `claude-sonnet-4.6`: parse_path=`strict_parse_failed`; n_exec_turns=1; error=exec turn 2 parse failed
- `gpt-5.4-mini`: parse_path=`strict_protocol_cf`; n_exec_turns=1; error=-

## Feasibility
- `gemini-flash-latest`: feasible=False; reason=factory A precedence failed for J1: MA6 starts at 40 before predecessor finished at 48
- `claude-sonnet-4.6`: feasible=False; reason=schedule must be an object
- `gpt-5.4-mini`: feasible=True; reason=-

## Score vs Baseline
- `gemini-flash-latest`: score=0.00; gap_pct=100.00; baseline_objective=211.00
- `claude-sonnet-4.6`: score=-3.86; gap_pct=100.00; baseline_objective=211.00
- `gpt-5.4-mini`: score=-0.22; gap_pct=126.88; baseline_objective=211.00

## Transcript Coherence
- `gemini-flash-latest`: transcript_len=2; stop_reason=error; final_submission_source=parsed
- `claude-sonnet-4.6`: transcript_len=2; stop_reason=error; final_submission_source=parsed
- `gpt-5.4-mini`: transcript_len=3; stop_reason=decision_stop; final_submission_source=cf_parsed

## Suggested Fixes
- Prompt contract is still brittle on at least one model; inspect label emission and NEXT_SUB control fields.
- At least one model ended infeasible or skipped; inspect the final submission against the verifier-specific failure reason.
- One or more models failed to capture useful headroom; compare transcript decisions against the baseline and gold gap.
