# Concerns for `portfolio_hard_seed36`

## parse
- `gemini-flash-latest`: `strict_parse_failed`; stop=`error`; error=exec turn 2 parse failed
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`False`; submission_source=`parsed`; gap_pct=n/a
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `gpt-5.4-mini`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a

## score-vs-baseline
- `gemini-flash-latest`: score=-14.54; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=290.8
- `claude-sonnet-4.6`: score=-2.43; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=48.7
- `gpt-5.4-mini`: score=-1.13; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=22.6

## transcript coherence
- `gemini-flash-latest`: transcript exists but protocol parse failed after 1 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- Tighten protocol-label compliance; at least one run produced an unparseable exec turn.
- Add stronger self-checks before stop so invalid assignments are rejected before final answer.
