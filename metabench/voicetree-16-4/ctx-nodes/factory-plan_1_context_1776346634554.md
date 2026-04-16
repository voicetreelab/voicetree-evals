---
isContextNode: true
containedNodeIds:
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_1.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-spec.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-theory.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/1776343402673uBv_0.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-spec_1.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/llmpromptflowanswer.md
---
# ctx
Nearby nodes to: /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_1.md
```
help me design the codebase,
└── Factory Plan — 3 Parallel Factories to Build v1 in ~14h
    ├── Experiment Spec — Protocol Contract + Dataset Design
    │   ├── Experiment Theory — What We Measure & Why
    │   │   ├── alright help me figure out next steps and plan
    │   ├── run me through the llm prompt design + flow
    │   │   └── LLM Prompt Design + Flow (Answer)
```

## Node Contents
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
- **run me through the llm prompt design + flow** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-spec_1.md)
  # run me through the llm prompt design + flow
when an LLM gets given a question, what's the additional prompt we add on? how does it change per phase?
- **alright help me figure out next steps and plan** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/1776343402673uBv_0.md)
  # alright help me figure out next steps and plan
- **LLM Prompt Design + Flow (Answer)** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/llmpromptflowanswer.md)
  # LLM Prompt Design + Flow (Answer)
Walkthrough of what the harness prepends to each question: constant system prompt + phase-specific output contract (Turn 1 plan / Turn N exec / CF fork). Raw-string loop, post-hoc Gemini Flash extractor.
# LLM Prompt Design + Flow
Question asked: *when an LLM gets given a question, what's the additional prompt we add on? how does it change per phase?*
## Layer 1 — System prompt (constant, injected every turn)
> You are solving an optimization problem under a 30-minute wall budget. Objective is economic: score = max(0, 100 − gap_pct) − 0.01 × wall_seconds. You may decompose the problem into subtasks, revise your plan each turn, and stop when you judge no more subtasks are worth their time cost. Raw text output; the harness extracts structured fields post-hoc.
Establishes economic scoring, decomposition license, stop-rationality framing, and raw-string I/O contract.
## Layer 2 — User message (varies by phase)
### Turn 1 (plan phase)
`<instance JSON>` + the plan output contract:
  ...35 additional lines
<TASK> IMPORTANT. YOUR specific task, and the most relevant context is the source note you were spawned from, which is:
        /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_1.md: # help me design the codebase,


we will put everything required for the final kaggle benchmark submission into the metabench/kaggle_submission folder

let's design an filetree structure for this, and walk through the factory orchestration implementation plan  </TASK>

