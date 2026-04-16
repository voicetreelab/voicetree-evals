---
isContextNode: false
---
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
  hard task — a SWE problem, a METR-length item, a hard reasoning
  problem. Instead of solving directly, it first decomposes into
  subcomponents (one is fine if the task is atomic), and for each
  subcomponent predicts two things in an isolated chat: the
  probability it will solve this part in a single session, and the
  token budget it will need. Each subcomponent then gets executed
  in its own fresh session under the predicted budget, and the
  results are integrated. We score Brier per subcomponent on
  solvability, MAPE per subcomponent on tokens, and end-to-end
  accuracy on the full task. The construct is deliberately
  multi-signal — decomposition quality, per-part difficulty
  prediction, total-budget prediction, and integration — because
  all four are HCH properties we want to measure, and for HCH the
  conflation is the point. The qualitative prior that’s
  discriminative and worth pre-registering: Codex pre-commits to a
  budget and halts when it exceeds it; Claude tends to keep going
  regardless. That’s not a smartness difference, it’s a
  self-allocation-under-scarcity difference, and it’s exactly what
  HCH requires from its primitive. Cheapest headline item is a
  negative-control unsolvable subcomponent (Riemann-style); any
  model predicting high P(solve) on it has broken self-assessment.



Evolution 1:


Our current approach is a metacognition benchmark built around
  natural-language coupled job-shop scheduling.

  The core protocol is: the model first makes an explicit
  planning-and-calibration move, then gets a small number of
  execution turns to improve its current best answer, while paying
  a wall-clock cost for continuing. So we are not just measuring
  whether the model eventually gets the right answer; we are
  measuring whether it can reason well about its own reasoning
  process.

  The problem family is a two-factory supply-chain scheduling
  task. Each job must finish its route through Factory A before
  the corresponding job can begin in Factory B. Each factory has
  its own machine routing, machine-capacity constraints, and
  precedence structure. The model is given a precise natural-
  language problem statement plus a baseline feasible schedule,
  and it tries to improve that baseline under a budgeted multi-
  turn protocol.

  We like this setup because it hits the properties we actually
  care about. It creates genuine upfront uncertainty, it naturally
  forces decomposition into meaningful subtasks, and it supports
  non-obvious global tradeoffs where a locally sensible move can
  be globally bad. It also gives us exact offline gold via OR-
  Tools, so scoring is objective rather than heuristic.

  The benchmark signal we want is specifically metacognitive: can
  the model predict how hard the task is, choose a good next
  subproblem, update confidence after partial work, and stop at a
  rational point instead of either bailing too early or grinding
  unproductively. The wall-clock budget pressure is important
  because it turns this into an economic decision problem rather
  than a pure accuracy maximization problem.

  Protocol-wise, we have deliberately simplified to a single
  canonical objective-optimizing prompt rather than multiple
  prompt arms. The current belief is that the real benchmark
  signal should come from the interaction between the problem
  structure and the stop/decomposition protocol, not from
  ablation-style prompt variants.

  Implementation-wise, we are testing two nearby versions of this
  idea. The lighter version uses a simpler two-stage flowshop
  where the answer is just a job ordering; the heavier version
  keeps the full coupled job-shop structure and asks the model to
  emit a complete schedule that we can verify exactly. The point
  of running both is to see whether the richer structure gives
  materially better metacognitive signal, or whether a simpler
  formulation already captures most of the value with much lower
  operational complexity.

  The high-level thesis is: a useful metacognition benchmark
  should not just ask “can the model solve this?” It should ask
  “can the model allocate effort, decompose well, calibrate
  itself, and stop intelligently on a problem where those choices
  genuinely matter?” Coupled natural-language scheduling is our
  current best candidate for that.


Evolution 2:

 Load-bearing conclusions

  Problem-class distinction (the central frame)

  - Construction problems (TSP, jobshop, bin-pack, vanilla Steiner)
   have memorized greedy recipes → one-shot ceiling, no metacog
  signal.
  - Search problems (Sokoban, PDDL, chess-like) require state-tree
  exploration → multi-turn is structurally forced.
  - Three-tier taxonomy (Mia-validated): Tier 1
  general-recipe-but-expensive (Sokoban, N-puzzle); Tier 2
  instance-dependent heuristic choice (PDDL, Max-SAT at phase
  transition, CSP, MAPF, graph coloring, treewidth, Group/Directed
  Steiner); Tier 3 no general framework (GGP, ARC-AGI, program
  synthesis).
  - Correct filter isn't "NP-hard" — it's "does a solver
  competition show a rotating winner?" TSP/jobshop fail this;
  coloring/Max-SAT/PDDL/MAPF pass.

  Empirical anchor — 6×7 coupled jobshop, Gemini 3.1 Pro, seeds
  1/2/3

  - Gaps 8.49 / 1.75 / 3.03% (mean 4.43%) — NOT Johnson-saturated,
  real headroom.
  - Every seed: one exec turn then stop. Same one-shot pattern as
  TSP, flowshop, 3×4, 5×6.
  - Massive A1 miscalibration: declared gaps 100/135/120% vs
  realized 1.75–8.49%, atomic_p_correct=0 across the board.
  - Key implication: multi-turn is a protocol problem, not just a
  problem-class problem. Even rich instances don't force iteration.

  Ruled out (don't revisit)

  - Pure size-scaling on jobshop: binds on working memory, not     
  metacog — memorized recipes (list scheduling, shifting
  bottleneck) scale.                                               
  - Vanilla Steiner Tree: Takahashi-Matsuyama shortest-path      
  heuristic too strong (models derive it without knowing the name).
  - Open Shop Scheduling: NP-hard but has memorized recipes (LAPT,
  list scheduling) → Tier 1b. I overweighted this earlier;         
  corrected.                                                     
  - Stochastic durations: muddies gold definition.                 
  - K=3+ composites upfront: spec bloat, verifier fragility, gold
  explosion — speculative, only escalate if K=2 still ceilings.    
  - Budget-anxiety skip: was wrong. Ivy's real objection was only
  in-prompt stop-rule coaching ("stop when marginal gain < cost"). 
  State feedback (time/tokens consumed) is equivalent to a chess 
  clock and must stay.                                             
                                                                 
  Kept / validated                                               

  - Economic $score = reward·(100 − gap%) − penalty·wall_s is      
  WPMS-shaped by construction. Outer scoring layer is correct
  as-is.                                                           
  - NL wrapping is free (Meg v2 proved it suppresses code        
  emission).                                                       
  - Mei's harness (hch/codex_metagame_v2) is reusable scaffolding:
  plan/exec loop, budget injection, hard-kills, JSONL logging.     
  Working budgets: TOTAL=1800s, SUBTASK=600s, PLAN=300s (30s plan
  killed turn 1).                                                  
  - Per-subtask budget already encodes "decompose-for-more-compute"
   economics.                                                      
  - Offline gold in minutes is acceptable (user relaxed the
  "millisecond compute" constraint).                               
                                                                 
  Amplifier stack                                                  
                                                                 
  - Problem structure: size; sequence-dependent setups; shared     
  operator/resource pool; multi-objective.
  - Surface form: NL wrap (free); distractors; specification gap;  
  online/adversarial reveal (forces multi-turn; nuclear option if  
  composites still ceiling).                                     
  - Scoring pressure: budget feedback (keep); minimum-words answer;
   competing goals.                                                
                                                                 
  Current finalists (ranked)                                       
                                                                 
  1. Steiner × coloring composite (K=2) — novel,                   
  contamination-proof, tight coupling: relay choice determines   
  coloring subgraph. Coastal Emergency worked example (8 villages, 
  3 terminals, planted Port-Bay-Cliff triangle in interference   
  graph) showed greedy "Steiner-first-then-color" loses ~30% to  
  joint-optimal. Nia (Codex) is currently building + running the
  3-seed spike on Gemini 3.1 Pro — report pending.
  2. Graph coloring at phase transition — DIMACS-validated rotating
   heuristics (DSATUR/RLF/tabu/ZykovColor), best NL surface via    
  scheduling/conflict scenarios.
  3. Weighted Partial Max-SAT at phase transition — strongest      
  evidentiary base (MaxSAT Eval); NL surface weak. Note: our outer 
  scoring is already WPMS-shaped regardless of underlying problem.
  4. Group / Directed Steiner Tree — no const-factor approx →      
  instance-specific heuristic pressure.                            
  5. Custom novel PDDL domain — zero contamination by construction,
   higher harness cost.                                            
                                                                 
  Open questions / pending decisions                               
   
  - Nia's Steiner × coloring spike results — does composite        
  coupling actually flip one-shot, or does Gemini 3 stop at turn 2
  like every prior spike?                                          
  - If composites still one-shot → protocol-side lever (online   
  reveal, min-exec-turns, between-turn critical-info feedback).    
  - For 200–500-question Kaggle set: proposed cross-class split
  (30% coloring / 30% Steiner×coloring / 20% WPMS-NL / 10%         
  Group/Directed Steiner / 10% open-shop or MAPF). Cross-class A1
  calibration becomes its own finding.                             
  - "Beyond BeyondBench" positioning: A3 stop-rationality, A1    
  pre-run calibration, composite coupling, wall-clock economics —  
  all novel vs. BeyondBench's accuracy-only frame.
  - 1-turn recipe-recall probe remains a cheap gate for any new    
  candidate before investing in a full spike.   
[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_2_0.md]]
[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_2_1.md]]