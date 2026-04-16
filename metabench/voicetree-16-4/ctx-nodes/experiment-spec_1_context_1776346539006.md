---
isContextNode: true
containedNodeIds:
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-spec_1.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-spec.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-theory.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan.md
---
# ctx
Nearby nodes to: /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-spec_1.md
```
run me through the llm prompt design + flow
└── Experiment Spec — Protocol Contract + Dataset Design
    ├── Experiment Theory — What We Measure & Why
    └── Factory Plan — 3 Parallel Factories to Build v1 in ~14h
```

## Node Contents
- **Experiment Spec — Protocol Contract + Dataset Design** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-spec.md)
  # Experiment Spec — Protocol Contract + Dataset Design
Two-level spec: per-question protocol (turn 1 plan + turn N exec, raw-string with post-hoc extractor) and benchmark-level design (~210 questions = 120 solo across 6 classes × 2 difficulties × 10 seeds + 90 portfolios).
# Experiment Spec
## Per-question protocol
### System prompt
> You are solving an optimization problem under a 30-minute wall budget. Objective is economic: score = max(0, 100 − gap_pct) − 0.01 × wall_seconds. You may decompose the problem into subtasks, revise your plan each turn, and stop when you judge no more subtasks are worth their time cost. Raw text output; the harness extracts structured fields post-hoc.
### Turn 1 contract (plan)
```
PLAN_STATE: <free-form, model-structured plan; persisted verbatim into turn 2 prompt>
NEXT_SUB: {id: 1, desc: <str>, p_solve: <float>, time_budget_s: <int>}
  ...47 additional lines
- **Experiment Theory — What We Measure & Why** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-theory.md)
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
  ...29 additional lines
- **Factory Plan — 3 Parallel Factories to Build v1 in ~14h** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan.md)
  # Factory Plan — 3 Parallel Factories to Build v1 in ~14h
Three parallel factories with Opus orchestrators coordinating Codex implementers: Content (dataset+verifiers), Platform (harness+kaggle), Research (analysis+paper). Ships in ~14h with all 210 questions, Phase 1+2 data, CF pass, paper draft through results.
# Factory Plan — Building v1
Three parallel factories, each with **Opus orchestrator** coordinating **Codex implementers**.
## Factory A — Content (dataset + verifiers)
**A-lead (Opus):** schema freeze review, per-class task definition, PR review, consolidate fragments to `questions.jsonl`.
**A-Codex (one per problem class):**
- A-CJS: CJS-5×6 generator + verifier (baseline: `hch/codex_metagame_v2/`)
- A-Steiner: Steiner×coloring (baseline: `hch/portfolio_spike/steiner_coloring_*.py`)
- A-GraphCol: graph coloring slack (baseline: `hch/portfolio_spike/graph_coloring_instance.py`)
  ...56 additional lines
<TASK> IMPORTANT. YOUR specific task, and the most relevant context is the source note you were spawned from, which is:
        /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-spec_1.md: # run me through the llm prompt design + flow

when an LLM gets given a question, what's the additional prompt we add on? how does it change per phase? </TASK>

