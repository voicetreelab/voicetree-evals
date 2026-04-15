---
color: green
isContextNode: false
agent_name: Cho
---
# MetaCoach RUN suborch — both pilots executed end-to-end via Option A bridge

Spawned Dae (Sonnet, headful). Both Q1 + Q2 ran live on the Kaggle kernel via Option A bridge. Toolchain validated. Pilot note updated in place with real run data — zero fabrication. Critical finding: vanilla-arm format compliance is the binding bottleneck, not reasoning capability.

## Decomposition decision

One worker, not two. Two sequential bridge submissions + one pilot-note update share all setup (.venv, .env, kernel state); splitting per-question would have duplicated context-load and risked kernel contention beyond the existing parallel HCH worker (Bob's side).

## Outcome

| Q | passed | vanilla | metacoach | redirected |
|---|--------|---------|-----------|------------|
| Q1 (grid 63/512) | ❌ False | None / None | None / p=0.99 | False |
| Q2 (last digit=2) | ✅ True | None / None (format fail) | 'B' / p=0.99 | True (FALSE POSITIVE) |

## Key findings

1. **Format non-compliance is the dominant failure mode** — Gemini 2.5 Flash defaults to LaTeX `$\boxed{X}$` instead of the required `ANSWER: X` line. Affects all vanilla calls + Q1 metacoach. Q2 metacoach happened to comply.
2. **Redirection metric is contaminated by format failures** — Q2 `redirected=True` is a false positive: vanilla reasoned to the correct answer but failed format parsing, so any non-None metacoach answer scores as redirection. The novelty metric needs a parser-robustness gate before MetaCoach signal can be trusted.
3. **Bridge timeout was 30s; insufficient for 2-call tasks (~50–90s).** Dae bumped `submit_task.py:228` to 300s — small, defensible change.
4. **Per-call token breakdown in `.run.json` confirmed present** (Q2 shows req-1 vanilla and req-2 metacoach with separate in/out/latency).
5. **Bridge serializes correctly** — initial run hit `KernelBusyError` (overlap with HCH worker / prior timed-out exec); 90s wait + retry succeeded. Coordination with Bob's worker held.
6. **`.task.json` only emitted on pass** (Q2 yes, Q1 no). Kaggle "Save Task" UI flow not exercised.

## Deliverables verified

- `kaggle/pilots/metacog-spike-2026-04-15.md` — updated in place with run data
- `kaggle/option_a_bridge/submit_task.py` — timeout 30→300s
- 3 artifacts on Kaggle-side: q1.run.json, q2.task.json, q2.run.json
- Worker progress node: [metacoach-run-worker-results](metacoach-run-worker-results.md)

## Implications for Ben/Aki

- **Toolchain ✅** — Option A bridge end-to-end works; both spikes (HCH parallel + this) validated.
- **Production blockers identified** — (a) prompt must enforce ANSWER: format hard, or (b) parser must extract boxed-letter fallback before scoring vanilla. Without one of these, MetaCoach redirection metric is unmeasurable.
- **Cost signal** — vanilla 137in/966out, metacoach 1436in/2193out per Q2; coaching prefix ~10× input, ~2× output token cost.

## Learnings (for the next agent)

**1. What did I try first, and why did I change approach?**
No approach change. Spawned exactly one Sonnet worker (Dae) on first decision and held to orchestrator discipline — never read or ran the bridge myself. The "one worker not two" call was already well-justified by the prior auth-phase suborch (Amit→Amy); preserving that decision avoided redundant context-load.

**2. If a future agent attempts this same task, what will they get wrong?**
Don't trust `redirected=True` on MetaCoach until vanilla-arm format compliance is verified — right now it's a near-guaranteed false positive on Gemini 2.5 Flash because vanilla reasons correctly but emits `$\boxed{X}$` instead of `ANSWER: X`, so any non-None metacoach answer scores as redirection regardless of actual reasoning improvement. Fix the parser (boxed-letter fallback) OR enforce format in the prompt before any larger MetaCoach run, otherwise the load-bearing novelty metric is unmeasurable.

**3. What does a successor need to believe to continue without repeating my reasoning?**
- Option A bridge end-to-end works on real Kaggle kernel; toolchain is no longer the risk.
- Default `submit_task.py` timeout is 30s — too short for any 2+ LLM-call task. Stays at 300s now.
- `.task.json` only emits on pass; `.run.json` emits per-call with separate token counts/latency — good for cost analysis (coaching prefix ~10× input tokens).
- Bridge serializes; parallel suborchs (HCH + MetaCoach) can collide → `KernelBusyError`, recoverable with ~90s backoff + retry.
- **The real research blocker is parser robustness, not bridge plumbing or prompt design.**

## Related

- Worker: [metacoach-run-worker-results](metacoach-run-worker-results.md)
- Prior auth phase: [metacoach-spike-suborch-report](metacoach-spike-suborch-report.md)
- Parallel HCH suborch: Bob (separate report)

[[task_1776233921100lmb]]
