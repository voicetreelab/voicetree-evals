# Concerns for ve_medium_seed2

- class: `ve`
- difficulty: `medium`
- baseline_gap_pct: `100.0`

## Parse
- `gemini-flash-latest`: parse_path=`partial_rescue`, parse_events=2, modes=['partial_rescue', 'cf_partial_rescue'], error=`-`
- `claude-sonnet-4.6`: parse_path=`not_run`, parse_events=0, modes=['-'], error=`skipped remaining rows after repeated timeouts on mwis_medium_seed3`
- `gpt-5.4-mini`: parse_path=`partial_rescue`, parse_events=2, modes=['partial_rescue', 'cf_partial_rescue'], error=`-`

## Feasibility
- `gemini-flash-latest`: feasible=`True`, failure_reason=`-`
- `claude-sonnet-4.6`: feasible=`False`, failure_reason=`skipped remaining rows after repeated timeouts on mwis_medium_seed3`
- `gpt-5.4-mini`: feasible=`True`, failure_reason=`-`

## Score vs Baseline
- `gemini-flash-latest`: score=86.80225720975706, gap_pct=8.798039771072386, baseline_gap_pct=100.0, improved_vs_baseline_gap=True, final_submission_source=`cf_parsed`
- `claude-sonnet-4.6`: score=0.0, gap_pct=100.0, baseline_gap_pct=100.0, improved_vs_baseline_gap=False, final_submission_source=`not_run`
- `gpt-5.4-mini`: score=92.15625525408454, gap_pct=7.724569521746304, baseline_gap_pct=100.0, improved_vs_baseline_gap=True, final_submission_source=`cf_parsed`

## Transcript Coherence
- `gemini-flash-latest`: stop_reason=`decision_stop`, n_exec_turns=1, transcript_messages=3, wall_s=439.9703041249886, retries=0
- `claude-sonnet-4.6`: stop_reason=`skipped_model`, n_exec_turns=0, transcript_messages=0, wall_s=0.0, retries=0
- `gpt-5.4-mini`: stop_reason=`decision_stop`, n_exec_turns=1, transcript_messages=3, wall_s=11.917527209036052, retries=0

## Suggested Fixes
`claude-sonnet-4.6` needs prompt/protocol attention for `ve_medium_seed2` because parse_path was `not_run`.
`claude-sonnet-4.6` produced an infeasible or missing final answer for `ve_medium_seed2`; inspect verifier failure `skipped remaining rows after repeated timeouts on mwis_medium_seed3`.
`claude-sonnet-4.6` did not beat the baseline gap on `ve_medium_seed2`.
`claude-sonnet-4.6` ended with stop_reason `skipped_model` on `ve_medium_seed2`.
