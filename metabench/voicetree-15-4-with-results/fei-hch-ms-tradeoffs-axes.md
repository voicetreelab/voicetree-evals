---
color: blue
isContextNode: false
agent_name: Fei
---
# Q3/Q4 — Pros/cons + axis-by-axis implications of multi-session HCH

Multi-session's main win is Axis B (real token counts vs word-count proxy). Main costs are 5× latency and 3× authoring complexity. Axes A and D are unchanged; Axis C improves marginally but fundamental gap (no per-subtask gold) remains.

## Q3 — Pros/cons

### Pros
- **Axis B upgrade**: Real `outputTokens` per call from `.run.json` vs `len(text.split())` word-count proxy. In v1 pilot: predicted 50 words, actual 137 — MAPE 0.516. Multi-session makes this a token-precise measurement.
- **True context isolation**: Each sub-solver cannot anchor on sibling work. Tests genuine decomposition capability, not stylistic formatting.
- **Smaller per-call input**: Each EXECUTE receives only question + subtask desc (~400 tokens). Single-call accumulates full growing context. Total token cost per question may be similar despite more calls.

### Cons
- **Latency**: ~5 sequential API calls per question × ~50s avg = ~250s vs ~49s single-call. ~5× slower per question. (Option A bridge: no parallelism within a task.)
- **Integration drift**: INTEGRATE call must reconstruct answer from text outputs only. Single-session model uses full in-context reasoning to reconcile subtask work.
- **Plan-execute coherence**: Sub-solvers don't know the overall plan context. Must explicitly re-state full subtask scope in each EXECUTE prompt to avoid misinterpretation.
- **Orphaned sub-calls**: If a sub fails (parse error, timeout), INTEGRATE receives partial inputs. Requires explicit error handling.
- **Timeout risk**: At 5 calls × 60s (HLE questions can run long) = 300s. Hits the bridge limit exactly. Complex questions may time out.
- **3× task authoring complexity**: 3 prompt templates (PLAN, EXECUTE, INTEGRATE) + dynamic dispatch + partial failure handling vs current single-prompt gen_hch_hle12_tasks.py pattern.

## Q4 — Axis-by-axis implications

| Axis | Single-session | Multi-session | Change |
|------|----------------|---------------|--------|
| A1 — atomic Brier | p_correct_if_atomic vs vanilla correct | unchanged | none |
| A2 — word MAPE | words_if_atomic vs vanilla word count | unchanged | none |
| A3 — decomp decision | chose_decomp vs accuracy lift over vanilla | unchanged | none |
| **B — subtask effort** | `words_to_produce_solution` vs `len(text.split())` | vs `outputTokens` from `.run.json` | **UPGRADE** |
| C — sub consistency | p_solve/confidence vs self-reported correctly_solved | same — still self-report, but sub-solver context isolated | marginal |
| D — final calibration | P_CORRECT vs gold judge | P_CORRECT from INTEGRATE vs gold | unchanged |

**Axis B detail**: Multi-session gives real input + output tokens per subtask. The `words_to_produce_solution` prediction (already in the spec) becomes directly comparable to `outputTokens` — a more principled measurement than word count, and consistent across models with different tokenizers.

**Axis C detail**: The sub-solver in multi-session can't see what siblings produced, so `correctly_solved=True` means 'I solved this isolated subtask' rather than 'I completed writing in a full-context session'. Marginally more meaningful, but the fundamental design gap (no per-subtask gold answer to verify against) remains. Axis C is still internal consistency only.

### NOTES

- Axis B is the only axis where multi-session provides a qualitatively different measurement (tokens vs words). All other axes can be scored equivalently in either mode.
- The v1 Axis C paradox (23/24 subtasks 'solved' yet 0/8 all-solved questions had correct final answers) would look identical in multi-session — correctly_solved is still a self-report.

[[fei-hch-multisession-research-overview]]
