# Concerns for `graphcol_hard_seed4`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=0.00%
- `claude-sonnet-4.6`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=0.00%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=300.00%

## score-vs-baseline
- `gemini-flash-latest`: score=94.96; baseline_obj=16.0; gold_obj=4.0; final_obj=4.000; wall_s=504.5
- `claude-sonnet-4.6`: score=97.85; baseline_obj=16.0; gold_obj=4.0; final_obj=4.000; wall_s=214.7
- `gpt-5.4-mini`: score=-0.18; baseline_obj=16.0; gold_obj=4.0; final_obj=16.000; wall_s=17.9

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 2 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 2 exec turns.

## suggested fixes
- Solver quality is weak on at least one feasible run; a better local-improvement strategy is needed.
