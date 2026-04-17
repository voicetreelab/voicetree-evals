# Reproducing the benchmark

## 0. Prerequisites

- Node.js ≥ 20 (for `tsx` + modern ESM). Tested on 22.20.0.
- `pnpm` ≥ 9 (or `npm` — just replace `pnpm` with `npm` below; both work).
- ~10 MB disk for fixture renderings.
- An LLM API key for whichever model(s) you want to evaluate (Step 4 only; Steps 1–3 are offline).

## 1. Install and regenerate fixtures

```bash
git clone <this-repo>
cd llm-graph-viz
pnpm install
pnpm run generate-fixtures
```

Expected output:

```
tree-20                   N=  20  E=   5  a(G)=1 (LB=1, degen=1)
kanban-100                N= 100  E= 152  a(G)=11 (LB=6, degen=11)
world-model-like-465      N= 465  E= 483  a(G)=3 (LB=3, degen=3)
```

If arboricity reported here doesn't match, the PRNG seeded in `scripts/generate-fixtures.ts` is deterministic across Node versions — confirm you're on Node ≥ 20 and that you haven't patched `mulberry32`. `a(G)` values are the upper bound from the simple forest-greedy; LB is the Nash-Williams tight lower bound (see `scripts/arboricity.ts`).

## 2. Render every fixture in every format

```bash
mkdir -p formats/{tree-20,kanban-100,world-model-like-465}
for f in tree-20 kanban-100 world-model-like-465; do
  pnpm render A fixtures/$f.json > formats/$f/A-ascii-lossy.txt
  pnpm render B fixtures/$f.json > formats/$f/B-mermaid.mmd
  pnpm render C fixtures/$f.json > formats/$f/C-ascii-footer.txt
  pnpm render E fixtures/$f.json > formats/$f/E-tree-cover.txt
  pnpm render H fixtures/$f.json > formats/$f/H-json.json
done
```

Formats F (Sugiyama 2D ASCII via `graph-easy`) and G (PNG via Cytoscape or GraphViz) are not included in the repo's renderers because they depend on external tools. See §5 below for how to produce them.

## 3. Verify format-C round-trip fidelity

```bash
pnpm run parse score fixtures/tree-20.json            formats/tree-20/C-ascii-footer.txt
pnpm run parse score fixtures/kanban-100.json         formats/kanban-100/C-ascii-footer.txt
pnpm run parse score fixtures/world-model-like-465.json formats/world-model-like-465/C-ascii-footer.txt
```

Expected: `"nodeFidelity": 1, "edgeFidelity": 1, "edgePrecision": 1` on all three. If any drops, either the parser or the renderer regressed; see `scripts/parse.ts` for the scoring semantics.

## 4. Running the LLM evaluation (not yet scripted)

This is the one step not shipped in the repo. The benchmark design is in [`design.md`](design.md), the question set in [`questions/question-set.md`](questions/question-set.md). A minimal runner sketch:

```python
# pseudo-code — runner.py
import json, anthropic

fixture = json.load(open('fixtures/world-model-like-465.json'))
format_text = open('formats/world-model-like-465/E-tree-cover.txt').read()
questions = json.load(open('questions/instantiated-world-model-like-465.json'))

client = anthropic.Anthropic()
for q in questions:
    prompt = f"You will be given a graph in a custom format, then a question.\n\nGRAPH:\n{format_text}\n\nQUESTION: {q['prompt']}\n\nAnswer in the JSON schema: {q['schema']}"
    resp = client.messages.create(
        model='claude-opus-4-7',
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=2048,
        temperature=0,
    )
    score = score_response(q, resp.content[0].text)  # per §4 rubric in design.md
    print(q['id'], score, resp.usage.input_tokens, resp.usage.output_tokens)
```

Scoring code per the rubric in [`design.md`](design.md) §4.1 is not shipped — writing it is the next benchmark task. For open PRs contributing a scorer, see the repo issues tagged `scorer`.

### 4.1 Cost estimate

At Anthropic API current list prices for Claude Opus 4.7 (`$15 / M input, $75 / M output`):

- Per call on `world-model-like-465` in format E: ~24 k input + ~400 output = ~$0.39.
- Full grid (5 formats × 3 fixtures × 30 questions × 4 models): ~1 800 calls ≈ **$450**.

Sonnet 4.6 and Haiku 4.5 reduce per-call cost ~5× and ~25× respectively.

## 5. Format F and G — external tools

### 5.1 Format F — Sugiyama 2D ASCII

Use `graph-easy` (Perl CPAN module; stable since ~2008, still maintained). Produce DOT first, then pipe:

```bash
# install once
cpan -i Graph::Easy

# render a fixture
pnpm render B fixtures/tree-20.json | \
  # convert mermaid → dot (write a small shim, or use mermaid-cli to export)
  # then:
  graph-easy --from=dot --as=ascii
```

Alternative: `dot-to-ascii` (`ggerganov/dot-to-ascii`) is a lighter-weight Go tool that handles the same input. Pick based on your platform.

### 5.2 Format G — PNG

Two paths:

1. **GraphViz** (simplest, no GUI):
   ```bash
   # render dot from your fixture (write a small dot renderer) then:
   dot -Tpng fixture.dot -o fixture.png
   ```
   GraphViz's `sfdp` layout is typically best for force-directed graphs of this size.

2. **Cytoscape + Playwright** (used internally by voicetree for BF-181; higher-fidelity):
   - Start a headless Cytoscape browser page.
   - Load the graph as `elements` (one-to-one with your adjacency JSON).
   - Screenshot at 1600×1200.
   - The voicetree codebase ships a working Playwright harness (BF-181); not included here since it depends on the voicetree app shell.

Token counting for format G depends on the vision model's image-token accounting. For Claude, a 1600×1200 image is typically ~1 600 input tokens; for GPT-5, closer to ~2 200. Document whichever you use and mark the row accordingly.

## 6. Contributing new measurements

If you run the benchmark on a new model or fixture, please open a PR adding a row to [`results/`](results/). Include:

- The tokenizer version used for input-token counting (model name + date).
- The exact prompt scaffold if you deviated from the skeleton in §4.
- Temperature and any sampling settings.
- Raw responses in a `runs/<model>-<date>/` directory, not just summary numbers.

Cross-references from `results/` back to commits (git-SHA) let future readers replay without ambiguity.

## 7. Known gotchas

- **Mermaid's `-.->` arrow.** Our format B uses dashed arrows for cross-edges and solid for tree. Some Mermaid parsers break on this; if you run the mermaid fixture through a renderer that chokes, replace `-.->` with `-->` (reduces fidelity to the format's semantic distinction).
- **Token counting for format H.** Raw JSON tends to tokenize poorly because it's structured — your model's tokenizer will split on braces and quotes, inflating token count ~20% over the naive `bytes/4` estimate. Measure with the actual tokenizer before reporting `score / token`.
- **Fixture determinism.** The PRNG in `scripts/generate-fixtures.ts` is seeded with three fixed constants (`0xC0FFEE`, `0xDEADBEEF`). Changing those regenerates different-but-equally-valid fixtures. Don't do it in a PR that also reports scores — the comparison will be spurious.
- **File limits on real vaults.** The upstream `vt-graph` sets a 600-file scan limit (BF-186 found this was the binding constraint at real-vault scale). If you adapt these scripts to real corpora, expect to hit OS file-handle limits before hitting benchmark-token limits.
