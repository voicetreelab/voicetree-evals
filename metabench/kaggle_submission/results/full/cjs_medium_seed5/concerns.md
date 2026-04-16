# Concerns for cjs_medium_seed5

## Parse
- gemini-flash-latest: parse_path=strict_protocol_cf; error=-; exec_turns=2
- claude-sonnet-4.6: parse_path=strict_parse_failed; error=exec turn 2 parse failed; exec_turns=1
- gpt-5.4-mini: parse_path=strict_protocol_cf; error=-; exec_turns=1

## Feasibility
- gemini-flash-latest: feasible=True; verified_objective=102; stop_reason=decision_stop
- claude-sonnet-4.6: feasible=False; verified_objective=None; stop_reason=error
- gpt-5.4-mini: feasible=True; verified_objective=164; stop_reason=decision_stop

## Score-vs-baseline
- gemini-flash-latest: score=60.51; gap_pct=34.21052631578947; baseline_objective=164.0; final_submission_source=cf_parsed
- claude-sonnet-4.6: score=-4.91; gap_pct=100.0; baseline_objective=164.0; final_submission_source=parsed
- gpt-5.4-mini: score=-0.19; gap_pct=115.78947368421052; baseline_objective=164.0; final_submission_source=cf_parsed

## Transcript coherence
- gemini-flash-latest: transcript_turns=4; coherent multi-turn transcript
- claude-sonnet-4.6: transcript_turns=2; transcript ended in parse failure
- gpt-5.4-mini: transcript_turns=3; coherent multi-turn transcript

## Suggested fixes
- No additional concerns beyond the bucketed observations above.
