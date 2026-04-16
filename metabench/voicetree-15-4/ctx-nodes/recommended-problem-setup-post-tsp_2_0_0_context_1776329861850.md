---
isContextNode: true
containedNodeIds:
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_2_0_0.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_2_0.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_2.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/trajectory-post-tsp-synthesis.md
  - /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_1.md
---
# ctx
Nearby nodes to: /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_2_0_0.md
```
alright, i think then it's time to just make a kaggle benchmark actual spike
└── AI feedback
    └── okay, bringing everything together into a final benchmark
        └── Recommended setup: NL-wrapped coupled job shop with economic stop scoring
            ├── Trajectory synthesis: from HCH metacog to post-TSP simplification
            ├── #
```

## Node Contents
- **AI feedback** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_2_0.md)
  # AI feedback
Manu, this is a significant evolution and I have real thoughts. Let me be direct about what's working, what concerns me, and where I think you're at risk of over-engineering before the deadline.
What's genuinely strong in this trajectory:
The construction-vs-search distinction is the most important insight in this document. Recognizing that TSP and vanilla job shop have memorized greedy recipes that produce one-shot ceilings is exactly the kind of finding that separates a real benchmark from a toy. The empirical anchor (Gemini 3.1 Pro hitting 4.43% mean gap with one-exec-turn-then-stop across all seeds) is the evidence you need to justify the pivot away from jobshop, and the massive A1 miscalibration (declared 100-135% vs realized 1.75-8.49%) is itself a publishable metacognitive finding.
The wall-clock economic scoring is also solid. It transforms the benchmark from pure accuracy maximization into resource-bounded rationality testing, which is the right frame for metacognition.
What concerns me:
You're drifting from Kaggle submission toward research project. The judge gave you 85.5 and said the single highest-leverage fix was "scale n from 24 to 200 with counterfactual baselines." You've instead gone deeper into problem-class taxonomy, are evaluating Steiner×coloring composites, and are considering a cross-class 200-500 question split. This is better research but the Kaggle deadline is real.
Ask yourself: if you had to submit tomorrow, which version wins more prize money?
Version A: Refined coupled job shop, n=200, Free-Choice/Forced-Atomic/Forced-Decomposed counterfactuals, A1/A2/A3 with calibration-resolution decomposition
Version B: Novel composite class (Steiner×coloring), smaller n, stronger per-instance metacog signal, protocol-side innovations
  ...18 additional lines
- **okay, bringing everything together into a final benchmark** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_2.md)
  # okay, bringing everything together into a final benchmark
1. we should probably build on what beyond bench did 
https://arxiv.org/pdf/2509.24210
2. 
  - restore a 5 min planning turn / larger benchmark-style
    budget
  - replace exact-correctness claims with thresholded distance-
    to-optimal forecasts
Initial idea:
One is HCH-style compute allocation prediction. Give the agent a
  ...171 additional lines
- **Recommended setup: NL-wrapped coupled job shop with economic stop scoring** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp.md)
  # Recommended setup: NL-wrapped coupled job shop with economic stop scoring
Recommended one main benchmark family that fits the graph constraints: procedurally generated coupled two-factory job-shop instances with exact offline gold, a natural-language surface, visible wall-clock budgeting, and a single canonical objective-optimizing prompt.
## Recommended problem setup
Use procedurally generated **coupled two-factory job-shop** instances as the main benchmark family.
## Why this best fits the graph
- It keeps the strongest part of the budget-metagame idea: agents can improve a baseline answer progressively, and stopping early or late is economically meaningful.
- It avoids the main TSP failure mode: there is no single memorized NN+2-opt-style recipe that frontier models can reliably recall and execute.
- It exposes the metacognitive signals the graph cares about: upfront uncertainty, decomposition choice, per-subtask effort prediction, intermediate self-checking, and stop-decision quality.
- It stays fully automatable: generate from seed, compute exact gold offline with OR-Tools, verify any proposed schedule mechanically.
- It can be rendered in natural language, which helps avoid turning the task into 'just emit a solver template.'
  ...30 additional lines
- **Trajectory synthesis: from HCH metacog to post-TSP simplification** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/trajectory-post-tsp-synthesis.md)
  # Trajectory synthesis: from HCH metacog to post-TSP simplification
Reconstructed the benchmark-design arc using `vt graph structure` plus the task context and key node heads. Core arc: HCH metacog targets -> NP-hard/generative search -> budget-metagame/TSP harness -> empirical falsification of TSP -> shift toward coupled job shop.
## CLI used
`vt graph structure /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4`
## Orchestration
Single-agent task. The two outputs here — trajectory synthesis and recommended setup — are tightly coupled, so decomposition would not have improved speed or quality.
## High-level insight trajectory
1. The starting point was HCH metacognition, not raw accuracy. The graph repeatedly centers the benchmark on: whether the model knows when decomposition helps, whether it can estimate subtask difficulty/effort, and whether it can verify intermediate work and stop rationally.
2. The next move was to find a procedurally generated problem family with exact verification, scalable difficulty, and a natural-language surface. The graph's generation-pipeline nodes explicitly push toward seedable instances, offline gold computation, and paired formal/NL renderers.
3. NP-hard approximable problems looked attractive because they support partial credit and a real economic tradeoff: more compute can buy a better answer. That led to the budget-metagame framing and then to TSP as the first concrete MVP.
  ...19 additional lines
- **#** (/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_1.md)
  # 
<TASK> IMPORTANT. YOUR specific task, and the most relevant context is the source note you were spawned from, which is:
        /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_2_0_0.md: # alright, i think then it's time to just make a kaggle benchmark actual spike

here's https://kkb-production.jupyter-proxy.kaggle.net?token=eyJhbGciOiJkaXIiLCJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwidHlwIjoiSldUIn0..ANhWVdv8oKrZrM8BdFNkxA.tlxCrWcXyovDh_h7El7zhTc08ETzZaAD8DB9GpCS4U4P6NxQHbAwD37fHaTXSKU0F_n7Vh2RFLxZaqCS07kkWfBXjav20cHTDX-QJ9mA7Kkuezi0-L6-PNvFlEyauDDVW1RY2aOr2N5095ON48kymuQCPdWUyhlMzZjV5oSYKDTE0Rzb5mhyzRgdv109axJeYoUwS_dUs3cGjOHSmARZJ8533nyhiyX0b_YJGZUv5yZhc4RcRKL_IwQpvOFTA_bS.ZsFZz-Ye53vvlQ44OwJ0-A


let's make it just for the intial spike do the 5x6 coupled version 

and run it against gemini 3, sonnet, and gpt5.4

you can see how we did this before /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/task_1776233921036o3d.md

you will be orchestartor, add orchestrator discipine to your task list to not do the work yourself

you can start by spawning a codex agent to try implement and run this on the actual kaggle

 </TASK>

