# portfolio_medium_seed2

## Parse
- `gemini-flash-latest`: parse_path=`strict_protocol_cf`; stop_reason=`decision_stop`; turns=1; attempts=1; error=-
- `claude-sonnet-4.6`: parse_path=`strict_protocol_cf`; stop_reason=`decision_stop`; turns=1; attempts=1; error=-
- `gpt-5.4-mini`: parse_path=`strict_protocol_cf`; stop_reason=`decision_stop`; turns=1; attempts=1; error=-

## Feasibility
- `gemini-flash-latest`: feasible=False; failures=steiner_medium_seed2: interference violation between Dune and Port; tsp_medium_seed2: tour must contain exactly 20 cities
- `claude-sonnet-4.6`: feasible=False; failures=tsp_medium_seed2: tour items must be integers
- `gpt-5.4-mini`: feasible=False; failures=cjs_medium_seed2: schedule must be an object; steiner_medium_seed2: submission must be an object; tsp_medium_seed2: submission must provide tour as a list of city indices

## Score vs Baseline
- baseline_objective=0.0; gold_objective=100.0
- `gemini-flash-latest`: score=-8.137342787499074; gap_pct=n/a; component_gaps=cjs_medium_seed2=113.33%, steiner_medium_seed2=18.31%, tsp_medium_seed2=100.00%
- `claude-sonnet-4.6`: score=24.47608921012602; gap_pct=n/a; component_gaps=cjs_medium_seed2=113.33%, steiner_medium_seed2=18.31%, tsp_medium_seed2=100.00%
- `gpt-5.4-mini`: score=-0.8710435979417526; gap_pct=n/a; component_gaps=cjs_medium_seed2=100.00%, steiner_medium_seed2=18.31%, tsp_medium_seed2=100.00%

## Transcript Coherence
- `gemini-flash-latest`: transcript_entries=3; wall_s=162.7s; stop_reason=`decision_stop`
- `claude-sonnet-4.6`: transcript_entries=3; wall_s=49.6s; stop_reason=`decision_stop`
- `gpt-5.4-mini`: transcript_entries=3; wall_s=17.4s; stop_reason=`decision_stop`

## Suggested Fixes
- Add stronger contract/schema reminders for sub-problem answers inside the portfolio response.
