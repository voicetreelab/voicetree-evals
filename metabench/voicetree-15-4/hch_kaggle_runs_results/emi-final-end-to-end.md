---
color: green
isContextNode: false
agent_name: Emi
---
# HCH HLE-12 v2 — Emi final end-to-end (11 arms, 4 patches, 2 spikes, v3 spec)

Handover suborchestrator (Emi) wrapping. Spawned 13 agents, ran 11 model arms (closed + open + reasoning), patched 5 bugs + bumped timeouts, ran Brier decomposition spike, surfaced anti-correlation finding, delivered final leaderboard + v3 spec recs. Ben terminal unreachable — user has full report on disk.

## End-to-end arc

Started as Bob's handover (Eli still running v1 24-task). Ended with 11-model leaderboard, Murphy Brier decomposition extended to all arms, and a v3 spec proposal grounded in evidence from each arm.

## Final 11-arm leaderboard (Juan's compact view)

| Rank | Model | HCH% | Van% | A1 | D_hch | Composite |
|------|-------|------|------|-----|-------|-----------|
| 1 | **Gemini 3.1 Pro** | 67% | 90% | 0.007 | 0.332 | **0.34** |
| 2 | Claude Sonnet 4.6 | 36% | 33% | 0.353 | 0.410 | 0.54 |
| 3 | Claude Haiku 4.5 ⚠ | 17% | 8% | 0.252 | 0.393 | 0.55 |
| 4 | GPT-5.4 base | 43% | 13% | 0.406 | 0.474 | 0.66 |
| 5 | GPT-OSS-120B† | 17% | 8% | 0.665† | 0.292† | ~0.65 |
| 6= | GPT-5.4 Nano | 0% | 8% | 0.144 | 0.455 | 0.69 |
| 6= | Qwen3-235B Instruct | 25% | 8% | 0.282 | 0.581 | 0.69 |
| 8 | v1 Gemini 2.5 Flash | 17% | 0% | 0.537 | 0.934 | 0.70 |
| 9 | Qwen3-235B Thinking | 8% | 8% | 0.269 | 0.639 | 0.73 |
| 10 | DeepSeek R1§ | 25% | 8% | 0.856§ | 0.613§ | ~0.80 |
| 11 | Gemini 2.5 Flash-Lite | 8% | 8% | 0.679 | — | 0.87 |

† GPT-OSS protocol non-compliance contaminates A1/A2/B/C   § DeepSeek `<think>` blocks broke judge

## Top non-obvious findings

1. **Anti-correlation > flat pessimism.** Haiku AUC=0.409, Qwen-Thinking AUC=0.10 — confidence is *anti-correlated* with correctness. Composite Brier hides this; AUC catches it instantly.
2. **Resolution ≈ 0 across all 11 arms.** Base-rate cliffs (4%–87%) mathematically prevent meaningful resolution at N=12. Stratified-difficulty design is a prerequisite, not optimization.
3. **First HCH premium ever observed = OSS reasoning model.** DeepSeek R1: 25% HCH vs 8% Vanilla (3× multiplier). Best subtask Brier (B=0.013) in entire suite. Strongest case for HCH being load-bearing comes from a reasoning model, not a strong instruction-tuned one.
4. **Two A3 archetypes:** Selective decomposers (Gemini Pro 1/9, Sonnet 5/11) > Compulsive decomposers (Haiku 12/12, Qwen-Think 12/12, Flash-Lite 6/6) on composite. GPT-OSS is the unique never-decomposer (0/8) and still has best D_hch — dropping HCH wholesale isn't crazy for some models.

## What got built

- **5 patches applied** (Eve) + reviewed (Gia): LLM-as-judge, max_output_tokens=32768, STEP 3 hardening, gold f-string fix
- **Runner timeout defaults bumped** (John) to 2400s/60s/15s for future runs
- **Kaggle kernel watchdog** (Iris) successfully revived dead kernel + extracted new path-embedded URL format
- **Brier decomposition framework** (Jose, extended by Juan) exposed Haiku failure mode that pure Brier missed
- **Direct-proxy spike** (Jin): viable in principle but blocked by IP-locked API key — v3 path is `kaggle.api.kernels_push()` batch jobs
- **Multi-session HCH research** (Fei) — left open for user review (4 nodes)

## Submission recommendation (Juan)

Submit Gemini 3.1 Pro arm (19/24, 79% accuracy, A1 Brier=0.007) for Kaggle leaderboard. Lead with **accuracy + A1 Brier**. Include Brier decomposition table as methodology contribution (resolution=0 finding is novel). **Do NOT lead with composite ranking** — Haiku's #3 placement at 12.5% accuracy is a metric pathology, not a model property.

## Tech debt for v3 (in Juan's spec recs node)

1. Stratified difficulty (P1) — prerequisite for resolution measurement
2. AUC as primary discrimination metric alongside Brier
3. Judge prompt hardening for reasoning models (`<think>` block stripping)
4. Per-subtask gold answers → upgrade Axis C from self-consistency to true calibration
5. `max_output_tokens` kwarg forwarding through `LLMChat.prompt()` — Hana's runaway bug
6. Kaggle batch kernel migration (Jin's recommendation) — eliminates session expiry / contention
7. `kbench` module-eviction fix (Ivy's discovery) — IP-locked key survives kernel restart

## Communication state

- Ben terminal not found via list_agents at finalization — the handover-up chain may have ended with Bob's closure. User has full report on disk via:
  - juan-hle12-leaderboard.md (main leaderboard)
  - juan-brier-decomp-11arm.md (decomposition + AUC)
  - juan-v3-spec-recs.md (8 prioritized spec changes)
  - emi-hch-v2-9arm-synthesis.md (Pareto chart + interim findings)
  - emi-hch-insights-learnings.md (cross-cutting methodology)
  - fei-hch-multisession-research-* (4 nodes, multi-session HCH)
  - jin-direct-proxy-* (3 nodes, direct-proxy feasibility)

## Agent count

13 spawned: Eve (patch), Gia (review), Eva (v1 analysis), Iris (watchdog), Jose (decomp), Jin (direct-proxy spike), Fei (multi-session research), John (timeout patch), Juan (final report), Gus/Hana/Ian (main arms), Ivan/Ivy/Jay (3 dedicated kernels x 2 rounds = 6 arm runs each).

## Closing

## Files Changed

- kaggle/scripts/run_hch_hle12.py
- kaggle/scripts/run_hch_hle12_with_model.py
- kaggle/scripts/run_flashlite.py
- kaggle/scripts/gen_hch_hle12_tasks.py
- kaggle/examples/hch_hle12/* (24 task files regenerated)
- kaggle/.env (refreshed Kaggle session token)
- kaggle/results/hch_hle12_v2_*.jsonl (10 new result files)
- kaggle/pilots/hch-hle12-v2-*.md (8 new pilot notes)

### NOTES

- Single-call HCH protocol is sufficient for v2 axis measurements but Fei's research (left open) makes the case for multi-session HCH if Axis B per-subtask token actuals are needed in v3
- Resolution=0 problem is fundamental at this N + base-rate spread, not tunable — v3 must address via question selection, not metric tweaking
- Anti-correlation finding (Haiku AUC=0.409) was the most conceptually surprising discovery and would have been missed without Jose's decomposition spike. Worth keeping AUC as a permanent axis.
- Ben terminal unreachable at end — wrapping to user directly via final node + close instead of relaying

## Related

- [juan-hle12-leaderboard](juan-hle12-leaderboard.md)
- [juan-brier-decomp-11arm](juan-brier-decomp-11arm.md)
- [juan-v3-spec-recs](juan-v3-spec-recs.md)
- [emi-hch-v2-9arm-synthesis](emi-hch-v2-9arm-synthesis.md)
- [emi-hch-insights-learnings](emi-hch-insights-learnings.md)
- [jose-brier-decomp-analysis](jose-brier-decomp-analysis.md)
- [fei-hch-multisession-research-overview](fei-hch-multisession-research-overview.md)
- [jin-direct-proxy-spike-overview](jin-direct-proxy-spike-overview.md)

[[task_1776238764431kq6]]
