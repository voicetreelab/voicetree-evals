# Concerns for `mwis_hard_seed13`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_parse_failed`; stop=`error`; error=exec turn 2 parse failed
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=17.06%
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`baseline`; gap_pct=100.00%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=19.16%

## score-vs-baseline
- `gemini-flash-latest`: score=77.27; baseline_obj=308.0; gold_obj=381.0; final_obj=n/a; wall_s=566.8
- `claude-sonnet-4.6`: score=0.00; baseline_obj=308.0; gold_obj=381.0; final_obj=n/a; wall_s=302.1
- `gpt-5.4-mini`: score=80.71; baseline_obj=308.0; gold_obj=381.0; final_obj=n/a; wall_s=13.2

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 2 exec turns.
- `claude-sonnet-4.6`: transcript exists but protocol parse failed after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- Tighten protocol-label compliance; at least one run produced an unparseable exec turn.
- Add stronger self-checks before stop so invalid solutions are rejected before final answer.
