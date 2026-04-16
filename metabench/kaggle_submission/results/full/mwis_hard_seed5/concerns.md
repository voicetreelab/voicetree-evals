# Concerns for `mwis_hard_seed5`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_parse_failed`; stop=`error`; error=exec turn 2 parse failed
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=18.82%
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`parsed`; gap_pct=100.00%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=28.34%

## score-vs-baseline
- `gemini-flash-latest`: score=75.76; baseline_obj=316.0; gold_obj=441.0; final_obj=n/a; wall_s=542.4
- `claude-sonnet-4.6`: score=0.00; baseline_obj=316.0; gold_obj=441.0; final_obj=n/a; wall_s=375.4
- `gpt-5.4-mini`: score=71.47; baseline_obj=316.0; gold_obj=441.0; final_obj=n/a; wall_s=18.7

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 1 exec turns.
- `claude-sonnet-4.6`: transcript exists but protocol parse failed after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 2 exec turns.

## suggested fixes
- Tighten protocol-label compliance; at least one run produced an unparseable exec turn.
- Add stronger self-checks before stop so invalid solutions are rejected before final answer.
