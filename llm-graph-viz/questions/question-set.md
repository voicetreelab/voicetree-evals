# Question set — 30 questions across 6 classes

This file is the authoritative source for the question templates referenced in [`design.md`](../design.md) §3. Each question is a template — it instantiates against a specific fixture by filling in concrete node references (e.g., `{X}` → `proj/backend/api/users`).

Per-fixture instantiations live in `questions/instantiated-<fixture>.json` (not yet committed — the instantiation step is part of the open scorer-implementation task; see `reproduce.md` §4).

## Section A — Structural queries (Q1–Q5)

Global invariants; reward completeness.

- **Q1** `[exact-count]` — How many nodes are there in total (including folders, subfolders, and leaves)?
- **Q2** `[exact-count]` — How many directed non-self cross-edges are there? (Do not count parent-child tree edges.)
- **Q3** `[argmax+value]` — Which node has the highest cross-edge out-degree, and what is that out-degree?
- **Q4** `[bool+witness]` — Does the cross-edge graph contain any directed cycles? If yes, name one cycle (sequence of nodes starting and ending at the same ID).
- **Q5** `[exact-count]` — How many weakly-connected components does the graph have? (Treat cross-edges as undirected and combine with tree edges.)

## Section B — Path queries (Q6–Q10)

Trace a route from A to B. Fabricated hops disqualify the answer.

- **Q6** `[path]` — Find any directed cross-edge path from `{X}` to `{Y}`. List each intermediate node. If no path exists, say `NONE`.
- **Q7** `[path+optimal]` — What is the shortest directed cross-edge path from `{X}` to `{Y}` by hop count?
- **Q8** `[bool+bool]` — Is `{Y}` reachable from `{X}` via cross-edges? Is `{X}` reachable from `{Y}`?
- **Q9** `[path+optimal]` — Starting from `{X}`, what is the longest simple (acyclic) directed cross-edge path? (Asked only on `tree-20` and `kanban-100`; NP-hard in general but small.)
- **Q10** `[node]` — For `{X}` and `{Y}`, what is their lowest common ancestor in the primary tree (parent containment)?

## Section C — Neighborhood queries (Q11–Q15)

Enumerate a local set. Scored by F1.

- **Q11** `[enumeration]` — Name every direct (1-hop) cross-edge out-neighbor of `{X}`.
- **Q12** `[enumeration]` — Name every direct (1-hop) cross-edge in-neighbor of `{X}`.
- **Q13** `[enumeration]` — Name every node within 2 cross-edge hops of `{X}` (either direction).
- **Q14** `[enumeration]` — List every descendant of `{X}` in the primary tree. (Transitive children.)
- **Q15** `[bool]` — Are `{X}` and `{Y}` siblings in the primary tree? (Share a parent.)

## Section D — Edge-count queries (Q16–Q20)

Probe whether the format preserves cross-cutting edges.

- **Q16** `[exact-count]` — How many cross-edges cross folder boundaries? (Edges whose src and tgt have different direct parents.)
- **Q17** `[exact-count]` — How many cross-edges go between the subtree rooted at `{X}` and the subtree rooted at `{Y}`? (Count both directions, no double-counting.)
- **Q18** `[exact-count]` — Among the top-level containers (direct children of the root), how many have *zero* outgoing cross-edges to any other top-level container's subtree?
- **Q19** `[fractional]` — What fraction of cross-edges cross folder boundaries? Round to the nearest 0.05.
- **Q20** `[two-node]` — Name one node with out-degree zero (a "sink" in the cross-edge graph) and one node with in-degree zero (a "source").

## Section E — Invariant queries (Q21–Q25)

Global yes/no with a witness when false.

- **Q21** `[bool+witness]` — Is every leaf in the primary tree also a sink in the cross-edge graph? If not, name a counterexample: a leaf node with at least one outgoing cross-edge.
- **Q22** `[bool+witness]` — Does `{X}` participate in any cross-edge cycle? If yes, name one.
- **Q23** `[bool+witness]` — Are there any pairs of nodes (A, B) with cross-edges in both directions? If yes, name one such pair.
- **Q24** `[exact-count]` — What is the minimum number of forests required to cover every cross-edge exactly once? (Arboricity. Accept the greedy upper bound as correct; tighter Nash-Williams LB not required.)
- **Q25** `[bool+witness]` — Do any two distinct nodes share the exact same title? If yes, name two such nodes.

## Section F — Refactor / emit queries (Q26–Q30)

Emit a commandlet. Test the format's use as a prompt for agent-driven mutations.

- **Q26** `[command-list]` — Produce a list of `rm @[<id>]` commands — one per node with zero outgoing cross-edges (all cross-edge sinks). Exclude nodes with children in the primary tree.
- **Q27** `[command-list]` — Find the deepest branch in the primary tree. Produce `mv @[<id>] @[<new-parent-id>]` commands to flatten it by one level (each grandchild becomes a child of its grandparent, preserving in-tree order).
- **Q28** `[command]` — Name two currently-unconnected weakly-connected components by giving one node from each. Emit `add-edge @[<src>] @[<tgt>]` that would merge them.
- **Q29** `[command-list]` — Compute the mean out-degree across all cross-edges. Emit `audit @[<id>]` for every node whose out-degree is strictly greater than the mean.
- **Q30** `[structured-emit]` — For target node `{X}`, emit a JSON object with shape `{parent_chain: [...], out_edges: [...]}`. `parent_chain` is the list of ancestors from root to `{X}` (inclusive, in order). `out_edges` is the list of direct cross-edge targets.

## Prompt scaffolding

All questions share the same system prompt:

```
You are a graph-reasoning assistant. You will be shown a graph representation
and asked questions about it. Do not ask clarifying questions — answer with
your best guess. Format your answer as a single JSON object matching the
schema at the end of the user message. Do not include chain-of-thought in
the JSON. Use the @[<id>] references given in the graph.
```

Per-question user-message template:

```
GRAPH (format <FMT>):

<graph text>

QUESTION: <question>

ANSWER SCHEMA: <schema specific to question class — see design.md §4>
```

The "format FMT" banner is the only format-identifying hint; the model is not told what `⇢` or `●` mean beyond what's in the graph text itself (the legend embedded in the format). This keeps the format-learning burden consistent across models.

## Per-class schema reference

Copy-paste into prompt scaffolding:

```
exact-count:        {"answer": <integer>}
argmax+value:       {"node_id": "<id>", "value": <integer>}
bool:               {"answer": true | false}
bool+witness:       {"answer": true | false, "witness": "<id or cycle list>" | null}
bool+bool:          {"a": true|false, "b": true|false}
path:               {"path": ["<id>", "<id>", ...]}
path+optimal:       {"path": ["<id>", "<id>", ...], "length": <integer>}
node:               {"node_id": "<id>"}
two-node:           {"sink": "<id>", "source": "<id>"}
enumeration:        {"ids": ["<id>", ...]}
fractional:         {"answer": <number in [0, 1]>}
command-list:       {"commands": ["<cmd>", ...]}
command:            {"command": "<cmd>"}
structured-emit:    (question-specific — see Q30)
```
