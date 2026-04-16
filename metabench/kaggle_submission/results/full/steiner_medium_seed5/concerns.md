# steiner_medium_seed5 concerns

## Parse
- gemini-flash-latest: parse_path=strict_protocol_cf, stop_reason=decision_stop, error=-
- claude-sonnet-4.6: parse_path=strict_protocol_cf, stop_reason=decision_stop, error=-
- gpt-5.4-mini: parse_path=strict_protocol_cf, stop_reason=decision_stop, error=-

## Feasibility
- gemini-flash-latest: feasible=True, submission_source=cf_parsed, failure_reason=-
- claude-sonnet-4.6: feasible=True, submission_source=cf_parsed, failure_reason=-
- gpt-5.4-mini: feasible=False, submission_source=cf_parsed, failure_reason=chosen cable links do not form a tree on the active villages

## Score-vs-baseline
- gemini-flash-latest: score=96.1164, gap_pct=0.0, baseline=70.0, gold=58.0, wall_s=388.4
- claude-sonnet-4.6: score=93.9696, gap_pct=5.172413793103448, baseline=70.0, gold=58.0, wall_s=85.8
- gpt-5.4-mini: score=0.0000, gap_pct=20.689655172413794, baseline=70.0, gold=58.0, wall_s=12.9

## Transcript Coherence
- gemini-flash-latest: assistant_turns=3, markers=BEST_GUESS,UPDATED_PLAN_STATE,QUALITY_FORECAST,CONTINUE_FORECAST,DECISION
- claude-sonnet-4.6: assistant_turns=3, markers=BEST_GUESS,UPDATED_PLAN_STATE,QUALITY_FORECAST,CONTINUE_FORECAST,DECISION
- gpt-5.4-mini: assistant_turns=3, markers=BEST_GUESS,UPDATED_PLAN_STATE,QUALITY_FORECAST,CONTINUE_FORECAST,DECISION

## Suggested Fixes
- gemini-flash-latest: No immediate fix suggested; output is structurally usable.
- claude-sonnet-4.6: No immediate fix suggested; output is structurally usable.
- gpt-5.4-mini: Verifier rejected the final submission; inspect normalized submission and failure_reason.
