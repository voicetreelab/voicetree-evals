# Concerns for `tsp_medium_seed2`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=0.80%
- `claude-sonnet-4.6`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=0.66%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=35.15%

## score-vs-baseline
- `gemini-flash-latest`: score=94.09; baseline_obj=447.8919893619096; gold_obj=387.4143294552208; final_obj=390.517; wall_s=510.7
- `claude-sonnet-4.6`: score=96.23; baseline_obj=447.8919893619096; gold_obj=387.4143294552208; final_obj=389.977; wall_s=310.8
- `gpt-5.4-mini`: score=64.74; baseline_obj=447.8919893619096; gold_obj=387.4143294552208; final_obj=523.591; wall_s=11.1

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 2 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- No urgent fixes from the current sample; rerun only if you need more stable rate estimates.
