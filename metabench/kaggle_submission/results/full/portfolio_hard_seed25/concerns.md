# Concerns for `portfolio_hard_seed25`

## parse
- `gemini-flash-latest`: `partial_rescue`; stop=`error`; error=exec turn 2 parse failed
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`False`; submission_source=`parsed`; gap_pct=n/a
- `claude-sonnet-4.6`: feasible=`True`; submission_source=`cf_parsed`; gap_pct=n/a
- `gpt-5.4-mini`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a

## score-vs-baseline
- `gemini-flash-latest`: score=-7.77; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=155.3
- `claude-sonnet-4.6`: score=3.85; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=56.4
- `gpt-5.4-mini`: score=5.66; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=20.2

## transcript coherence
- `gemini-flash-latest`: transcript ended with stop=`error` after 1 exec turns.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 1 exec turns.

## suggested fixes
- Add stronger self-checks before stop so invalid assignments/tours are rejected before final answer.
- Solver quality is weak on at least one feasible run; a better local-improvement strategy is needed.
