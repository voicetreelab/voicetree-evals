# Format examples

For every fixture in [`../fixtures/`](../fixtures/), this directory contains pre-rendered outputs in each format the renderers support:

```
formats/
├── tree-20/
│   ├── A-ascii-lossy.txt
│   ├── B-mermaid.mmd
│   ├── C-ascii-footer.txt
│   ├── E-tree-cover.txt
│   └── H-json.json
├── kanban-100/
│   └── (same five)
└── world-model-like-465/
    └── (same five)
```

**Start with `tree-20/`.** The smallest fixture is hand-crafted and small enough to read in one sitting — every cross-edge is traceable by eye. Comparing the five renderings of the same 20-node graph is the fastest way to form intuition for the strengths and weaknesses of each format.

## What each format looks like, in one line

- **A (`A-ascii-lossy.txt`)** — `tree`-style indent layout, with `⇢ Title` inline. Pretty. Drops unresolved targets, collides on duplicate titles.
- **B (`B-mermaid.mmd`)** — Mermaid source. All nodes declared first, edges last. Lossless in principle; co-location is terrible because edge and label are separated by hundreds of lines on real fixtures.
- **C (`C-ascii-footer.txt`)** — Format A's tree *plus* a `[Cross-Links]` footer keyed by stable IDs. Lossless on the rendered subgraph. Co-location is partial — tree inline, footer distant.
- **E (`E-tree-cover.txt`)** — Spine (containment tree) + k cover forests. Every edge adjacent to its source and target labels. Lossless; highest token cost.
- **H (`H-json.json`)** — Raw adjacency JSON. Precision ceiling; no human readability at scale.

Formats D (hybrid A+C), F (`graph-easy` 2D ASCII), and G (PNG) are *not* pre-rendered because:

- **D** is trivially `A + '[Cross-Links]' footer` — concatenate `A-ascii-lossy.txt` with the footer section of `C-ascii-footer.txt`.
- **F** requires a Perl CPAN module (`graph-easy`) or a Go tool (`dot-to-ascii`); see `../reproduce.md` §5.1.
- **G** requires either GraphViz or Cytoscape-in-Playwright; see `../reproduce.md` §5.2.

## Byte-count reference

| Fixture | A | B | C | E | H |
|---|---:|---:|---:|---:|---:|
| `tree-20` | 929 | 1 719 | 1 374 | 1 961 | 2 755 |
| `kanban-100` | 15 995 | 16 519 | 26 092 | 26 769 | 29 912 |
| `world-model-like-465` | 49 828 | 105 827 | 93 590 | 98 670 | 130 663 |

Divide by 4 for an approximate input-token count — but use your actual model's tokenizer when running the benchmark. Raw JSON (H) tokenizes ~20% worse than `bytes/4` suggests because of brace/quote overhead.

## Determinism

All renderers sort children, edges, and cover forests by ID. The byte-for-byte outputs in this directory should reproduce exactly with `pnpm run generate-fixtures && pnpm render <FMT> fixtures/<fixture>.json > formats/<fixture>/<rendered>.txt`. If you get a diff, the PRNG or renderer is non-deterministic — file an issue.
