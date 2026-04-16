# Concerns for `portfolio_hard_seed24`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `gpt-5.4-mini`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a

## score-vs-baseline
- `gemini-flash-latest`: score=-4.58; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=494.6
- `claude-sonnet-4.6`: score=18.18; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=39.3
- `gpt-5.4-mini`: score=-0.47; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=9.3

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 3 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 2 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- Add stronger self-checks before stop so invalid assignments/tours are rejected before final answer.
