# graphcol_medium_seed2 concerns

## Parse
- gemini-flash-latest: parse_path=strict_protocol_cf, stop_reason=decision_stop, error=-
- claude-sonnet-4.6: parse_path=strict_protocol_cf, stop_reason=decision_stop, error=-
- gpt-5.4-mini: parse_path=strict_protocol_cf, stop_reason=decision_stop, error=-

## Feasibility
- gemini-flash-latest: feasible=True, submission_source=cf_parsed, failure_reason=-
- claude-sonnet-4.6: feasible=True, submission_source=cf_parsed, failure_reason=-
- gpt-5.4-mini: feasible=True, submission_source=cf_parsed, failure_reason=-

## Score-vs-baseline
- gemini-flash-latest: score=96.7340, gap_pct=0.0, baseline=17.0, gold=4.0, wall_s=326.6
- claude-sonnet-4.6: score=98.0628, gap_pct=0.0, baseline=17.0, gold=4.0, wall_s=193.7
- gpt-5.4-mini: score=-0.1530, gap_pct=575.0, baseline=17.0, gold=4.0, wall_s=15.3

## Transcript Coherence
- gemini-flash-latest: assistant_turns=3, markers=BEST_GUESS,UPDATED_PLAN_STATE,QUALITY_FORECAST,CONTINUE_FORECAST,DECISION
- claude-sonnet-4.6: assistant_turns=3, markers=BEST_GUESS,UPDATED_PLAN_STATE,QUALITY_FORECAST,CONTINUE_FORECAST,DECISION
- gpt-5.4-mini: assistant_turns=3, markers=BEST_GUESS,UPDATED_PLAN_STATE,QUALITY_FORECAST,CONTINUE_FORECAST,DECISION

## Suggested Fixes
- gemini-flash-latest: No immediate fix suggested; output is structurally usable.
- claude-sonnet-4.6: No immediate fix suggested; output is structurally usable.
- gpt-5.4-mini: Run was feasible but economically weak; compare against baseline and consider prompt/horizon changes.
