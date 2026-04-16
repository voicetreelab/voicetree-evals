# Concerns for mwis_medium_seed10

- class: `mwis`
- difficulty: `medium`
- baseline_gap_pct: `100.0`

## Parse
- `gemini-flash-latest`: parse_path=`strict_protocol`, parse_events=1, modes=['strict'], error=`RuntimeError: llm CLI timed out after 180s`
- `claude-sonnet-4.6`: parse_path=`not_run`, parse_events=0, modes=['-'], error=`skipped remaining rows after repeated timeouts on mwis_medium_seed3`
- `gpt-5.4-mini`: parse_path=`strict_protocol_cf`, parse_events=2, modes=['strict', 'cf_strict'], error=`-`

## Feasibility
- `gemini-flash-latest`: feasible=`True`, failure_reason=`RuntimeError: llm CLI timed out after 180s`
- `claude-sonnet-4.6`: feasible=`False`, failure_reason=`skipped remaining rows after repeated timeouts on mwis_medium_seed3`
- `gpt-5.4-mini`: feasible=`True`, failure_reason=`-`

## Score vs Baseline
- `gemini-flash-latest`: score=91.78397265624953, gap_pct=3.90625, baseline_gap_pct=100.0, improved_vs_baseline_gap=True, final_submission_source=`parsed`
- `claude-sonnet-4.6`: score=0.0, gap_pct=100.0, baseline_gap_pct=100.0, improved_vs_baseline_gap=False, final_submission_source=`not_run`
- `gpt-5.4-mini`: score=89.44888883041529, gap_pct=10.416666666666666, baseline_gap_pct=100.0, improved_vs_baseline_gap=True, final_submission_source=`cf_parsed`

## Transcript Coherence
- `gemini-flash-latest`: stop_reason=`error`, n_exec_turns=1, transcript_messages=2, wall_s=430.9777551670559, retries=0
- `claude-sonnet-4.6`: stop_reason=`skipped_model`, n_exec_turns=0, transcript_messages=0, wall_s=0.0, retries=0
- `gpt-5.4-mini`: stop_reason=`decision_stop`, n_exec_turns=1, transcript_messages=3, wall_s=13.44445366691798, retries=0

## Suggested Fixes
`gemini-flash-latest` ended with stop_reason `error` on `mwis_medium_seed10`.
`claude-sonnet-4.6` needs prompt/protocol attention for `mwis_medium_seed10` because parse_path was `not_run`.
`claude-sonnet-4.6` produced an infeasible or missing final answer for `mwis_medium_seed10`; inspect verifier failure `skipped remaining rows after repeated timeouts on mwis_medium_seed3`.
`claude-sonnet-4.6` did not beat the baseline gap on `mwis_medium_seed10`.
`claude-sonnet-4.6` ended with stop_reason `skipped_model` on `mwis_medium_seed10`.
