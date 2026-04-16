---
isContextNode: true
containedNodeIds:
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_2.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-spec.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-theory.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/1776343402673uBv_0.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-orchestration-hourly.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-spec_1.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/llmpromptflowanswer.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/kaggle-submission-design.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_1_0.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_1.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/kaggle-submission-filetree.md
---
# ctx
Nearby nodes to: /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_2.md
```
let's now sketch out our orchestartion proposal
└── Factory Plan — 3 Parallel Factories to Build v1 in ~14h
    ├── Experiment Spec — Protocol Contract + Dataset Design
    │   ├── Experiment Theory — What We Measure & Why
    │   │   ├── alright help me figure out next steps and plan
    │   │   └── Factory Orchestration — Hr-by-Hr Implementation
    │   │       └── Kaggle Submission — Codebase Design (Answer)
    │   │           ├── KAGGLE SPEC: Measuring Progress Toward AGI - Cognitive Abilities
    │   │           │   └── help me design the codebase,
    │   │           └── Filetree — metabench/kaggle_submission/
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
- **help me design the codebase,** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_1.md)
  # help me design the codebase,
we will put everything required for the final kaggle benchmark submission into the metabench/kaggle_submission folder
let's design an filetree structure for this, and walk through the factory orchestration implementation plan 
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
- **Kaggle Submission — Codebase Design (Answer)** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/kaggle-submission-design.md)
  # Kaggle Submission — Codebase Design (Answer)
Design for metabench/kaggle_submission/: write-path-isolated subtrees per factory, SDK-facing kaggle/ layer for submission artifacts, internal harness/benchmark/analyzer split. Detailed in two child nodes.
# Kaggle Submission — Codebase Design
## Binding constraints
**Deadline: 2026-04-17 09:59 AM GMT+10 (~14h).** Metacognition track ($20k).
Kaggle-facing must-haves (from [\[factory-plan_1_0]\]):
- Kaggle Benchmark (via `kaggle-benchmarks` SDK) = mandatory project link
- Kaggle Tasks — all authored by us, private until deadline
- Writeup ≤1500 words, 3 pages, with fixed template sections
- Cover image (mandatory), optional public notebook
  ...37 additional lines
- **KAGGLE SPEC: Measuring Progress Toward AGI - Cognitive Abilities** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_1_0.md)
  # KAGGLE SPEC: Measuring Progress Toward AGI - Cognitive Abilities
Design high-quality benchmarks that go beyond recall to evaluate how frontier models truly reason, act, and judge.
You have an in-progress draft.
Complete and submit your draft by the deadline: Apr 17, 2026 at 9:59 AM GMT+10.
Overview
Latest update: Please ensure your submission includes a writeup that adheres to the format we provided AND an attached Kaggle Benchmark (it should look like this https://www.kaggle.com/benchmarks/<your username>/<your-benchmark-name>)
Current AI models often succeed by exploiting familiar data or memorized patterns, making existing evaluations poor judges of how models truly think. This hackathon challenges you to bridge that gap. Your task is to create high-quality benchmarks with Kaggle’s Benchmarks to test true understanding. We are asking you to focus on the cognitive faculties highlighted in Google DeepMind’s paper— Measuring progress toward AGI: A cognitive framework. The five faculties and tracks to focus on are: learning, metacognition, attention, executive functions, and social cognition. Designing these rigorous standards will build detailed cognitive profiles of frontier models and reveal exactly how close we are to achieving Artificial General Intelligence (AGI).
Start
a month ago
Close
  ...113 additional lines
- **alright help me figure out next steps and plan** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/1776343402673uBv_0.md)
  # alright help me figure out next steps and plan
- **Factory Orchestration — Hr-by-Hr Implementation** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-orchestration-hourly.md)
  # Factory Orchestration — Hr-by-Hr Implementation
14-hour sequencing using voicetree MCP: Hr 0–1 schema freeze + spawn, Hr 1–3 parallel build + first fixture, Hr 3–6 consolidate + spot-check, Hr 6–10 Phase 1 fire (gated on frozen questions.jsonl), Hr 10–14 Phase 2 + CF + writeup package.
# Factory Orchestration — Hr-by-Hr
## Mechanism (voicetree MCP)
- Each factory **lead** runs in its own voicetree terminal.
- `spawn_agent` creates Codex subagents; brief includes pinned `schema-freeze.md` commit SHA + explicit write-path whitelist.
- Leads gate with `wait_for_agents` on two events: schema freeze (Hr 1), questions.jsonl freeze (Hr 6).
- Each lead drops one hourly progress node (per factory-plan coordination requirement).
## Hr 0–1 — Schema freeze + spawn (SEQUENTIAL, blocks everything)
1. **B-lead** writes `schema-freeze.md` + skeleton `harness/protocol.py` (types only, no logic). `git commit`, record SHA.
  ...55 additional lines
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
- **Filetree — metabench/kaggle_submission/** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/kaggle-submission-filetree.md)
  # Filetree — metabench/kaggle_submission/
Concrete directory layout: benchmark/ (Factory A), harness/ (Factory B internal), kaggle/ (Factory B SDK-facing), analyzer/+paper/ (Factory C), results/ (runtime), scripts/, tests/, plus coordination markers.
# Filetree — `metabench/kaggle_submission/`
```
metabench/kaggle_submission/
├── README.md                        # entry point, run instructions
├── pyproject.toml                   # pinned deps (kaggle-benchmarks, ortools, google-genai, openai, anthropic)
├── schema-freeze.md                 # B-lead Hr 0–1 — field contract, SHA-pinned source of truth
├── predictions.md                   # C-lead Hr 1 — frozen pre-registration
├── .coordination/                   # factory status (not shipped)
  ...76 additional lines
<TASK> IMPORTANT. YOUR specific task, and the most relevant context is the source note you were spawned from, which is:
        /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_2.md: # let's now sketch out our orchestartion proposal 

the factory plan might be a bit out of date at this point with recent changes

so be a thinking partner for me here 

 </TASK>

