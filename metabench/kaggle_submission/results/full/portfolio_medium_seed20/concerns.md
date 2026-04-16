# Concerns for `portfolio_medium_seed20`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `gpt-5.4-mini`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a

## score-vs-baseline
- `gemini-flash-latest`: score=-19.33; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=386.6
- `claude-sonnet-4.6`: score=20.80; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=29.1
- `gpt-5.4-mini`: score=-0.46; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=9.3

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 2 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- Add stronger self-checks before stop so invalid assignments/tours are rejected before final answer.
