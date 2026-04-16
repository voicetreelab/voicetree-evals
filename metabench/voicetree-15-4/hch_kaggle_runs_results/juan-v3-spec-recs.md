---
color: blue
isContextNode: false
agent_name: Juan
---
# HCH spec v3 — recommendations from HLE-12 v2 multi-model evidence

8 v3 spec changes priority-ranked by measurement impact. Top 3 are load-bearing for scientific validity: stratified difficulty (resolution=0 structural fix), AUC axis (anti-correlation detection), and judge reasoning-model compatibility (DeepSeek/o3 runnable). Lower-priority items address infrastructure pain and axis design gaps.

## P1 — Stratified difficulty per model tier [HIGH — measurement validity]
**Problem:** Resolution=0 for ALL 11 arms. At N=12, questions either too hard (8% acc for most OSS) or too easy (87% for Gemini Pro). ō(1-ō) ceiling at 8% = 0.074 max achievable resolution.
**Evidence:** Jose's Murphy decomp + all 11 arms confirm. Gemini Pro degenerate at high end; all others degenerate at low end.
**Change:** 3 difficulty strata (easy/medium/hard, 4 Qs each). Select per model using prior accuracy estimate. Target 30–60% aggregate baseline accuracy per run.
**Impact:** Makes Resolution, AUC, and Brier decomposition informative. The single most important structural fix.

## P2 — AUC as primary discrimination axis (A4) [HIGH — exposes reward-hacks]
**Problem:** Total Brier masks anti-correlated models. Haiku (AUC=0.409) and Qwen-Think (AUC=0.10) both pass casual Brier inspection but are actively harming calibration.
**Evidence:** Haiku composite 0.55 (#3), but anti-correlated. Qwen-Think AUC=0.10 — worst in suite.
**Change:** Add Axis A4: AUC(p_correct_if_atomic, vanilla_correct) + AUC(P_CORRECT_HCH, hch_correct). Flag any arm with AUC<0.5 as 'anti-discriminating'.
**Impact:** Exposes reward-hackers. Rank-based metric is invariant to base rate and N.

## P3 — Judge reasoning-model compatibility [HIGH — runnable on R1/o3]
**Problem:** DeepSeek R1-0528 wraps ALL outputs in `<think>...</think>` blocks. `judge.startswith('YES')` fails → judge_pass=False all 24 tasks. A1, A3, B, C all contaminated.
**Evidence:** ivy-deepseek-r1-hle12-complete.md — judge bug; all scores unreliable.
**Change:** Pre-process judge response: strip `<think>...</think>` block before parse. Use `'YES' in response.upper()` not `startswith`. Apply same fix to answer extraction from reasoning models.
**Impact:** Makes benchmark runnable on R1, o3, Qwen-Think, and any future reasoning model without workarounds.

## P4 — max_output_tokens kwarg forwarding [HIGH — operational]
**Problem:** LLMChat.prompt() silently strips `max_output_tokens` kwarg. Without cap, Q43 (Sonnet: 11,592 words, 11.5 min), Q49 (Sonnet: 9,982 words, 6 min), Q43 (Flash-Lite: 10,376 words).
**Evidence:** hana-sonnet-arm-complete.md; ivy-flashlite-hle12-complete.md.
**Change:** Add `max_output_tokens` param to LLMChat.prompt() pass-through to proxy API. Set default=32768 in all task files (already done by Eve's v2 patch — just needs proxy to honor it).
**Impact:** Prevents runaway generation; makes per-question timing comparable across arms.

## P5 — Report Brier decomposition always [MEDIUM — scientific rigor]
**Problem:** Total Brier alone hides failure mode. v1 D_hch=0.934 and Haiku A1=0.253 look different in magnitude but both have Resolution≈0; the difference is Reliability, not discrimination.
**Evidence:** Jose's decomp — all 5 arms near-zero resolution. Confirmed for 6 new arms.
**Change:** Runner outputs Reliability, Resolution, Uncertainty alongside total Brier per axis. Flag degenerate cases (accuracy <5% or >90%) in report.
**Impact:** Most informative single addition for peer review; differentiates overconfidence from anti-correlation.

## P6 — Per-subtask gold for Axis C (optional upgrade) [MEDIUM — axis validity]
**Problem:** C paradox: every arm shows C≈0.001–0.100 (near-perfect), yet final accuracy 0–79%. Model reports correctly_solved=True for subtasks even when wrong.
**Evidence:** Flash-Lite Q99: all 4 subtasks correctly_solved=True, final answer wrong. Holds for all 11 arms.
**Change (optional):** Add `gold_subtasks` field to task spec for Qs where intermediate answers are well-defined. Old C (self-report) retained as metacog signal. New C_verified = Brier(p_solve, actual_subtask_correct).
**Impact:** Separates self-consistency (valid metacog) from ground-truth calibration (new, harder claim). Not mandatory — existing C is interpretable as designed.

## P7 — Protocol non-compliance hardening for OSS [MEDIUM — OSS comparability]
**Problem:** GPT-OSS-120B never emits ATOMIC_PREDICTION, SUBTASKS, P_CORRECT consistently. 5 proxy 503s. A1/A2/B/C unreliable (n=2 each). Never decomposes (0/8).
**Evidence:** ivan-gptoss-hle12-complete.md; protocol skip pattern.
**Change:** Stronger system prompt with explicit chain-of-thought instruction; few-shot example of compliant output. Add Axis E: protocol_compliance_rate = (tasks with all required fields) / N.
**Impact:** Makes OSS arms comparable to closed-tier; flags non-compliant models explicitly.

## P8 — Direct-proxy runner (migration away from Kaggle bridge) [LOW — operational]
**Problem:** Kaggle kernel session expiry was root cause of 3 blocked arms (Gus/Hana/Ian on shared kernel). Watchdog overhead per session expiry.
**Evidence:** jin-direct-proxy-spike-overview.md — direct proxy call confirmed feasible. john-runner-timeout-defaults-bumped.md — 40-min ceiling needed.
**Change:** Default new arms to direct-proxy runner (jin's 76-LOC spike). Kaggle Option A kept only for legacy kbench integration tests.
**Impact:** Eliminates operational #1 pain point. Proxy API key is stable; no kernel expiry or contention.

## Summary table
| Priority | Rec | Impact area | Evidence arm |
|----------|-----|-------------|---------------|
| P1 | Stratified difficulty | Resolution ceiling | ALL 11 arms |
| P2 | AUC axis (A4) | Anti-correlation detection | Haiku, Qwen-Think |
| P3 | Judge reasoning-model | R1/o3 runnable | DeepSeek R1 |
| P4 | max_output_tokens forward | Runaway generation | Sonnet, Flash-Lite |
| P5 | Brier decomp always | Failure mode clarity | Jose's 5-arm decomp |
| P6 | Per-subtask gold (C) | Ground-truth subtask | All arms (C paradox) |
| P7 | OSS protocol hardening | OSS comparability | GPT-OSS-120B |
| P8 | Direct-proxy runner | Operational reliability | Gus/Hana/Ian blocked |

### NOTES

- P1 and P2 are co-dependent: stratified difficulty makes Resolution non-zero; AUC then has meaningful signal above that floor. Implement together.
- P3 (judge reasoning-model) is already a bug fix more than a spec change — can be patched in _judge_answer() without protocol revision.
- P6 note from Emi's insights node: Axis C self-report IS a valid metacog measurement as-is. The upgrade to per-subtask gold is additive, not a correction of a flaw.
- Q44 CTF (flag{no_zeros}) should be replaced in any v3 question set — requires code execution, blocked every arm, not a pure reasoning task.
- Q68 gold answer may be wrong: DeepSeek R1 argument that 'C' (not 'B') is correct for decreasing-domain modal logic was noted in ivy-deepseek-r1-hle12-complete.md. Worth reviewing with a domain expert before v3.

## Related

- [juan-hle12-leaderboard](juan-hle12-leaderboard.md)
- [juan-brier-decomp-11arm](juan-brier-decomp-11arm.md)
- [emi-hch-insights-learnings](emi-hch-insights-learnings.md)
- [jin-direct-proxy-spike-overview](jin-direct-proxy-spike-overview.md)

[[task_1776261532883qv5]]
