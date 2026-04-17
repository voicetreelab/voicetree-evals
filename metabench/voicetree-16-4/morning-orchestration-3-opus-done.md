---
color: green
isContextNode: false
agent_name: Aki
---
# Morning orchestration — 3 Opus investigators complete

Spawned 3 Opus agents in parallel to work the overnight pilot's top 3 follow-ups from Ben's discussion doc. Amit → portfolio root cause + fix plan. Ari → MWIS-hard exclusion patch landed. Anna → metacog Brier analyzer script + report landed. All terminals left open for human review.

# Morning orchestration — 3 Opus investigators complete

## Scope

User asked to orchestrate morning follow-up on the overnight pilot. Based on Ben's `discussion-of-results.md` (Experiments 1, 2) + user's explicit asks, three independent investigations decomposed cleanly. Spawned one Opus per concern, depth 0, no sub-spawning — ran in parallel.

## Agents + outcomes

| Agent | Terminal | Scope | Task node | Deliverable | Status |
|---|---|---|---|---|---|
| Amit | Amit | Portfolio infeasibility root cause | task_1776373751566rv9 | 6-node tree: root / evidence / mechanism / citations / fix-proposal / open-questions | **open** (review pending) |
| Ari | Ari | MWIS-hard patch-or-remove from portfolio-hard | task_1776374118474b9d | Landed `PORTFOLIO_HARD_EXCLUDE_CLASSES` constant (option b). Generator patch deferred with concrete plan. | **open** (sign-off pending) |
| Anna | Anna | Metacog forecast calibration — previously dark data | task_17763740598480xi | analyze_metacog.py + metacog_analysis.md + metacog_rollup.csv. 1182 forecast-turns scored. | **open** (review pending) |

## Headline findings

**Amit (portfolio):** Not a model-capability bug. Prompt-construction bug — `render_nl(portfolio)` emits only `problem_id|class|value_cap`, drops all sub-component instance data + per-class schemas. Models invent schemas (Sonnet `"selected"` vs `"selected_vertices"`, Gemini hallucinates TSP nodes from Steiner cities). Fixes 1+2+3 = ~60 LOC, expected lift 0→~70% medium / 3→~50% hard.

**Ari (MWIS):** Chose exclusion over generator patch because Sonnet is 0/6 feasible + 3/3 stop=error on solo MWIS-hard anyway — even a perfect generator contributes one dead model to portfolio scoring. Canonical constant landed. Generator root cause also diagnosed (bridge-bypass in `_connect_components`) with a ~15-line fix plan for follow-up.

**Anna (metacog):** Overall Quality Brier = 0.197. Model ordering: Sonnet 0.097 ≫ GPT 0.172 > Gemini 0.322. Continue-forecast adds ~no resolution over base-rate (all three within ±0.03 of own floor). GPT emits identical forecasts turn-after-turn on 53/64 rows (flat-forecast bug). VE rows all emit solo-style thresholds — prompt-schema mismatch that should be fixed.

## Cross-cutting observations

- Two independent prompt bugs discovered in one morning (portfolio render_nl + VE threshold schema). The overnight benchmark was surfacing model performance through a noisy prompting layer on multiple classes.
- Ari's Claim 3 (Sonnet's MWIS-hard floor) is reinforced by Anna's finding (Sonnet Brier 0.097 overall, but cjs_medium Brier 0.883 + worst cells concentrated on the classes it fails on — overconfident in collapse).
- None of the three fixes overlap. Ari's landed; Amit's + Anna's recommended follow-ups are independently applicable.

## Why leave terminals open

- **Amit:** fix proposal is unlanded — user should review before any patches go in.
- **Ari:** constant landed without explicit sign-off; option (b) vs (a) is a judgement call.
- **Anna:** VE prompt fix recommendation is actionable and not landed.

## Depth budget usage

I started with DEPTH_BUDGET=10. Spawned 3 children at budget=0 (so none could further spawn). Remaining budget: 10 — none used recursively. Orchestration cost stayed cheap.

## Related

- [portfolio-infeasibility-root](portfolio-infeasibility-root.md) — Amit
- [mwis-hard-portfolio-exclude-landed](mwis-hard-portfolio-exclude-landed.md) — Ari
- [metacog-forecast-analysis-done](metacog-forecast-analysis-done.md) — Anna
- [discussion-of-results](discussion-of-results.md) — Ben (source)

[[MORNING-WAKEUP-BRIEF_1]]
