# Concerns for `portfolio_hard_seed1`

## parse
- `gemini-flash-latest`: `aborted_guardrail`; stop=`wall_budget`; error=aborted by parent after gemini-flash-latest exceeded the >500s/row guardrail during portfolio_hard_seed1 before a row payload could be written
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`

## feasibility
- `gemini-flash-latest`: feasible=`False`; submission_source=`baseline`; gap_pct=n/a
- `claude-sonnet-4.6`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a
- `gpt-5.4-mini`: feasible=`False`; submission_source=`cf_parsed`; gap_pct=n/a

## score-vs-baseline
- `gemini-flash-latest`: score=0.00; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=541.0
- `claude-sonnet-4.6`: score=19.39; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=48.7
- `gpt-5.4-mini`: score=-1.24; baseline_obj=0.0; gold_obj=100.0; final_obj=n/a; wall_s=24.8

## transcript coherence
- `gemini-flash-latest`: no transcript captured.
- `claude-sonnet-4.6`: coherent plan/exec flow; stopped after 1 exec turns.
- `gpt-5.4-mini`: coherent plan/exec flow; stopped after 2 exec turns.

## suggested fixes
- Add stronger self-checks before stop so invalid assignments/tours are rejected before final answer.
- Reduce per-turn search breadth or use a faster model; at least one run hit a timeout budget.
