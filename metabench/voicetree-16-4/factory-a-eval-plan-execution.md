---
color: blue
isContextNode: false
agent_name: Ivan
---
# Execution — 5 Codex fan-out, budget, collision-handling

5 leaf Codex: 2 in parallel (q-gen + harness), then gate on 3-model smoke, then 3 parallel eval workers. Depth-budget clean (my 5 → all depth=0). Cost <$10 (Sonnet output dominates). One write-path overlap flagged: `harness/prompt.py` — mitigated.

## Codex fan-out diagram

```
Ivan (depth=5)
├── A-questions   [depth=0, parallel w/ A-harness]   ~30-45 min
│     writes: scripts/build_questions.py, questions.jsonl, gold/gold.jsonl
├── A-harness     [depth=0, parallel w/ A-questions]  ~45-60 min
│     writes: eval_harness/*.py, harness/prompt.py (amend), 3 smoke JSONs
│
│     │
│     ▼  GATE: user reviews 3-model smoke (parseability + feasibility)
│
├── A-eval-gemini [depth=0, parallel]                ~25 min @ 90s/row
│     writes: results/runs/gemini-flash-latest/*.json
├── A-eval-claude [depth=0, parallel]                ~25 min
│     writes: results/runs/anthropic_claude-sonnet-4-6/*.json
└── A-eval-gpt    [depth=0, parallel]                ~25 min
      writes: results/runs/gpt-5.4-mini/*.json
```

## Write-path isolation audit

| Codex | Write path | Collision risk |
|---|---|---|
| A-questions | `scripts/`, `questions.jsonl`, `gold/` | none |
| A-harness | `eval_harness/` (new), `harness/prompt.py` (amend) | **`harness/prompt.py` overlaps Ben's territory** — see mitigation |
| A-eval-* | `results/runs/{model}/*.json` only | none |

### `harness/prompt.py` collision mitigation
Ben's S1-S3 is landed (commit `336b345`). Iris is on S4 (Kaggle upload → consumes embedded bundle from `kaggle/task.py`, NOT source `harness/prompt.py`). So amending `prompt.py` does not race Iris's in-flight writes.

**But:** `kaggle/task.py` was built from a snapshot of `harness/prompt.py` via `build_task.py`. If we amend source, Kaggle artifact is out-of-date until rebuilt. **Mitigation:** after 3-model smoke passes, re-run `python kaggle/build_task.py` to refresh `kaggle/task.py`. This is a second-line step, doesn't block Phase 2 eval.

## Depth budget
- Ivan: 5 → all 5 Codex spawn at depth=0 (leaf). Clean. Zero further budget required.

## Cost estimate

Per-run output ≈ 20-30k tokens (Gia's data on Flash). 15 runs/model × ~25k out ≈ 375k out tokens each.

| Model | Output $/1M | 375k cost | Input cost (~50k/run × 15) |
|---|---|---|---|
| gemini-flash-latest | ~$0.30 | $0.11 | ~$0.04 |
| claude-sonnet-4-6 | $15.00 | $5.63 | ~$2.25 |
| gpt-5.4-mini | ~$0.60 | $0.23 | ~$0.08 |
| **Total** | | **≈10 USD** | |

10x headroom vs $75 budget. Covers prompt-hardening retries + 1 round of regeneration if needed.

## Timing estimate
- Phase 1 parallel: max(45, 60) = **60 min**
- Gate + manual review: **~10 min**
- Phase 2 parallel: **~25 min**
- **Total wall: ~95 min** from go.

## PREDICTION CLAIMS

- **Claim:** LocalLLM's 1-line divergence (system via constructor vs chats.new) is the only code difference between local and Kaggle runs. *Falsifiable by:* diff the `run_instance()` call chain — bytes below LLM layer should match.
- **Claim:** `gemini-flash-latest` + `claude-sonnet-4-6` + `gpt-5.4-mini` emit labelled `BEST_GUESS:` ≥95% of the time with hardened prompt (no fallback needed). *Falsifiable by:* counting parse_method from smoke + eval.
- **Claim:** Per-model eval wall ≈ 25 min avg. *Falsifiable by:* actual run — if any model averages >150s/row, we pull plug and re-scope.
- **Claim:** Total spend <$10, Sonnet dominates. *Falsifiable by:* `llm logs --json` post-run sum.


phase 3 [[factory-a-eval-plan-v1]]
