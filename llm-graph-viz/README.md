# llm-graph-viz — A Benchmark for LLM Graph Serialization

**Question.** When an LLM needs to reason about a non-trivial directed graph with cross-cutting edges, *which text/image format minimizes reasoning error per token*?

This benchmark compares eight candidate graph serializations (ASCII, Mermaid, adjacency footers, tree-cover, 2D ASCII layout, PNG, raw JSON) across structural / path / neighborhood / edge-count / invariant questions, three graph shapes (tree / mid-arboricity / high-arboricity), and multiple frontier models.

The benchmark is **derived from real measurements** on a 465-node zettelkasten (`voicetree-public` world-model), already run end-to-end with lossless roundtrip verification. See [`results/bf-191-bf-192.md`](results/bf-191-bf-192.md) for the one completed row and the upstream commits that produced it.

## Who should care

- **Researchers** publishing on "LLMs + graph reasoning". The format axis is usually held fixed (commonly as ASCII-or-Mermaid); this benchmark puts the format on the x-axis and asks whether it matters. It appears to matter a lot — the format spread on edge fidelity alone is ~20 percentage points on the measured fixture, and the token cost spread is ~6×.
- **Engineers building agent-readable tools** (graph visualizers, dependency-graph exporters, IDE integrations). The picks you're defaulting to — `tree`-style viewers, Mermaid sources, JSON dumps — have different failure modes against agent consumers than human consumers.
- **Anyone designing an LLM prompt that contains a graph.** Non-obvious result: the "pretty" format for humans (inline ASCII arrows) is the worst format on edge fidelity for agents, and the "lossless" format for pipelines (raw JSON) is not necessarily the best on token cost. A cheap structural reframe — tree-cover, or ASCII + path-ID footer — beats both for many queries.

## Candidate formats (A–H)

| Tag | Format | One-liner |
|---|---|---|
| A | Inline ASCII tree with `⇢ title` arrows | The `tree`-style viewer format. Lossy baseline. |
| B | Mermaid source | Structurally lossless; poor stream-locality for LLMs. |
| C | ASCII tree + `[Cross-Links]` footer | Shipped lossless-emit format; path-ID footer restores fidelity. |
| D | Hybrid A+C | Inline arrows + footer. Best ergonomics, highest maintenance. |
| E | Arboricity-bounded tree-cover | Spine + k cover forests. Lossless AND edge-co-located. |
| F | `graph-easy` / `dot-to-ascii` (Sugiyama 2D) | Classical ASCII layout. 2D placement, not token adjacency. |
| G | PNG rendered by Cytoscape/GraphViz | Read multimodally. Bypasses the text-format debate entirely. |
| H | Raw JSON state dump | Precision ceiling for exact-equality queries. |

Formats C, E, and H are the current local wins on *emit*, *assert-cheap*, and *assert-exact* respectively. The benchmark exists to check how robust those wins are off the original fixture.

## Quick numbers (one fixture, one run — full table in `results/`)

Measured on a real 465-node zettelkasten (world-model; N=465, E=476, arboricity = 3):

| Format | Edge fidelity | Token cost vs A | Edges co-located? |
|---|---:|---:|---|
| A — ASCII lossy | 79.6% | 1.0× | inline |
| B — Mermaid | 82.6% | 0.7× | no (mean 957-line gap src↔edge) |
| C — ASCII + footer | 98.1% (100% on rendered subgraph) | ~3.2× | partial (tree inline, footer distant) |
| E — Tree-cover | 100% | ~4.4× | inline, every edge |
| H — JSON | 100% (by construction) | ~12× | trivially co-located (per-node block) |

Upstream provenance: internal voicetree commits `f7042f61` (format C implementation, BF-191) and `e9c2d49f` (format E implementation + arboricity, BF-192). Those SHAs are citations for the original work; the runs happened against a private vault not bundled with this benchmark.

## Getting started

```
git clone <this-repo>
cd llm-graph-viz
pnpm install   # or npm install — only dev deps
```

Look at:
1. [`design.md`](design.md) — the full experiment design (IVs / DVs / question set / scoring).
2. [`fixtures/`](fixtures/) — the three reference graphs as adjacency JSON.
3. [`formats/tree-20/`](formats/tree-20/) — what each format A–H actually looks like on the smallest fixture. Read these first to calibrate intuition.
4. [`reproduce.md`](reproduce.md) — end-to-end repro instructions.
5. [`results/bf-191-bf-192.md`](results/bf-191-bf-192.md) — the one completed row.

## Status

- **Design:** complete.
- **Fixtures:** 3 reference graphs, structural-only adjacency (no proprietary content).
- **Renderers:** A (lossy ASCII), B (Mermaid), C (ASCII + footer), E (tree-cover), H (JSON passthrough). F (`graph-easy`) and G (PNG) are specified in `design.md` but not included — they're thin wrappers over external tools (`graph-easy` CPAN module; Playwright+Cytoscape or GraphViz `dot -Tpng`).
- **Parsers / scorers:** ASCII-footer parser + arboricity reference implementation, both ported from the internal vt-graph work that produced the initial row.
- **Question set:** 30 questions + rubric. **No LLM run yet — that's the next task.**

## Non-goals

- **Not** a claim that any single format is always best. The point of the benchmark is that the answer is shape-dependent (arboricity, size, query mix) and should be measured rather than assumed.
- **Not** a replacement for a proper graph database when exact equality is the goal. Format H (JSON) wins that use case by construction; the interesting comparisons are on the lossy-but-cheap end.
- **Not** a human-readability benchmark. Several format choices (e.g., footer-based lossless formats) are bad for humans and good for agents. If your consumer is a human, you're off-distribution.

## Citation

If you use this benchmark, please cite:

```
@misc{voicetree-llm-graph-viz-2026,
  author       = {Masson, Manu},
  title        = {llm-graph-viz: A benchmark for LLM graph serialization},
  year         = 2026,
  publisher    = {GitHub},
  howpublished = {\url{https://github.com/voicetree/voicetree-evals/tree/main/llm-graph-viz}},
}
```

The upstream roundtrip + arboricity work is at commits `f7042f61` and `e9c2d49f` on `voicetree-public`.

## License

MIT. See [`LICENSE`](LICENSE).
