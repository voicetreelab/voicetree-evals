# Concerns for `tsp_hard_seed10`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=0.00%
- `claude-sonnet-4.6`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=6.51%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=22.05%

## score-vs-baseline
- `gemini-flash-latest`: score=94.57; baseline_obj=589.6582259632314; gold_obj=442.8740545630947; final_obj=442.874055; wall_s=543.1
- `claude-sonnet-4.6`: score=92.68; baseline_obj=589.6582259632314; gold_obj=442.8740545630947; final_obj=471.722150; wall_s=80.5
- `gpt-5.4-mini`: score=77.84; baseline_obj=589.6582259632314; gold_obj=442.8740545630947; final_obj=540.507206; wall_s=11.9

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 2 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 3 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- No urgent fixes from the current sample; rerun only if you need tighter rate estimates.
