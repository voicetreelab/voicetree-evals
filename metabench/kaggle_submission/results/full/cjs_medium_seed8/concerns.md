# Concerns for cjs_medium_seed8

## Parse
- gemini-flash-latest: parse_path=strict_protocol_cf; error=-; exec_turns=2
- claude-sonnet-4.6: parse_path=baseline_only; error=exec turn 2 timed out after 400s; exec_turns=1
- gpt-5.4-mini: parse_path=strict_protocol_cf; error=-; exec_turns=1

## Feasibility
- gemini-flash-latest: feasible=True; verified_objective=80; stop_reason=decision_stop
- claude-sonnet-4.6: feasible=True; verified_objective=157; stop_reason=wall_budget
- gpt-5.4-mini: feasible=True; verified_objective=157; stop_reason=decision_stop

## Score-vs-baseline
- gemini-flash-latest: score=90.12; gap_pct=3.896103896103896; baseline_objective=157.0; final_submission_source=cf_parsed
- claude-sonnet-4.6: score=-4.23; gap_pct=103.8961038961039; baseline_objective=157.0; final_submission_source=baseline
- gpt-5.4-mini: score=-0.16; gap_pct=103.8961038961039; baseline_objective=157.0; final_submission_source=cf_parsed

## Transcript coherence
- gemini-flash-latest: transcript_turns=4; coherent multi-turn transcript
- claude-sonnet-4.6: transcript_turns=1; transcript ended in timeout
- gpt-5.4-mini: transcript_turns=3; coherent multi-turn transcript

## Suggested fixes
- No additional concerns beyond the bucketed observations above.
