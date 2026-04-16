# Concerns for mwis_medium_seed7

- class: `mwis`
- difficulty: `medium`
- baseline_gap_pct: `100.0`

## Parse
- `gemini-flash-latest`: parse_path=`strict_protocol`, parse_events=2, modes=['strict', 'cf_strict_parse_failed'], error=`RuntimeError: llm CLI timed out after 180s`
- `claude-sonnet-4.6`: parse_path=`not_run`, parse_events=0, modes=['-'], error=`skipped remaining rows after repeated timeouts on mwis_medium_seed3`
- `gpt-5.4-mini`: parse_path=`strict_protocol_cf`, parse_events=2, modes=['strict', 'cf_strict'], error=`-`

## Feasibility
- `gemini-flash-latest`: feasible=`True`, failure_reason=`RuntimeError: llm CLI timed out after 180s`
- `claude-sonnet-4.6`: feasible=`False`, failure_reason=`skipped remaining rows after repeated timeouts on mwis_medium_seed3`
- `gpt-5.4-mini`: feasible=`False`, failure_reason=`selected set is not independent: edge V005-V052 is internal`

## Score vs Baseline
- `gemini-flash-latest`: score=85.76883623169978, gap_pct=11.700468018720748, baseline_gap_pct=100.0, improved_vs_baseline_gap=True, final_submission_source=`parsed`
- `claude-sonnet-4.6`: score=0.0, gap_pct=100.0, baseline_gap_pct=100.0, improved_vs_baseline_gap=False, final_submission_source=`not_run`
- `gpt-5.4-mini`: score=0.0, gap_pct=100.0, baseline_gap_pct=100.0, improved_vs_baseline_gap=False, final_submission_source=`cf_parsed`

## Transcript Coherence
- `gemini-flash-latest`: stop_reason=`decision_stop`, n_exec_turns=1, transcript_messages=2, wall_s=433.08540441608056, retries=0
- `claude-sonnet-4.6`: stop_reason=`skipped_model`, n_exec_turns=0, transcript_messages=0, wall_s=0.0, retries=0
- `gpt-5.4-mini`: stop_reason=`decision_stop`, n_exec_turns=1, transcript_messages=3, wall_s=16.073759416816756, retries=0

## Suggested Fixes
`claude-sonnet-4.6` needs prompt/protocol attention for `mwis_medium_seed7` because parse_path was `not_run`.
`claude-sonnet-4.6` produced an infeasible or missing final answer for `mwis_medium_seed7`; inspect verifier failure `skipped remaining rows after repeated timeouts on mwis_medium_seed3`.
`claude-sonnet-4.6` did not beat the baseline gap on `mwis_medium_seed7`.
`claude-sonnet-4.6` ended with stop_reason `skipped_model` on `mwis_medium_seed7`.
`gpt-5.4-mini` produced an infeasible or missing final answer for `mwis_medium_seed7`; inspect verifier failure `selected set is not independent: edge V005-V052 is internal`.
`gpt-5.4-mini` did not beat the baseline gap on `mwis_medium_seed7`.
