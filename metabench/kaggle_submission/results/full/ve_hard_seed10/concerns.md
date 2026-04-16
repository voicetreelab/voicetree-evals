# Concerns for `ve_hard_seed10`

## parse
- `gemini-flash-latest`: `partial_rescue`; stop=`decision_stop`
- `claude-sonnet-4.6`: `partial_rescue`; stop=`error`; error=exec turn 3 parse failed
- `gpt-5.4-mini`: `partial_rescue`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=8.24%
- `claude-sonnet-4.6`: feasible=`True`; submission_source=`parsed`; gap_pct=15.48%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=10.42%

## score-vs-baseline
- `gemini-flash-latest`: score=87.61; baseline_obj=0.5; gold_obj=0.4969414410021404; final_obj=0.456000; wall_s=414.7
- `claude-sonnet-4.6`: score=80.80; baseline_obj=0.5; gold_obj=0.4969414410021404; final_obj=0.420000; wall_s=372.0
- `gpt-5.4-mini`: score=89.43; baseline_obj=0.5; gold_obj=0.4969414410021404; final_obj=0.548732; wall_s=15.3

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 1 exec turns.
- `claude-sonnet-4.6`: transcript ended with stop=`error` after 2 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- No urgent fixes from the current sample; rerun only if you need more stable rate estimates.
