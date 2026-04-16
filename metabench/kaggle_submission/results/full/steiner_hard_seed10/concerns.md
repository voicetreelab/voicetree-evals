# Concerns — steiner_hard_seed10

## Parse
- `gemini-flash-latest`: parse_path=`strict_protocol_cf`; n_exec_turns=1; error=-
- `claude-sonnet-4.6`: parse_path=`strict_protocol_cf`; n_exec_turns=2; error=-
- `gpt-5.4-mini`: parse_path=`strict_protocol_cf`; n_exec_turns=1; error=-

## Feasibility
- `gemini-flash-latest`: feasible=True; reason=-
- `claude-sonnet-4.6`: feasible=True; reason=-
- `gpt-5.4-mini`: feasible=True; reason=-

## Score vs Baseline
- `gemini-flash-latest`: score=95.97; gap_pct=0.00; baseline_objective=86.00
- `claude-sonnet-4.6`: score=99.19; gap_pct=0.00; baseline_objective=86.00
- `gpt-5.4-mini`: score=75.26; gap_pct=24.64; baseline_objective=86.00

## Transcript Coherence
- `gemini-flash-latest`: transcript_len=3; stop_reason=decision_stop; final_submission_source=cf_parsed
- `claude-sonnet-4.6`: transcript_len=4; stop_reason=decision_stop; final_submission_source=cf_parsed
- `gpt-5.4-mini`: transcript_len=3; stop_reason=decision_stop; final_submission_source=cf_parsed

## Suggested Fixes
- None.
