# portfolio_medium_seed5

## Parse
- `gemini-flash-latest`: parse_path=`strict_protocol_cf`; stop_reason=`decision_stop`; turns=1; attempts=1; error=-
- `claude-sonnet-4.6`: parse_path=`strict_protocol_cf`; stop_reason=`decision_stop`; turns=2; attempts=1; error=-
- `gpt-5.4-mini`: parse_path=`strict_protocol_cf`; stop_reason=`decision_stop`; turns=1; attempts=1; error=-

## Feasibility
- `gemini-flash-latest`: feasible=False; failures=tsp_medium_seed5: tour must contain exactly 20 cities
- `claude-sonnet-4.6`: feasible=False; failures=tsp_medium_seed5: tour must contain exactly 20 cities
- `gpt-5.4-mini`: feasible=False; failures=tsp_medium_seed5: submission must provide tour as a list of city indices

## Score vs Baseline
- baseline_objective=0.0; gold_objective=100.0
- `gemini-flash-latest`: score=5.798483044876928; gap_pct=n/a; component_gaps=cjs_medium_seed5=115.79%, steiner_medium_seed5=46.55%, tsp_medium_seed5=100.00%
- `claude-sonnet-4.6`: score=23.15700085140034; gap_pct=n/a; component_gaps=cjs_medium_seed5=115.79%, steiner_medium_seed5=20.69%, tsp_medium_seed5=100.00%
- `gpt-5.4-mini`: score=25.356836218097857; gap_pct=n/a; component_gaps=cjs_medium_seed5=115.79%, steiner_medium_seed5=20.69%, tsp_medium_seed5=100.00%

## Transcript Coherence
- `gemini-flash-latest`: transcript_entries=3; wall_s=236.8s; stop_reason=`decision_stop`
- `claude-sonnet-4.6`: transcript_entries=4; wall_s=60.3s; stop_reason=`decision_stop`
- `gpt-5.4-mini`: transcript_entries=3; wall_s=16.3s; stop_reason=`decision_stop`

## Suggested Fixes
- Add stronger contract/schema reminders for sub-problem answers inside the portfolio response.
