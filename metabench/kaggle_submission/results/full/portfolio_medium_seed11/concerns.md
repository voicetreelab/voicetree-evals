# portfolio_medium_seed11

## Parse
- `gemini-flash-latest`: parse_path=`strict_protocol_cf`; stop_reason=`decision_stop`; turns=1; attempts=1; error=-
- `claude-sonnet-4.6`: parse_path=`strict_protocol_cf`; stop_reason=`decision_stop`; turns=1; attempts=1; error=-
- `gpt-5.4-mini`: parse_path=`strict_protocol_cf`; stop_reason=`decision_stop`; turns=1; attempts=1; error=-

## Feasibility
- `gemini-flash-latest`: feasible=False; failures=steiner_medium_seed11: interference violation between Cape and Port; tsp_medium_seed11: tour must contain exactly 20 cities
- `claude-sonnet-4.6`: feasible=False; failures=tsp_medium_seed11: tour must contain exactly 20 cities
- `gpt-5.4-mini`: feasible=False; failures=tsp_medium_seed11: submission must provide tour as a list of city indices

## Score vs Baseline
- baseline_objective=0.0; gold_objective=100.0
- `gemini-flash-latest`: score=-9.4541372642869; gap_pct=n/a; component_gaps=cjs_medium_seed11=96.10%, steiner_medium_seed11=22.41%, tsp_medium_seed11=100.00%
- `claude-sonnet-4.6`: score=24.78922595742578; gap_pct=n/a; component_gaps=cjs_medium_seed11=96.10%, steiner_medium_seed11=22.41%, tsp_medium_seed11=100.00%
- `gpt-5.4-mini`: score=26.142143461573408; gap_pct=n/a; component_gaps=cjs_medium_seed11=96.10%, steiner_medium_seed11=22.41%, tsp_medium_seed11=100.00%

## Transcript Coherence
- `gemini-flash-latest`: transcript_entries=3; wall_s=214.8s; stop_reason=`decision_stop`
- `claude-sonnet-4.6`: transcript_entries=3; wall_s=42.0s; stop_reason=`decision_stop`
- `gpt-5.4-mini`: transcript_entries=3; wall_s=14.9s; stop_reason=`decision_stop`

## Suggested Fixes
- Add stronger contract/schema reminders for sub-problem answers inside the portfolio response.
