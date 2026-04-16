# Concerns for `ve_hard_seed7`

## parse
- `gemini-flash-latest`: `partial_rescue`; stop=`decision_stop`
- `claude-sonnet-4.6`: `strict_parse_failed`; stop=`error`; error=exec turn 2 parse failed
- `gpt-5.4-mini`: `partial_rescue`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=6.24%
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`parsed`; gap_pct=100.00%
- `gpt-5.4-mini`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=8.78%

## score-vs-baseline
- `gemini-flash-latest`: score=89.96; baseline_obj=0.5; gold_obj=0.5044401986925733; final_obj=0.535900; wall_s=380.2
- `claude-sonnet-4.6`: score=0.00; baseline_obj=0.5; gold_obj=0.5044401986925733; final_obj=n/a; wall_s=376.8
- `gpt-5.4-mini`: score=91.10; baseline_obj=0.5; gold_obj=0.5044401986925733; final_obj=0.548743; wall_s=11.9

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec flow; stopped after 1 exec turns.
- `claude-sonnet-4.6`: transcript exists but protocol parse failed after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- Tighten protocol-label compliance; at least one run produced an unparseable exec turn.
- Add stronger self-checks before stop so invalid solutions are rejected before final answer.
