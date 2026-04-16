---
color: green
agent_name: Mia
---

# NP-hard instance-specific heuristics: literature survey

## Summary

Surveyed the academic and practitioner literature for NP-hard problem classes where the heuristic is genuinely **instance-specific** — not just computationally expensive. The organizing framework is the **Algorithm Selection Problem** (Rice 1976): wherever solver competitions (SAT, IPC, PACE, MaxSAT Evaluations, DIMACS) produce a rotating winner across instances of the same problem class, that class qualifies. Two corrections to the provided taxonomy, plus a dedicated graph-problems section (per Mary's addendum).

**Top 3 for our use case:**
1. **Weighted Partial Max-SAT at phase transition** — strongest across all axes
2. **Graph Coloring (Erdős-Rényi at hardness threshold)** — best NL surface; DIMACS confirms per-instance variation; decades of solver-competition evidence
3. **Open Shop Scheduling (≥3 machines)** — no Johnson-equivalent confirmed; OR-Tools exact gold; NL-friendly; builds on existing job-shop codebase

---

## Tier Correction

**Tier 1a — Polynomial recipe (too easy):** 2-machine flowshop (Johnson 1954), bipartite matching. LLMs solve in one turn.

**Tier 1b — Memorized NP-hard recipe (confirmed failure mode):** TSP (NN+2-opt recalled), standard job-shop (list scheduling recalled), N-puzzle (IDA*). Evidence: our own TSP and job-shop spikes. These kill metacognitive signal: frontier models produce near-optimal solutions in one reasoning pass regardless of prompt arm. This category must be treated as a first-class filter criterion.

**Tier 2 — Target tier (instance-dependent heuristic, confirmed by competition data):**
All of the following are validated by solver competition results showing no single winner across instances of the same problem class:
- **Max-SAT / WPMS:** MaxSAT Evaluations — SATLike wins random/crafted; RC2 wins industrial
- **PDDL Planning:** IPC 2023 — IBaCop2 selects among 5+ planners per-instance using SAS+ features
- **MAPF:** EECBS vs CBS vs LaCAM — winner reverses by map topology and agent density (tracker.pathfinding.ai)
- **MILP:** SCIP vs Gurobi vs CPLEX — per-instance variation; ML branching (NIPS 2014) outperforms fixed rules
- **Graph Coloring:** DIMACS COLOR — DSATUR, RLF, tabu, ZykovColor each dominate on different graph families
- **Max-Cut:** GW gives 0.878 worst-case; Burer-Monteiro and SA outperform on dense/structured instances
- **Subgraph Isomorphism:** Glasgow >> VF2 on hard instances (1879 failures vs 51); RI/VF3 >> Glasgow on easy instances
- **Open Shop Scheduling (≥3 machines):** No polynomial rule (Gonzalez & Sahni 1976); CP/MIP required; instance-specific

**Tier 3 — No general framework (gold computation is the operational blocker):** GGP, Program Synthesis (ARC-AGI), Theorem Proving. Strongly instance-specific but computing optimal play requires a domain-specific solver — operationally blocked for our purposes.

---

## Per-Class Deep-Dive Table

| Class | Instance-specific evidence | Open-source gold solver | NL-renderable? | Anytime curve? | LLM results | Contam. risk |
|---|---|---|---|---|---|---|
| **Max-SAT / WPMS** | MaxSAT Evaluations: rotating winner; SATLike (IJCAI 2018), HistLS (2025) | RC2, MaxHS | Moderate (constraint stories) | Yes — SLS ECDF quality curve; Anytime MaxSAT (FMCAD 2019) | BeyondBench (ICLR 2026): poor on hard instances | Low (generated at clause/var ratio ~4.26) |
| **PDDL Planning** | IPC 2023: IBaCop2 per-instance portfolio; FD Stone Soup sequential | FastDownward (GPL), IBaCop2 | Excellent ("move block A to shelf B") | Yes — satisficing planners improve quality | PlanBench (NeurIPS 2022): GPT-4 fails medium Blocksworld | Medium (IPC domains are published) |
| **MAPF** | EECBS vs CBS: reverses by map/density; live tracker | EECBS (MIT), LaCAM | Moderate ("warehouse robots") | Yes — EECBS bounded-suboptimal | Not benchmarked | Low (synthetic seeded maps) |
| **MILP** | SCIP vs Gurobi per-instance variation; ML branching outperforms | SCIP (Apache), HiGHS | Hard (numerical precision) | Yes — incumbent/bound gap improves | Not benchmarked | Low for generated instances |
| **QBF** | QBFEVAL: CAQE vs DepQBF vs RAReQS | CAQE (MIT) | Very hard (quantifier semantics) | Not naturally anytime | Not benchmarked | Low |
| **Open Shop (≥3 machines)** | No polynomial rule (Gonzalez & Sahni 1976) | OR-Tools CP-SAT | Good (any-order factory routing) | Yes — CP-SAT progressive | Not benchmarked | Low (less famous than job-shop) |

---

## Graph Problems (Dedicated Section — Mary's Addendum)

### Framing
Key axes for each graph problem: (a) Is heuristic choice genuinely instance-specific, or just computationally expensive? (b) Which random graph model produces the hardest instances? (c) Is there an anytime solver with a clear quality curve?

### Graph Coloring / Chromatic Number

**NP-hardness:** NP-complete (Karp 1972); inapproximable within n^{1−ε} (Zuckerman 2007).

**Instance-specific?** Strongly. DIMACS COLOR challenge (1993): DSATUR (Brélaz 1979) dominates sparse graphs; RLF (Leighton 1979) dominates dense; tabu search (Galinier & Hao 1999) wins near-threshold random graphs; ZykovColor (SAT-based, 2021) wins Erdős-Rényi at hardness threshold. No single heuristic covers all DIMACS families.

**Random graph models:** G(n,p) with p chosen so E[χ(G)] hits target k — hardest near the transition where χ(G) jumps from k to k+1. Planted-solution models (hide k-coloring, add random edges to saturation) give clean gold. Erdős-Rényi is the standard; Barabási-Albert power-law graphs have different hardness profiles (DSATUR performs relatively better there).

**Anytime?** Yes. Tabu search reduces k progressively; ZykovColor does incremental bottom-up (start at upper bound, reduce by 1 per iteration). Quality metric = current best k (monotonically decreasing is the objective).

**NL-renderable?** Excellent — zero precision loss. "Assign each county a color so no two neighboring counties share the same color, using as few colors as possible." Map coloring is the canonical NL framing.

**LLM results?** BeyondBench (ICLR 2026) includes graph coloring: poor on hard instances with contamination guarantee (>10^15 unique instances per task). Risk: LLMs may recall DSATUR. The instance-specific signal is *which search strategy to use after initialization*, not the initialization itself.

**Gold:** ZykovColor, incremental Kissat SAT encoding, Brelaz exact variant.

---

### Treewidth / Elimination Ordering (PACE Competition)

**NP-hardness:** NP-complete (Arnborg, Corneil, Proskurowski 1987). FPT in k (Bodlaender 1996).

**Instance-specific?** Strongly. PACE 2016 (first challenge, 100s timeout): Tamaki (branch-and-bound + balanced separators) solves 199/200; Bodlaender & van der Zanden (balanced separators + DP) solves 173/200; SAT-based submission (Bannach et al.) solves 166/200. Different strategies dominate on different structural graph families.

**Random graph models:** PACE uses boosted real-world instances (social, road networks). Erdős-Rényi at specific densities also hard; real-world graphs with near-tree structure are easiest.

**Anytime?** Yes — branch-and-bound with upper-bound initialization can be stopped at any point.

**NL-renderable?** Poor. "Find a tree decomposition of minimum width" requires graph theory background. Very hard to frame as a compelling optimization story without losing the computational structure. **This is the key weakness for our use case.**

**Gold:** Tamaki's PACE 2016 winner (C++, open source at pacechallenge.org/2016); also htd.

---

### Maximum Clique / Maximum Independent Set

**NP-hardness:** MaxClique ≡ MaxIS; both NP-hard and inapproximable within n^{1−ε}.

**Instance-specific?** Yes. Phase transition in MaxClique on G(n,p) near specific edge densities (Shida 2007, arXiv:0707.2853 — analogue of the SAT phase transition). Dense graphs: bound via coloring number (chromatic number bounds clique); sparse graphs: adjacency enumeration (Bron-Kerbosch); planted clique of size ~√n: spectral methods. Different algorithms dominate different regions.

**Random graph models:** G(n, 1/2) has ω(G) ≈ 2 log₂ n deterministically — the gap between the greedy lower bound and the true maximum is the hard region. Planted clique (hide clique of size k between log n and √n, add random edges): clean gold = planted clique size.

**Anytime?** Yes — MaxCliqueDyn and Bron-Kerbosch variants improve best-found clique size monotonically. GRASP also anytime.

**NL-renderable?** Good. "Find the largest group of people in this social network where everyone knows each other." Social network / team selection framing is intuitive.

**LLM results?** Not systematically benchmarked. Risk: greedy degree-based recipe may be recalled.

**Gold:** MaxCliqueDyn (C++), Cliquer, MACE — all open source.

---

### Subgraph Isomorphism

**NP-hardness:** NP-complete (contains Hamiltonian cycle detection as special case).

**Instance-specific?** Very strongly. McCreesh et al. ("When Subgraph Isomorphism is Really Hard, and Why," JAIR 2018): difficulty is *not* predicted by size; Glasgow fails 51 instances while VF2 fails 1,879 of the same set; RI/VF3 >> Glasgow on easy instances. Solver complementarity is the norm.

**Random graph models:** G(n,p) for both pattern and target; hard instances generated by controlling pattern-to-target size ratio and edge density. McCreesh et al. provide a hardness-controlled generator with predictable hard/easy regions.

**Anytime?** Not naturally — this is a decision problem. The optimization variant **Maximum Common Induced Subgraph (MCIS)** is anytime with partial credit = size of the largest common subgraph found.

**NL-renderable?** Good. "Does this molecular interaction motif appear in this larger protein network?" Pattern matching in biology/chemistry is intuitive.

**Gold:** Glasgow Subgraph Solver (MIT, github.com/ciaranm/glasgow-subgraph-solver). Supports MCIS.

**Key weakness:** The decision variant lacks natural partial credit; the MCIS variant is the right form for our use case but is less studied.

---

### Max-Cut

**NP-hardness:** NP-hard. Goemans-Williamson (1995) gives 0.87856 approximation via SDP + hyperplane rounding. Optimal inapproximable beyond GW ratio under UGC (Khot, Kindler, Mossel, O'Donnell).

**Instance-specific?** Yes. GW is a universal lower bound but Burer-Monteiro non-convex SDP and simulated annealing often achieve >99% optimal on structured instances where GW gives ~88%. Dense near-bipartite graphs vs. sparse expanders require fundamentally different approaches. Quantum-classical hybrid achieves ~99% average on 3-regular graphs — strong evidence that instance structure matters.

**Random graph models:** G(n,p) Erdős-Rényi; planted bisection (two halves, sparse inter-cuts — clean gold = bisection size); Barabási-Albert (power-law, different hardness profile). Planted bisection models give the cleanest procedural generation with known near-optimal.

**Anytime?** Yes — simulated annealing, tabu, Burer-Monteiro all improve cut size monotonically over time.

**NL-renderable?** Good. "Partition towns into two groups to maximize the number of roads connecting the two groups." Telecommunications network partitioning also works.

**Gold:** SCIP, HiGHS (open source exact); Gurobi (commercial).

---

### Minimum Feedback Vertex Set / Steiner Tree / Graph Bandwidth

**MFVS:** NP-hard on directed graphs; undirected: FPT in solution size. Anytime via branch-and-bound. NL: "Break all deadlock cycles in this dependency network by removing the minimum number of processes." Gold: SCIP ILP.

**Steiner Tree:** NP-hard (Karp 1972 original 21); best known approximation 1.39 (Robins-Zelikovsky 2005). Anytime via Variable Neighborhood Descent (VND). NL: "Find the cheapest sub-network connecting all customer locations." SteinLib benchmark (DIMACS-style). Gold: Dreyfus-Wagner DP for small terminal sets; Gurobi for general.

**Graph Bandwidth:** NP-hard; no PTAS under ETH (Blache et al.). **Weakest graph candidate** — no natural anytime property, unintuitive NL framing ("number all nodes 1..n so adjacent get close numbers"), no strong PACE/DIMACS competition backing. Branch-and-bound with SDP lower bound exists but rarely studied as an anytime solver.

**Assessment for our use case:** MFVS and Steiner Tree are legitimate NP-hard problems with instance-specific difficulty, but graph coloring, max clique, and max-cut have stronger anytime curves, more intuitive NL framings, and cleaner partial-credit metrics. Bandwidth should be deprioritized.

---

## Novel Candidates

**Weighted CSP / MaxCSP:** Constraint graph structure determines which propagation (AC-3 vs. MAC) and search (CBFS, LDS, lazy clause generation) wins — strongly instance-specific. Anytime via branch-and-bound with soft constraint cost function. NL-renderable as configuration/scheduling problems. Gold: Mini-CP, Choco (both open source). Lower LLM training exposure than SAT/planning. The "algorithm selection for CSP" literature (ISAC, LLAMA) explicitly shows per-instance selection is critical.

**Orienteering Problem (OP):** "Visit as many high-value sites as possible within a time/distance budget." Instance-specific: dense geographic clusters vs. scattered sites require different beam widths and savings algorithms. Better than TSP because *which nodes to visit* is instance-specific, not just the route order. OR-Tools handles OP; LKH3 is anytime. Contamination risk lower than TSP.

---

## Ranked Recommendations

### 1. Weighted Partial Max-SAT at Phase Transition

**Rationale:** MaxSAT Evaluation competition data is the strongest evidentiary base. SATLike wins random/crafted instances; RC2 wins industrial — no single winner. No dominant LLM recipe: DPLL/CDCL don't translate to the instance-specific local search choices needed for WPMS, so the memorized-recipe failure mode is avoided. SLS gives a clean anytime quality curve via ECDF analysis. Gold via RC2 or MaxHS (minutes for 100–500 variable instances at clause/variable ratio ~4.26). Partial credit = weight of unsatisfied soft clauses (continuous and meaningful). NL rendering: "a project has hard requirements and prioritized soft preferences; satisfy as many preferences as possible."

**Key weakness:** NL surface is less vivid than map coloring. A domain narrative wrapper is required to make it compelling to a human reader. The term "clause" is technical.

### 2. Graph Coloring (Erdős-Rényi at Hardness Threshold)

**Rationale:** Best NL surface of all candidates — map coloring is universally intuitive with zero precision loss. DIMACS COLOR provides decades of solver evidence confirming per-instance variation (DSATUR vs. tabu vs. ZykovColor: winner depends on graph density). BeyondBench (ICLR 2026) confirms LLMs perform poorly on hard generated instances with contamination resistance. Progressive k-reduction gives a clean quality curve.

**Key weakness:** DSATUR is a textbook recipe LLMs may recall. The instance-specific metacognitive signal is in the *search strategy choice after initialization*, which requires genuine multi-turn behavior to surface and may be harder to elicit than the planning/scheduling variants.

### 3. Open Shop Scheduling (≥3 Machines)

**Rationale:** No Johnson's-rule equivalent for 3+ machines — confirmed NP-hardness with no known polynomial recipe (Gonzalez & Sahni 1976). Structurally related to our existing coupled job-shop codebase, reducing implementation cost. OR-Tools CP-SAT provides exact gold in minutes for moderate instances. NL-renderable as factory scheduling ("each job must visit all facilities in any order; minimize total completion time"). Lower LLM training exposure than standard job-shop.

**Key weakness:** Moderate contamination risk (scheduling is a common OR textbook topic); anytime quality curve is less smooth than tabu-based approaches.

---

## Open Questions

1. **DSATUR recipe recall test:** Our TSP/job-shop experience shows frontier models recall named heuristics. Do models recall DSATUR + local search for graph coloring? Needs a 1-turn empirical test on Gemini 3 before committing.
2. **MaxSAT NL surface quality:** Can WPMS be made compelling in NL without losing hardness properties? Requires a domain narrative iteration.
3. **Gold feasibility sizing:** For WPMS and open shop, what instance sizes keep RC2/OR-Tools tractable under 5 minutes? Needs a sizing spike analogous to the job-shop 3x4 spike.
4. **MCIS as subgraph optimization variant:** Maximum Common Induced Subgraph is anytime with partial credit. Glasgow supports it. Quick feasibility check warranted.
5. **MAPF NL surface:** Could "disaster rescue coordination" framing make MAPF compelling enough to justify its strong per-instance solver variation?

## Learnings

**Approach:** Used the Algorithm Selection Problem literature (SATzilla, IBaCop2, PACE) as the evidentiary backbone. This was the right call — solver competition data is the strongest available evidence for per-instance heuristic variation, and it's directly citable.

**What a future agent will get wrong:** Equating "NP-hard" with "instance-specific." The correct filter is: *does a solver competition show a rotating winner across instances of the same problem class?* TSP and job-shop are NP-hard but have dominant memorized recipes. This distinction (Tier 1b vs. Tier 2) is the key finding.

**What to believe to continue this work:** Graph coloring at the hardness threshold is strongest if NL surface matters most. Weighted Partial Max-SAT is strongest if mathematical rigor and clean anytime curves matter most. Open shop scheduling is fastest to implement given the existing codebase. **Before implementing any of these, run a 1-turn recipe-recall test:** give Gemini 3 a hard instance of the candidate problem and see if it recalls a named heuristic and applies it in one reasoning pass. If yes → the class is Tier 1b, reject it.

---

resulted in [[task_1776327296747sj4]]
