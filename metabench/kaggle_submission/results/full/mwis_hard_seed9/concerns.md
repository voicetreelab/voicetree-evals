# Concerns for `mwis_hard_seed9`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=6.51%
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=100.00%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=14.18%

## score-vs-baseline
- `gemini-flash-latest`: score=85.40; baseline_obj=448.0; gold_obj=522.0; final_obj=n/a; wall_s=808.6
- `claude-sonnet-4.6`: score=0.00; baseline_obj=448.0; gold_obj=522.0; final_obj=n/a; wall_s=184.2
- `gpt-5.4-mini`: score=85.69; baseline_obj=448.0; gold_obj=522.0; final_obj=n/a; wall_s=13.0

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 2 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- Add stronger self-checks before stop so invalid solutions are rejected before final answer.
