# Fixtures

Three reference graphs, generated deterministically by `scripts/generate-fixtures.ts`. All content is synthetic — no proprietary material.

| File | N | E | Arboricity (LB / UB) | Shape |
|---|---:|---:|---|---|
| `tree-20.json` | 20 | 5 | 1 / 1 | Small project-docs tree with 5 cross-references |
| `kanban-100.json` | 100 | 152 | 6 / 11 | 12-node K₁₂ hub clique + sparse tail |
| `world-model-like-465.json` | 465 | 483 | 3 / 3 | Zettelkasten calibrated to BF-192 world-model signature |

The `LB` (Nash-Williams lower bound) is tight; the `UB` (simple forest-greedy) can overshoot on dense subgraphs (see `results/bf-191-bf-192.md` §2.1). Use `LB` for arboricity-bucket classification.

## Schema

Each fixture is a JSON file with this structure:

```json
{
  "nodes": [
    {"id": "<stable string id>", "title": "<human title>", "parent": "<id> | null"}
  ],
  "edges": [
    {"src": "<id>", "tgt": "<id>", "label": "<optional edge label>"}
  ]
}
```

Invariants enforced by `scripts/graph.ts`:

- `id`s are unique.
- Every `parent` resolves.
- The parent relation is acyclic (the primary tree is a forest).
- Every edge's `src` and `tgt` exist in `nodes`.
- No self-edges in `edges`.

## Why three fixtures, not more

- Small-tree (tree-20) exists so a human can read the entire graph in one glance, which is the only way to debug the rubric and catch scorer bugs.
- Medium-high-arboricity (kanban-100) tests formats against *adversarial* structure — the tree-cover format E is most interesting at a(G) approaching 6 because BF-192's analysis predicted the crossover near there.
- Large-world-model-like (world-model-like-465) exists to test at realistic-zettelkasten scale (~500 nodes, a=3). This is a direct structural copy of the BF-192 measured fixture, with synthetic content in place of the original AGI-predictions notes.

Adding more fixtures is a straightforward PR — see `scripts/generate-fixtures.ts`.

## What the fixtures do *not* cover

- **Multi-root graphs.** All three fixtures have a single root (`proj`, `root`, `wm`). A multi-root vault is a valid zettelkasten shape that none of these test. Adding a fourth fixture for this case is open work.
- **Directed cycles in cross-edges.** The world-model fixture has some bidirectional pairs (which contain 2-cycles). Larger cycles (length ≥ 3) are not injected — if they appear, they're artifacts of the PRNG, not deliberate tests.
- **Labeled edges beyond a fixed vocabulary.** The kanban fixture uses `blocks | related-to | duplicate-of`; the tree-20 fixture uses `calls | requires | reads | uses | documents`. A real vault has open-vocabulary labels. Format renderers should treat labels as opaque strings.
