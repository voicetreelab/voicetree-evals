# Concerns for `portfolio_medium_seed14`

## parse
- `gemini-flash-latest`: `partial_rescue`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `gpt-5.4-mini`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a

## score-vs-baseline
- `gemini-flash-latest`: score=-11.03; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=220.5
- `claude-sonnet-4.6`: score=11.72; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=46.4
- `gpt-5.4-mini`: score=13.25; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=15.8

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 1 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- Add stronger self-checks before stop so invalid portfolio components are rejected before final answer.
