# Concerns for `portfolio_hard_seed9`

## parse
- `gemini-flash-latest`: `not_run`; stop=`not_run`; error=skipped after gemini-flash-latest exceeded the >500s/row guardrail on portfolio_hard_seed1
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`False`; submission_source=`baseline`; gap_pct=n/a
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `gpt-5.4-mini`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a

## score-vs-baseline
- `gemini-flash-latest`: score=0.00; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=0.0
- `claude-sonnet-4.6`: score=-1.50; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=30.0
- `gpt-5.4-mini`: score=-0.47; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=9.4

## transcript coherence
- `gemini-flash-latest`: no transcript captured.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- Add stronger self-checks before stop so invalid assignments/tours are rejected before final answer.
