# Concerns for `portfolio_medium_seed36`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `gpt-5.4-mini`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a

## score-vs-baseline
- `gemini-flash-latest`: score=-26.79; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=535.9
- `claude-sonnet-4.6`: score=2.16; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=71.9
- `gpt-5.4-mini`: score=4.91; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=16.8

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 2 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 2 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- Add stronger self-checks before stop so invalid assignments/tours are rejected before final answer.
