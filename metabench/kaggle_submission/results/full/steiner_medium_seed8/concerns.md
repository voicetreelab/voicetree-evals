# steiner_medium_seed8 concerns

## Parse
- gemini-flash-latest: parse_path=strict_protocol_cf, stop_reason=decision_stop, error=-
- claude-sonnet-4.6: parse_path=strict_protocol_cf, stop_reason=decision_stop, error=-
- gpt-5.4-mini: parse_path=strict_protocol_cf, stop_reason=decision_stop, error=-

## Feasibility
- gemini-flash-latest: feasible=True, submission_source=cf_parsed, failure_reason=-
- claude-sonnet-4.6: feasible=True, submission_source=cf_parsed, failure_reason=-
- gpt-5.4-mini: feasible=True, submission_source=cf_parsed, failure_reason=-

## Score-vs-baseline
- gemini-flash-latest: score=96.1617, gap_pct=0.0, baseline=64.0, gold=53.0, wall_s=383.8
- claude-sonnet-4.6: score=99.3023, gap_pct=0.0, baseline=64.0, gold=53.0, wall_s=69.8
- gpt-5.4-mini: score=79.1360, gap_pct=20.754716981132077, baseline=64.0, gold=53.0, wall_s=10.9

## Transcript Coherence
- gemini-flash-latest: assistant_turns=3, markers=BEST_GUESS,UPDATED_PLAN_STATE,QUALITY_FORECAST,CONTINUE_FORECAST,DECISION
- claude-sonnet-4.6: assistant_turns=3, markers=BEST_GUESS,UPDATED_PLAN_STATE,QUALITY_FORECAST,CONTINUE_FORECAST,DECISION
- gpt-5.4-mini: assistant_turns=3, markers=BEST_GUESS,UPDATED_PLAN_STATE,QUALITY_FORECAST,CONTINUE_FORECAST,DECISION

## Suggested Fixes
- gemini-flash-latest: No immediate fix suggested; output is structurally usable.
- claude-sonnet-4.6: No immediate fix suggested; output is structurally usable.
- gpt-5.4-mini: No immediate fix suggested; output is structurally usable.
