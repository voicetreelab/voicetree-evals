# Concerns for `tsp_medium_seed5`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=0.00%
- `claude-sonnet-4.6`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=6.39%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=17.85%

## score-vs-baseline
- `gemini-flash-latest`: score=93.04; baseline_obj=554.4458562721104; gold_obj=426.2791525386463; final_obj=426.279; wall_s=695.6
- `claude-sonnet-4.6`: score=92.92; baseline_obj=554.4458562721104; gold_obj=426.2791525386463; final_obj=453.501; wall_s=69.4
- `gpt-5.4-mini`: score=82.03; baseline_obj=554.4458562721104; gold_obj=426.2791525386463; final_obj=502.382; wall_s=11.8

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 3 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 2 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- No urgent fixes from the current sample; rerun only if you need more stable rate estimates.
