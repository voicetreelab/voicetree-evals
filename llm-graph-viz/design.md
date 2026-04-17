# Experiment design — llm-graph-viz

## 1. The research question

> When an LLM is asked a structural question about a non-trivial directed graph with cross-cutting edges, which serialization minimizes reasoning error per token?

The test is **per-query reasoning accuracy**, not raw compression ratio or roundtrip fidelity. A format that is lossless but too large to fit in context has score 0 on every question it can't be prompted with. A format that is small but ambiguous (unresolved references, colliding titles) loses on any query that requires path-exact answers.

## 2. Variables

### 2.1 Independent variables

| IV | Levels |
|---|---|
| **Format** | A (lossy ASCII), B (Mermaid), C (ASCII + footer), D (hybrid A+C), E (tree-cover), F (`graph-easy` / `dot-to-ascii`), G (PNG, multimodal), H (JSON) |
| **Graph size** | small (20 nodes), medium (100 nodes), large (465 nodes) |
| **Arboricity bucket** | low (a ≤ 3), mid (4 ≤ a ≤ 6), high (a ≥ 7) |
| **Model** | Claude Opus 4.7, Claude Sonnet 4.6, Gemini 2.5 Pro, GPT-5 |

The fixtures pair size × arboricity on the diagonal: `tree-20` is (small, low=1); `kanban-100` is (medium, mid=6); `world-model-like-465` is (large, low=3). Off-diagonal combinations are not in the initial benchmark — justified by budget, and by the fact that arboricity scales sub-linearly with size for natural graphs, so (large, high) fixtures are rare in the wild.

### 2.2 Dependent variables (measured per (format × graph × question × model) cell)

| DV | Definition |
|---|---|
| **Node-recall precision** | Of nodes the model names in its answer, fraction that exist in the ground-truth graph. |
| **Edge-recall precision** | Of (src, tgt) pairs the model names, fraction that exist as directed edges in ground truth. |
| **Edge-recall recall** | Of ground-truth edges whose enumeration is required by the question, fraction the model names. (Only meaningful for *enumeration* and *count* questions.) |
| **Token cost (input)** | Tokens in the formatted graph, by the model's own tokenizer. |
| **Token cost (output)** | Tokens the model emits on the answer. |
| **Wall-clock** | End-to-end response time (s). |
| **Fabrication rate** | Fraction of named nodes or edges that do not exist in ground truth. Complement of precision, surfaced separately for failure-mode analysis. |
| **Refusal rate** | Fraction of prompts the model declines / stalls / answers "I don't know" without a best-guess. |
| **Score** | Per-question score from rubric in §4; in [0, 1]. |

**Primary headline metric.** `score / input_tokens`, averaged across the question set, per (format × graph × model). This is the "accuracy per token" the research question asks about.

### 2.3 Controls / confounders

- **Prompt scaffolding** is held fixed across formats. The system prompt is identical; only the format of the graph payload changes. No format-specific hints ("this is a tree-cover format with k=3 forests"). Formats with in-band metadata (the `═══ COVER FOREST k ═══` banner in E, the `[Cross-Links]` header in C) count those bytes toward token cost.
- **Legend** is allowed but must be ≤ 20 lines and counted in input tokens. It's part of the format. Keep legends in `formats/<fixture>/*.legend.md` for auditability.
- **Temperature** fixed at 0.0 where settable; otherwise documented (e.g., GPT-5 current API defaults).
- **Tokenizer** = the model's own tokenizer where public. For closed tokenizers, approximate with `bytes / 4` and mark the row.
- **Sampling** = single run per cell for the initial pass. Re-run at N=3 in a follow-up to bound variance; the design assumes low within-cell variance at T=0 and documents this assumption.

## 3. Question set (30 questions)

Structure: 6 question types × 5 questions each = 30. Each question is answerable from the graph alone; no external knowledge required. Each question has a *class* that determines the scoring rubric (§4).

Questions are written *graph-shape-parametric*: the same question template fills in concrete node IDs per fixture. A question like "list descendants of X" instantiates as "list descendants of `n17`" on `tree-20` and "list descendants of `governance-backlog`" on `kanban-100`. Concrete per-fixture instantiations live in [`questions/instantiated.md`](questions/instantiated.md).

### 3.1 Structural queries (Q1–Q5) — "what shape is this graph?"

These are whole-graph invariants, computed from the full adjacency. They reward completeness.

| Q | Template | Class |
|---|---|---|
| Q1 | How many nodes total? | exact-count |
| Q2 | How many directed edges (non-self)? | exact-count |
| Q3 | What's the maximum out-degree, and which node achieves it? | argmax+value |
| Q4 | Is the graph a DAG? If not, name one cycle. | bool+witness |
| Q5 | How many connected components are there (treating edges as undirected)? | exact-count |

### 3.2 Path queries (Q6–Q10) — "can you trace from A to B?"

Reward: single concrete path, correctness of each hop, total length. Penalize spurious hops heavily (see §4.3).

| Q | Template | Class |
|---|---|---|
| Q6 | Find any directed path from node X to node Y. Name each node on the path. | path |
| Q7 | What's the shortest directed path from X to Y? (By hop count.) | path+optimal |
| Q8 | Is Y reachable from X? yes/no. If no, what about the reverse? | bool+bool |
| Q9 | Find the longest acyclic simple path starting at X. | path+optimal (NP but small graphs; answer on small fixture only) |
| Q10 | For two specified nodes X, Y: what's their lowest common ancestor in the primary tree? (If graph isn't a tree, use the containment hierarchy.) | node |

### 3.3 Neighborhood queries (Q11–Q15) — "what's near X?"

Reward: complete enumeration of a local set.

| Q | Template | Class |
|---|---|---|
| Q11 | Name all direct (1-hop) out-neighbors of X. | enumeration |
| Q12 | Name all direct in-neighbors of X. | enumeration |
| Q13 | Name all nodes within 2 hops of X (either direction). | enumeration |
| Q14 | List all descendants of X in the tree / containment hierarchy. | enumeration |
| Q15 | Are X and Y siblings in the primary tree? (share a parent) | bool |

### 3.4 Edge-count queries (Q16–Q20) — "quantify the edge mix"

These probe whether the format preserves the cross-cutting edges (the ones that break pure tree rendering).

| Q | Template | Class |
|---|---|---|
| Q16 | How many cross-folder / cross-subtree edges are there? | exact-count |
| Q17 | How many edges go *between* the subtree rooted at X and the subtree rooted at Y? | exact-count |
| Q18 | How many self-contained subtrees (no outgoing cross-edges to their complement) does the graph have among its top-level containers? | exact-count |
| Q19 | What's the ratio of cross-edges to total edges? (round to nearest 0.05) | fractional |
| Q20 | Name a node with zero outgoing edges and a node with zero incoming edges. | two-node |

### 3.5 Invariant queries (Q21–Q25) — "does a property hold?"

Global yes/no with a requested witness. Tests whether the format supports proof-level reasoning (not just enumeration).

| Q | Template | Class |
|---|---|---|
| Q21 | Is every leaf in the primary tree also a sink in the edge graph? If not, name a counterexample. | bool+witness |
| Q22 | Does node X participate in any cycle? If yes, name one. | bool+witness |
| Q23 | Is there any pair of nodes with edges in both directions? (bidirectional) | bool+witness |
| Q24 | What's the arboricity bound — minimum forest count to cover all edges? (Accept the greedy upper bound as correct.) | exact-count |
| Q25 | Are there any duplicate-titled nodes in different folders? (Tests whether the format preserves path uniqueness.) | bool+witness |

### 3.6 Refactor / edit queries (Q26–Q30) — "emit a command"

These test *emit* use cases. The model is given a format and asked to produce a commandlet referring to graph IDs.

| Q | Template | Class |
|---|---|---|
| Q26 | Produce a list of `rm <id>` commands for all sinks (nodes with zero out-degree). | command-list |
| Q27 | Produce a list of `mv <src> <new-parent>` commands to flatten the deepest branch by one level. | command-list |
| Q28 | Produce an `add-edge <src> <tgt>` command that would connect two currently-unconnected components. (Name a valid pair.) | command |
| Q29 | Produce an `audit <id>` command for each node whose out-degree exceeds the graph's mean. | command-list |
| Q30 | Given a target node X, produce a JSON object listing X's full parent chain and all its out-edges. | structured-emit |

## 4. Scoring rubric

### 4.1 Per-class scoring

| Class | Score definition |
|---|---|
| **exact-count** | 1 if answer matches ground truth exactly; 0.5 if within ±10% relative; 0 otherwise. |
| **argmax+value** | 0.5 for correct argmax; 0.5 for correct value; min of both scores if asked for both. |
| **bool** | 1 if matches ground truth; 0 otherwise. |
| **bool+witness** | 0.5 for correct boolean; 0.5 for a correct witness when required. If the boolean is wrong, the witness is 0. |
| **bool+bool** | 0.5 per sub-answer. |
| **path** | 1 if every hop in the named path is a real edge, in order, from X to Y; 0 if any hop is fabricated or out-of-order; 0 if path doesn't reach Y. |
| **path+optimal** | As `path`, but with a 0.5× penalty if the path is valid but longer than optimal. |
| **node** | 1 if correct; 0 otherwise. |
| **two-node** | 0.5 per node; each scored independently (must exist and satisfy the stated property). |
| **enumeration** | F1 of named set vs ground-truth set. Precision = names that are correct / total names; recall = correct names / ground-truth size; F1 = harmonic mean. |
| **fractional** | 1 if within ±0.05 of ground truth; 0.5 if within ±0.1; 0 otherwise. |
| **command-list** | F1 of the commands as a set of tuples (cmd, args). Order-insensitive. |
| **command** | 1 if the emitted command is valid (arguments are real node IDs) and achieves the stated effect; 0 otherwise. |
| **structured-emit** | JSON must parse; parent chain exact; out-edges scored as `enumeration` F1; average of the three sub-scores. |

### 4.2 Fabrication penalty

A named node or edge that does not exist in ground truth costs:
- `enumeration`: already priced into F1 precision — no extra penalty.
- `path` / `command`: disqualifies the whole answer (score 0).
- `bool+witness`: disqualifies the witness (score 0.5 from bool only).

The rationale: fabricated adjacencies are the dominant harm mode in agent workflows. Penalize them asymmetrically from partial recall.

### 4.3 Refusal scoring

A clean refusal (`"I cannot answer from this context"`) scores 0 but is tracked separately in the refusal-rate DV. A stalled / meta / "you didn't give me enough information" answer that does not name a concrete guess also scores 0 but counts as a refusal. A low-confidence guess that names concrete answers is scored normally — it's the confident guess that matters, since that's what downstream code consumes.

### 4.4 Aggregation

Per (format × graph × model):
- `mean_score` = average of 30 per-question scores.
- `mean_score_per_1k_input_tokens` = `mean_score / (mean_input_tokens / 1000)`. **This is the headline metric.**
- `fabrication_rate`, `refusal_rate` reported alongside.

Per format (aggregating across graphs and models):
- Report `mean_score` and `mean_score_per_1k_tokens` with 95% bootstrap CI.

## 5. Sanity checks (before running on new models)

1. **Ground-truth self-consistency.** For each fixture, confirm the adjacency matches what the renderers parse back. `pnpm run verify-fixtures` enforces this.
2. **Known-answer smoke test on one model.** Run all 30 questions on format H (JSON) with one frontier model. H should score ≥ 0.85 on `exact-count` / `enumeration` / `bool`. If it doesn't, the rubric or fixtures are buggy — don't compare across formats yet.
3. **Tokenizer alignment.** Verify that the input-token count returned by the API matches what you measure locally. Drift here invalidates `score / token` comparisons.

## 6. What this design does *not* control for

- **Prompt language.** All prompts are English. Non-English graph labels (common in multilingual corpora) may break format-specific tokenizers unevenly.
- **Model-specific post-training.** Some frontier models have been specifically trained on Mermaid or DOT; others have not. The benchmark measures the joint distribution (format-training × format-prompt) rather than the clean format effect.
- **Image quality for format G.** Rendering choices (label size, edge curvature, layout algorithm) affect multimodal performance. Document the render settings in `scripts/render-png.ts`; rerunning with different settings is expected to move the G row.
- **Legend placement.** Format-level legends (explaining `⇢` vs `⇗`) live above the graph. Placing them below or inline probably matters and isn't tested.

## 7. Suggested follow-up studies

1. **Arboricity gate replication.** The internal BF-192 result found that `E` wins lossless-and-co-located *only when a(G) ≤ 3*. Replicate on fixtures spanning `a ∈ {1, 3, 6, 9}` and measure the crossover precisely.
2. **Short-ID variant for E.** The tree-cover format uses full path IDs. Measure the `score / token` gain from replacing them with shortest-unique-suffix IDs. The internal estimate is ~60% token reduction at 0% fidelity loss on world-model; validate empirically.
3. **Image+JSON duo.** Format G (PNG) is already multimodal-ready. Pair it with H (JSON) for exact-equality queries and measure whether the duo dominates the text formats on the joint query mix.
4. **Scaling law.** Re-run on 1k and 2k-node fixtures. Tree-cover's token multiplier is approximately linear in `a(G) × N`; mermaid and ASCII-lossy are ≈ 1.1× in N. There may be a graph-size crossover where mermaid wins regardless of the arboricity bucket.

## 8. Relation to prior upstream work

The format choices mirror two internal empirical studies in the voicetree codebase — **BF-191** (which shipped format C in `vt-graph view`) and **BF-192** (arboricity + tree-cover analysis). Those studies motivated formats C and E by measuring fidelity + co-location on one real fixture; this benchmark generalizes the measurement to cover query accuracy, multiple fixtures, and multiple models. See [`results/bf-191-bf-192.md`](results/bf-191-bf-192.md) for the reproduced row and upstream commit SHAs.
