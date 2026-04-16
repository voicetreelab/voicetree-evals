---
color: green
isContextNode: false
agent_name: Otto
---
# Otto — Current state summary (2026-04-16)

Running summary of the Kaggle benchmark orchestration arc. Starting task, major surprises, current state, next steps. Written at user's request for a check-in.

## Starting task

User brief: "make a kaggle benchmark actual spike... for the initial spike do the 5x6 coupled version... run it against gemini 3, sonnet, and gpt5.4... you will be orchestrator... start by spawning a codex agent." Scope was **one** problem class (coupled two-factory job shop, 5×6), **3 models**, **3 seeds**, via the Kaggle Option A bridge. My standing rule throughout: orchestrator discipline, never do substantive work myself, surface blast-radius decisions to the user.

## Major adjustments / surprises (in order)

1. **Raj's first-pass harness bugs.** Codex worker shipped pilot + JSONLs but left three gaps: no hard-kill on subtask budget (had to manually interrupt Sonnet seed 3), Gemini seed 3 plan_parse_fail, GPT-5.4 infeasible schedules on all 3 seeds.
2. **Rio's surgical fixes.** threading.Thread + join(timeout) for hard-kill, JSON-codeblock + uppercase-key fallback parser, diagnosed GPT-5.4 as **real capability gap** (machine-overlap violations every seed, narrated constraint satisfaction but emitted invalid schedules). Non-obvious gotcha: `kbench.actors.user.send` must be called INSIDE the worker thread because kbench context is thread-local.
3. **Token expiry mid-orchestration.** Kaggle Jupyter token is short-lived. Had to spawn Sam (round 1) then Vic (round 2) with Claude-in-Chrome tools to extract fresh token from the user's open tab. Pattern now codified.
4. **HLE-decomposition-uncertainty concern.** User raised a benchmark-validity question mid-run: coupled jobshop hands the model its decomposition; A3 loses signal. I reframed toward A1-calibration as the real signal. In parallel, Sai spawned Siti (Masked Block Jobshop) + Tara (4-problem Portfolio Spike) to address the concern structurally.
5. **Steiner × coloring n=12/k=4 got killed.** Queued as a follow-on Kaggle spike. Ren's exact-solve verdict: gold computation takes 1-2h per instance, SCIP-Jack not a quick drop-in, brute-force infeasible under 30min. **Verifier, not model, was the blocker.**
6. **Pivot to portfolio Kaggle port.** Sai's handoff: portfolio beats masked-block for multi-LLM reproduction because portfolio structure is what forces cross-subtask behavior. Rephased matrix (pilot → 3×1 → conditional 3×3) to de-risk the ~4.5h commit.
7. **Root-URL bridge fix.** Timi's Phase 0 pilot 404'd twice despite fresh tokens — turned out the /api/sessions path construction (/k/{run}/{token}/proxy) was wrong; root URL with ?token= query param works. Not staleness. Future refreshes use root form.
8. **Zoe's subtask_id gate diagnosis.** Sonnet's retry tripped a "parse_fail" stop despite all turns parsing correctly. Root cause: harness enforced sequential sub_id ordering, but Sonnet dynamically reorders subtasks (plan traversal 4→5→2→3→6). Fix: parse_fail still hard-stops, sub_id mismatch became soft override. **Free signal: Sonnet dynamically reorders subtasks, not just adds them — richer plan-as-state than Tara spec'd.**
9. **Portfolio n=1 falsified Sai's prediction 3.** GPT-5.4 executed the MOST subtasks (8), not Sonnet (4). GPT named its decomposition axis ("bottleneck-first") — only model to bite the axis-log prompt. Three genuinely distinct allocation strategies emerged in a single seed.

## Current state

**Shipped:**
- CJS-5×6 single-problem Kaggle spike, 3 models × 3 seeds. Gemini 5.27% mean gap (one 0% optimal), Sonnet 42.35%, GPT-5.4 95.19% (0/3 feasible). Pilot note: `kaggle/pilots/cjs-5x6-spike-2026-04-16.md`.
- Portfolio spike Kaggle port (4 problems: CJS-5×6, Steiner×coloring N=8 K=4, TSP-20, slack graph coloring 30-node) + Phase 0 pilot + Phase 1 matrix (3 models × 1 seed). Pilot note: `kaggle/pilots/portfolio-spike-2026-04-16.md`.

**Phase 1 headline (seed 1):**

| model | net | exec_subtasks | stop_reason | axis_p1 | P1 | P2 | P3 | P4 |
|---|---:|---:|---|---|---:|---:|---:|---:|
| Gemini 3.1 Pro | **129.48** | 2 | subtask_timeout | null | 0.00 | 1.00 | 0.00 | 1.00 |
| Sonnet 4.6 | 56.11 | 4 | subtask_timeout | null | — | 1.00 | 0.67 | 0.00 |
| GPT-5.4 | 59.62 | 8 | max_exec_turns | bottleneck-first | 0.00 | 1.00 | 0.40 | 0.00 |

**Model strategies (n=1, directional):**
- Gemini: hunt cheap exact wins (P2+P4 both solved optimally, skip the harder problems)
- Sonnet: spread effort, dynamically reorder, 4 subtasks across 3 problems
- GPT-5.4: broadest spread, burn to max_exec_turns, no self-regulated stop, only model to declare axis

**Workers:** Raj, Rio, Sam, Vic, Zoe all closed. Timi still idle (stood down post-Phase-1). Depth budget: 4 of 10 remaining.

## Sai's predictions scorecard (n=1)

| # | Prediction | Result |
|---|---|---|
| 1 | 60% all frontier LLMs one-shot single-problem regardless of richness | Not testable in portfolio |
| 2 | 75% portfolio forces multi-subtask | **CONFIRMED** (all 3 models 2/4/8) |
| 3 | 50% Sonnet most, Gemini thinking-heavy, GPT least rational | **PARTIALLY FALSIFIED** (GPT executed most; axis-declaration argues against "least rational") |
| 4 | 40% economic-stop discriminates cleanly | **PARTIAL CONFIRM** (56–130 net spread, distinct stop_reasons) |

## Next steps (user decision pending)

Three options surfaced, awaiting user call:

- **A. Full Phase 2** — seeds 2/3 all 3 models (~3h, token-refresh risk) → then fire analyzer
- **B. Skip to analyzer** on n=1 cross-model + cross-spike synthesis, revisit Phase 2 only if analyzer surfaces specific ambiguities
- **C. Narrow Phase 2** — Gemini+GPT only (highest-contrast pair), skip Sonnet confirmation

After whichever Phase 2 path: spawn Sonnet analyzer (task #11) to write `kaggle/pilots/spike-results-discussion-2026-04-16.md` synthesizing portfolio + CJS-5×6 across models — portfolio-vs-single behavior, economic-stop discrimination, A1 calibration cross-class, axis-selection rationality, Sai's prediction scorecard.

## Parallel threads not orchestrated by Otto

- **Sai** (parent-level) — proposed Masked Block Jobshop, handed off portfolio Kaggle port to me.
- **Siti** (under Sai) — built Masked Block Jobshop local harness, ran 1 Gemini seed (indeterminate boundaries confirmed, still one-shot).
- **Tara** (under Sai) — built portfolio local harness + parser + gate, her code is what I forked for Kaggle.
- **Tao** — committed repo state in groups.

## Artifacts index

- Orchestration: `otto-cjs-5x6-orchestration-done.md` (prior), this node (current)
- CJS-5×6: `kaggle/pilots/cjs-5x6-spike-2026-04-16.md`, `kaggle/results/cjs_5x6_*.jsonl`
- Portfolio: `kaggle/pilots/portfolio-spike-2026-04-16.md`, `kaggle/results/portfolio_pilot_*.jsonl`
- Harness: `kaggle/examples/coupled_jobshop_spike/cjs_5x6.py`, `kaggle/examples/portfolio_spike/portfolio_spike.py`, `kaggle/scripts/run_*.py`
- Worker progress nodes: `rio-cjs5x6-fixes-progress.md`, `portfolio-spike-v1-kaggle-root-url-pilot-2026-04-16.md`, `portfolio-spike-sonnet-fix-pass-2026-04-16.md`, `portfolio-spike-phase1-gpt54-complete-2026-04-16.md`, `token-refresh-done.md`, `token-refresh-round2-done.md`

parent [[recommended-problem-setup-post-tsp_2_0_0]]
