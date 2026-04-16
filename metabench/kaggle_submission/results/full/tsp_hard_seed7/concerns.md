# Concerns for `tsp_hard_seed7`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=2.48%
- `claude-sonnet-4.6`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=5.29%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=4.85%

## score-vs-baseline
- `gemini-flash-latest`: score=93.38; baseline_obj=495.54467916828713; gold_obj=373.5454706811403; final_obj=382.826310; wall_s=414.0
- `claude-sonnet-4.6`: score=93.90; baseline_obj=495.54467916828713; gold_obj=373.5454706811403; final_obj=393.290609; wall_s=81.1
- `gpt-5.4-mini`: score=95.02; baseline_obj=495.54467916828713; gold_obj=373.5454706811403; final_obj=391.677737; wall_s=12.3

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 1 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 3 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- No urgent fixes from the current sample; rerun only if you need tighter rate estimates.
