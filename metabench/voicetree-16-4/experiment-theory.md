---
color: blue
isContextNode: false
agent_name: Amit
---
# Experiment Theory — What We Measure & Why

Metacog benchmark operationalizing 6 cognitive self-knowledge skills on economically-scored optimization problems with exact gold. Primary claim: continuation-CF as headline metric measures stop-rationality directly in $ units, no prior benchmark has this.

# Experiment Theory

## What we measure
Six metacognitive self-knowledge skills that frontier LLMs show measurable deficits in, operationalized on economically-scored optimization problems with exact OR-Tools gold.

## Background and prior work
- **Kadavath et al. (2022)** — atomic self-knowledge on binary-correct QA. Doesn't generalize to continuous-optimality problems.
- **HLE / SWE-bench / MMLU** — accuracy-first. Can't distinguish "tried hard and failed" from "stopped too early."
- **HCH (Christiano)** — theoretical primitive requires knowing when to delegate to a copy of self; no existing benchmark operationalizes this directly.
- **Beyond Bench (arxiv 2509.24210)** — closest prior art; needs positioning against (research factory TODO).

## Six primary metacog skills
1. **M1 — Knowing what you know.** Per-subtask `p_solve` Brier vs kept-as-best.
2. **M4 — Self-assessing continuous output quality without oracle.** Post-artifact `QUALITY_FORECAST: {p_gap_le_2/5/10}` Brier vs verified gap. Not binary p_correct — thresholded distance-to-optimal.
3. **M5 — Knowing when to stop.** Forced-continuation CF-$ distribution across clean stops. **Headline metric.**
4. **M6 — Predicting value of more effort.** `expected_delta_score` vs realized CF Δ error.
5. **M7 — Decomposing effectively.** Score-trajectory AUC normalized by Phase-1 per-cell capability ceiling. Compound outcome of M1+M3+M5+M6+PLAN_STATE revision firing together.
6. **M10 — Knowing strengths across a domain.** Capability-controlled allocation gap on portfolios: optimal-given-Phase-1-profile minus observed.

## Why optimization, not QA
Problems here are continuous improvement toward optimal, not binary-correct. This makes:
- Binary p_correct meaningless → use thresholded CDF (M4)
- Decomposition-trajectory visible turn-by-turn → M7 has a natural AUC operationalization
- Stop-rationality economically falsifiable → M5 pays for continuation in wall-cost
- Capability normalization possible via Phase-1 ceiling → M7 and M10 isolate self-knowledge from raw ability

## Capability is controlled for
M7 and M10 both normalize by the model's own Phase-1 per-cell performance. A weak-but-well-calibrated model can outscore a strong-but-miscalibrated one on metacog axes. This is what differentiates this from accuracy benchmarks.

## Pre-registered predictions (freeze before Phase 1 fires)
1. All 3 frontier families show plan-once-execute-once-stop as dominant behavior.
2. Gemini 3 Pro is systematically overconfident-in-stopping: positive CF-$ on ≥5/7 observed stops. Supported by n=1 masked-block: predicted −10, realized +2.98.
3. GPT-5.4 does not stop under budget pressure; hits max_exec_turns in portfolio settings.
4. Sonnet 4.6 has highest subtask count + lowest feasibility rate; explores broadly, doesn't convert.
5. M10 allocation gaps differ by family, not monotone in raw capability (weaker model can have smaller gap than stronger).

## What's novel
- **Continuation-CF as primary metric** — not accuracy, not calibration-proxy. Direct $-denominated metacog error.
- **Capability-controlled allocation gap** — operationalizes HCH's "knowing your copy's strengths" without needing explicit self-copy framing.
- **One unified protocol across 6 problem classes** → cross-class replication of findings built into the design, not post-hoc.
- **PLAN_STATE as free-form model-chosen string** → measures decomposition craft (M7) without imposing a scaffold that biases the finding.

## The paper's claim chain
M1 + M4 establish the model can predict its own present and immediate-future state. M5 + M6 establish whether it stops at the right moment (headline). M7 establishes whether it turns decomposition-friendly problems into gains. M10 establishes whether it knows its own strengths across a domain. All five are independently measurable on the same sessions; together they characterize an agent's metacognitive profile.


[[1776343402673uBv_0]]
