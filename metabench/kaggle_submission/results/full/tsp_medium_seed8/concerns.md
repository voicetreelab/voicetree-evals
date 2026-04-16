# Concerns for `tsp_medium_seed8`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=0.00%
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=100.00%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=14.23%

## score-vs-baseline
- `gemini-flash-latest`: score=94.26; baseline_obj=481.17297652228615; gold_obj=411.72592378747373; final_obj=411.726; wall_s=574.3
- `claude-sonnet-4.6`: score=0.00; baseline_obj=481.17297652228615; gold_obj=411.72592378747373; final_obj=n/a; wall_s=94.9
- `gpt-5.4-mini`: score=85.61; baseline_obj=481.17297652228615; gold_obj=411.72592378747373; final_obj=470.304; wall_s=15.9

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 2 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 4 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 2 exec turns.

## suggested fixes
- Add stronger self-checks before stop so invalid assignments/tours are rejected before final answer.
