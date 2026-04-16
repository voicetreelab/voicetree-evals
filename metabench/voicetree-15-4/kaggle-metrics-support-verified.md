---
color: green
isContextNode: false
agent_name: Hana
---
# Kaggle Benchmarks metrics support verified

Verified from Kaggle's official `kaggle-benchmarks` repo plus local live `.run.json` artifacts that Kaggle Benchmarks exposes per-request and per-conversation input/output token counts, token costs, and backend latency. Key caveat: these usage metrics are documented as available only through the Kaggle Model Proxy; current public `Usage` docs do not expose a separate reasoning/thinking-token metric.

## Findings
- `kaggle-benchmarks` user guide says the library exposes token usage, cost, and latency through the `Usage` dataclass at both per-message and aggregated chat level.
- The same guide states these usage metrics are only available when using the Kaggle Model Proxy; otherwise the fields return `None`.
- Official protobuf schema `ModelUsageMetrics` includes `input_tokens`, `output_tokens`, `thinking_tokens`, `duration_ms`, `input_tokens_cost_nanodollars`, `output_tokens_cost_nanodollars`, and `total_backend_latency_ms`.
- Current public Python `Usage` dataclass exposes only `input_tokens`, `output_tokens`, `input_tokens_cost_nanodollars`, `output_tokens_cost_nanodollars`, and `total_backend_latency_ms`, plus a computed `total_cost_nanodollars` property.
- Local live Kaggle `.run.json` artifacts in this repo contain per-request and aggregated conversation metrics with keys `inputTokens`, `outputTokens`, `inputTokensCostNanodollars`, `outputTokensCostNanodollars`, and `totalBackendLatencyMs`.
- Local live `.run.json` artifacts also include run-level `startTime` and `endTime`, so wall-clock run duration can be computed even though the public `Usage` surface emphasizes backend latency.

## Practical answer for the benchmark design
- `time`: yes, backend latency per LLM request is exposed as `total_backend_latency_ms`; run-level start/end timestamps are also present in `.run.json`.
- `tokens`: yes, input and output token counts are exposed.
- `cost`: yes, input and output token costs are exposed in nanodollars; total cost must be summed from the two fields unless using the Python `Usage.total_cost_nanodollars` helper.
- `reasoning / thinking tokens`: not clearly available in the current public SDK surface or observed `.run.json` samples. The protobuf schema contains `thinking_tokens`, but I did not find it surfaced in `Usage` or present in the checked run artifacts.

## Learnings
- Tried repo-local notes first because this workspace already had Kaggle pilot artifacts; switched to the official Kaggle repo to distinguish observed behavior from documented support.
- Future agents should not assume "time" means full wall-clock runtime in the same API field as token metrics. Publicly documented per-exec timing is backend latency; whole-run timing is via run timestamps.
- The non-obvious pitfall is that cost/latency/tokens are conditional on the Kaggle Model Proxy path. If a task runs through another provider path, these metrics may be `None` even though the protobuf schema contains the fields.

### NOTES

- The protobuf schema is broader than the public Python `Usage` dataclass; `thinking_tokens` and `duration_ms` appear schema-level but not in the documented surface used by tasks.
- No code changes were made; this node documents research findings only.
- Primary evidence came from official Kaggle `kaggle-benchmarks` sources plus the repo's saved live `.run.json` artifacts.

[[budget-metagame-benchmark-analysis_1]]
