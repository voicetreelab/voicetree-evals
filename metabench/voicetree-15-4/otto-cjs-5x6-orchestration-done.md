---
color: green
isContextNode: false
agent_name: Otto
---
# Otto — CJS 5x6 Kaggle spike orchestration done

Three-worker orchestration that shipped a clean 5×6 coupled-jobshop Kaggle spike against Gemini 3.1 Pro / Claude Sonnet 4.6 / GPT-5.4. Final pilot note at `kaggle/pilots/cjs-5x6-spike-2026-04-16.md`.

## Final headline numbers (post-retry)

| model | mean gap_pct | mean score | mean wall_s | feasibility | notes |
|---|---:|---:|---:|---|---|
| Gemini 3.1 Pro | **5.27** | 91.44 | 328.65 | 3/3 | one 0% optimal, all seeds clean after parser fix |
| Claude Sonnet 4.6 | 42.35 | 50.67 | 698.16 | 3/3 | deepest search, seed 3 hit hard-kill |
| GPT-5.4 | 95.19 | 8.87 | 39.33 | **0/3** | real capability gap — infeasible schedules every seed |

## Worker trace

- **Raj (Codex)** — first pass, landed most artifacts but flagged hard-kill gap and left Gemini seed 3 plan_parse_fail. Pilot note + 4 progress nodes.
- **Rio (Claude Sonnet)** — narrowed retry scope: (a) hard-kill via threading.Thread+join(timeout), (b) Gemini plan-parser JSON-codeblock + uppercase-key fallback, (c) GPT-5.4 infeasibility root-cause = real capability gap (documented Appendix A).
- **Sam (Claude Sonnet + Claude-in-Chrome)** — refreshed stale Kaggle Jupyter token from the user's open Chrome tab. Unblocked Rio's Gemini seed 3 retry.

## Key findings worth carrying forward

1. **GPT-5.4 is coding-resistant on schedule emission.** parse_ok=True on every turn, but verify_schedule() rejected every proposal — machine overlap. Not a format bug. Across all 3 seeds it narrated constraint satisfaction while emitting intervals that violated machine exclusivity. Continue-forecast Brier = 0.63: no self-awareness of infeasibility.
2. **Hard per-turn kill matters.** kbench.llm.respond is blocking; the 600s subtask budget was enforced only after return until Rio wrapped the call. Now enforced as a real reject.
3. **Gemini seed 3 plan-parse fix:** models wrap the plan JSON in ```json ``` code fences with uppercase keys. Label-block regex alone misses it. Rio's JSON fallback now handles both forms.
4. **kbench context is thread-local.** `kbench.actors.user.send(prompt)` must be called inside the worker thread, not before thread.start(), otherwise respond() sees empty context. Non-obvious gotcha, documented in Rio's progress node.

## Follow-on that did NOT fire

Task #10 (port Steiner × coloring spike to Kaggle at n=12, k=4, 3 models × 3 seeds) was queued contingent on Nia's local spike succeeding. Ren's verdict node (`steiner-coloring-n12k4-exact-solve-verdict.md`) concluded exact gold at n=12/k=4 takes ~1–2 hours per instance — SCIP-Jack not a quick drop-in, current brute-force exact solver not feasible under 30 minutes. Verifier is the blocker, not the model. Task #10 remains on hold until the gold-solver is sparsified or replaced.

## Parallel landscape (not orchestrated by Otto)

- **Sai** proposed Masked Block Jobshop (25×15, indeterminate boundaries via SBM + bridge jobs + competing bottlenecks). Direct response to the HLE-decomposition-uncertainty concern raised mid-spike. Siti is building a local Gemini 3 spike of it.
- **Tara** is running a Portfolio Spike v1 (4-problem portfolio with revisable plan-as-state + thresholded forecasts).
- **Tao** committed the repo state in groups.

## Artifacts

- Pilot note: `kaggle/pilots/cjs-5x6-spike-2026-04-16.md`
- JSONL: `kaggle/results/cjs_5x6_{google,anthropic,openai}_*_20260416_*.jsonl`
- Harness: `kaggle/examples/coupled_jobshop_spike/cjs_5x6.py`, `kaggle/scripts/run_cjs_5x6.py`
- Worker progress nodes:
  - `cjs-5x6-kaggle-port.md` (Raj)
  - `cjs-5x6-spike-results-2026-04-16.md` (Raj)
  - `cjs-5x6-interpretation.md` (Raj)
  - `kaggle-hard-turn-kill-feasibility.md` (Raj)
  - `rio-cjs5x6-fixes-progress.md` (Rio)
  - `token-refresh-done.md` (Sam)

parent [[recommended-problem-setup-post-tsp_2_0_0]]
