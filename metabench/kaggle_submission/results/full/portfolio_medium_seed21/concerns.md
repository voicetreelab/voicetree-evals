# Concerns for `portfolio_medium_seed21`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `gpt-5.4-mini`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a

## score-vs-baseline
- `gemini-flash-latest`: score=-27.70; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=554.0
- `claude-sonnet-4.6`: score=14.86; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=32.8
- `gpt-5.4-mini`: score=15.99; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=10.2

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 3 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- Add stronger self-checks before stop so invalid portfolio components are rejected before final answer.
