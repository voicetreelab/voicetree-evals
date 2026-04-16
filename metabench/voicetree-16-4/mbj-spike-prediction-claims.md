---
color: blue
isContextNode: false
agent_name: Bob
---
# MBJ spike — PREDICTION CLAIMS + follow-up notes

Four prediction claims with falsifiers + concrete notes for the agent that graduates MBJ to full class status (adds to SOLO_CLASSES, integrates portfolio, lands 12 hard seeds).

# PREDICTION CLAIMS

## 1. Porting the remaining 11 medium seeds will work without new surprises — 85% confident

**Basis:** The generator passed seed 1 on attempt 0 (no retries). The `_generate_candidate` → `run_preflight_heuristics` → `solve_exact_schedule` pipeline is deterministic-per-seed with 24 `max_generation_attempts` — it should self-heal for most seeds via the attempt loop.

**Falsifier:** Any seed 2..12 that fails the pre-flight after all 24 attempts. Likely culprits: `min_baseline_gap_pct=10` rejecting seeds where SPT is near-optimal; `min/max_heuristic_spread_pct=3..60` rejecting degenerate families.

## 2. Porting 12 hard seeds will work without new surprises — 55% confident

**Basis:** Hard is 12×10 with a 120s CP-SAT budget. For some seeds CP-SAT will hit the time limit without proving optimality. `solve_exact_schedule` currently accepts `FEASIBLE` status (pilot behaviour), so `gold_submission` may be sub-optimal and `baseline_gap_pct` math assumes the returned gold IS the optimum.

**Falsifier:** Hard-row generation exits with `solver_status="FEASIBLE"` and a baseline_gap_pct that's negative or otherwise inconsistent with the stored gold.

**Mitigation:** Raise `cp_time_limit_s` to 600s for hard, or assert `is_optimal` before returning (breaking generation for those seeds and relying on the attempt-loop + smaller sizes to eventually land).

## 3. LLMs will achieve non-trivial MBJ feasibility at first run — 70% confident

**Basis:** The schema is structurally similar to CJS (which has ~50–90% solo parse rates on Sonnet/GPT/Gemini), and the prompt embeds a fully-worked baseline schedule that models can echo back for guaranteed feasibility.

**Falsifier:** 0/3 frontier models emit a feasible MBJ schedule on seed 1 at first LLM run.

## 4. Adding MBJ to SOLO_CLASSES is non-trivial — 95% confident

**Basis:** That change propagates MBJ into:
- `HARD_SIZE_FALLBACKS` (currently has no MBJ entry, so a failing hard seed has no fallback)
- `MEDIUM_PORTFOLIO_COMPONENT_IDS` / `HARD_PORTFOLIO_COMPONENT_CLASSES` (portfolio assembly sampling)
- W5/W6/W8-style worker scripts that sample from `SOLO_CLASSES`
- Portfolio `_initial_best_guess` seeding (MBJ uses `baseline_submission` key, which runner reads first, so this specific integration is fine)

**Falsifier:** Adding `"mbj"` to `SOLO_CLASSES` makes `build_questions.py` or portfolio evaluation raise.

# Notes for the follow-up agent graduating MBJ to full class status

1. **Add `"mbj"` to `HARD_SIZE_FALLBACKS`** with medium-difficulty sizing as the fallback: e.g. `"mbj": (("n_jobs", 8), ("n_machines", 8))`. Current code will crash for any failing hard seed because there's no fallback path.

2. **Tune `min_baseline_gap_pct` and heuristic-spread bounds per difficulty.** For full-scale MBJ you probably want the pilot's 5–35% spread range to maintain benchmark signal. I loosened to 3–60% because small 8×8 instances have tighter natural spread.

3. **Decide CP-SAT optimality policy for hard.** Either: (a) require optimality and loop on seed if not proven within 120s, or (b) accept FEASIBLE and adjust `baseline_gap_pct` to compute against best-known rather than gold. Current pilot-style code takes option (b) silently, which rots gold-objective math.

4. **Portfolio integration:** MBJ `baseline_submission` has shape `{"machines": {...}, "makespan": ..., "weighted_tardiness": ..., "objective": ...}`. Portfolio's `_initial_best_guess` at `runner.py:472-501` reads `sub_instance['baseline_submission']` first — so seeding already works for portfolios containing MBJ. The `sub_inst.problem_statement` path in `render_nl._render_portfolio` also already handles it correctly.

5. **Smoke test before landing full class:** regenerate a single `mbj_hard_seed1` via the existing hard-row fallback, then run one LLM call through `run_instance` to confirm the prompt+schedule+score round-trip holds end-to-end. Skip if time-constrained.

forward-looking [[mbj-spike-landed]]
