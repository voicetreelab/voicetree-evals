# Concerns for `graphcol_medium_seed8`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=0.00%
- `claude-sonnet-4.6`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=0.00%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=475.00%

## score-vs-baseline
- `gemini-flash-latest`: score=96.29; baseline_obj=15.0; gold_obj=4.0; final_obj=4.000; wall_s=370.5
- `claude-sonnet-4.6`: score=97.99; baseline_obj=15.0; gold_obj=4.0; final_obj=4.000; wall_s=201.1
- `gpt-5.4-mini`: score=-0.20; baseline_obj=15.0; gold_obj=4.0; final_obj=23.000; wall_s=19.7

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 1 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 2 exec turns.

## suggested fixes
- Solver quality is weak on at least one feasible run; a better local-improvement strategy is needed.
