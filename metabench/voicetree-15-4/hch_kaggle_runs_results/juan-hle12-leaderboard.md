---
color: green
isContextNode: false
agent_name: Juan
---
# HCH HLE-12 v2 — FINAL 11-arm leaderboard + rankings

11 model arms complete on HLE-12. Gemini 3.1 Pro is strict Pareto dominator (79% acc, composite 0.34). DeepSeek R1 is first arm where HCH beats vanilla (+17pp), but <think> judge bug contaminates all axis scores. GPT-OSS unique never-decomposer; best D_hch=0.292. Composite diverges sharply from accuracy for Haiku (anti-correlated, AUC=0.41) and DeepSeek (contaminated). Composite = mean(A1_Brier, cap(A2_MAPE,1.0), A3_wrongdec, D_hch_Brier); missing/invalid values dropped.

## Core metrics — sorted by Composite (lower = better)

| C-rank | Model | HCH% | Van% | A1↓ | A2_cap↓ | A3↓ | D_hch↓ | Comp↓ | Acc-rank |
|--------|-------|------|------|-----|---------|-----|--------|-------|----------|
| 1 | **Gemini 3.1 Pro** | 67%(6/9) | 90%(9/10) | **0.007** | 0.793 | 0.22 | 0.332 | **0.34** | **1** |
| 2 | Claude Sonnet 4.6 | 36%(4/11) | 33%(4/12) | 0.353 | **0.524** | 0.73 | 0.410 | 0.54 | 2 |
| 3 | Claude Haiku 4.5 | 17%(2/12) | 8%(1/12) | 0.252 | 0.582 | 0.83 | 0.393 | 0.55 | 7⚠ |
| 4 | GPT-5.4 base | 43%(3/7) | 13%(1/8) | 0.406 | 1.000 | 0.57 | 0.474 | 0.66 | 3 |
| 5 | GPT-OSS-120B† | 25%(2/8v) | 8%(1/12) | 0.665† | 1.000† | n/a | **0.292†** | ~0.65† | 5= |
| 6= | GPT-5.4 Nano | 0%(0/12) | 8%(1/12) | 0.144 | 1.000 | 0.92 | 0.455 | 0.69 | 10⚠ |
| 6= | Qwen3-235B-Instruct | 25%(3/12) | 8%(1/12) | 0.282 | 1.000 | 0.79 | 0.581 | 0.69 | 4= |
| 8 | v1 Gemini 2.5 Flash | ~17% | 0% | 0.537 | 0.745 | 0.83 | 0.934 | 0.70 | 7= |
| 9 | Qwen3-235B-Thinking | 8%(1/12) | 8%(1/12) | 0.269 | 1.000 | 0.92 | 0.639 | 0.73 | 7= |
| 10 | DeepSeek R1-0528§ | 25%(3/12) | 8%(1/12) | 0.856§ | 1.000§ | 0.75 | 0.613§ | ~0.80§ | 4=⚠ |
| 11 | Gemini Flash-Lite | 8%(1/12) | 8%(1/12) | 0.679 | 1.000 | 0.92 | — | 0.87 | 7= |

† GPT-OSS: n_A1=2, n_A2=2 (unreliable); A3=N/A (never decomposes, unique in suite); composite=mean(A1,A2,D_hch) only.  
§ DeepSeek: `<think>` prefix breaks `judge.startswith("YES")` → judge_pass=False all 24 tasks; A1 n=4/12 only. Composite unreliable.  
⚠ Haiku comp-rank #3 despite acc-rank #7; Nano comp #6 despite acc-rank #10 — both reward-hack signals, see Brier decomp node.

## Extended axes (B, C, D_van, failure mode)

| Model | B‡ | C‡ | D_van | Coverage | Failure mode |
|-------|----|----|-------|----------|--------------|
| Gemini 3.1 Pro | 0.226 | 0.001 | 0.100 | 19/24 (5 contended) | protocol-skip (rarely decomposes) |
| Claude Sonnet 4.6 | 0.527 | 0.065 | 0.307 | 23/24 (q44_hch timeout) | overconfident-on-wrong |
| Claude Haiku 4.5 | 0.371 | 0.100 | 0.522 | 24/24 | anti-correlated (AUC=0.409<0.5) |
| GPT-5.4 base | 0.063♣ | 0.474♣ | 0.769 | 15/24 (9 BUSY) | overconfident-final; B best in suite |
| GPT-OSS-120B | 1.706 | 0.001 | 0.493 | 24/24 (5 proxy 503) | never-decomposes |
| GPT-5.4 Nano | 0.586 | 0.116 | 0.394 | 24/24 | 4-word vanilla (A2 invalid) |
| Qwen3-235B-Instruct | 0.564 | 0.070 | 0.899 | 24/24 | compulsive-decomposer |
| v1 Gemini 2.5 Flash | 0.516 | 0.026 | N/A | 24/24 (4 bugs) | extreme-overconfidence |
| Qwen3-235B-Thinking | 3.750 | 0.028 | 0.786 | 24/24 | thinking-mode A2/B invalid |
| DeepSeek R1-0528 | 0.013 | 0.613 | N/A | 24/24 (<think> bug) | think-breaks-judge |
| Gemini Flash-Lite | 0.033 | 0.737 | N/A | 24/24 (D not logged) | severe overconfidence |

‡ B/C axis naming inconsistent: B=word_MAPE for most; GPT-base B=subtask_p_solve_Brier (♣). C=subtask_p_solve_Brier for most; GPT-base C=final_p_correct_Brier; DeepSeek C=D_hch equivalent. Use caution cross-arm.

## Cost estimates and notable annotations
| Model | Cost est. | Notable per-arm |
|-------|-----------|------------------|
| Gemini 3.1 Pro | ~$0.64–$1.00 | First-ever decomp payoff (Q41); Q44 CTF blocked all arms |
| Claude Sonnet 4.6 | ~$1–$3 | First decomp payoff in suite (Q41 4 subtasks) |
| Claude Haiku 4.5 | ~$0.10 | Always decomposes (12/12); anti-correlated A1 |
| GPT-5.4 base | ~$3–$8 | B=0.063 exceptional subtask calibration |
| GPT-OSS-120B | ~$1–$3 | Best D_hch=0.292; proxy 503 errors |
| GPT-5.4 Nano | ~$0.01 | Cheapest arm; Q52 self-judge false negative |
| Qwen3-235B-Instruct | ~$0.50 | HCH +2 over vanilla; Q49 70× verbosity overshoot |
| v1 Flash | ~$0.07 | Baseline; 4 bugs; all scores partially contaminated |
| Qwen3-235B-Thinking | ~$1–$2 | Q43 always truncates across all 3 arms it ran |
| DeepSeek R1-0528 | ~$0.50 | First +17pp HCH premium; B_subtask=0.013 (best) |
| Gemini Flash-Lite | ~$0.05 | kbench eviction bug discovered; D not logged |

## Accuracy-rank vs composite-rank: big movers
- Haiku: acc #7 → comp #3 (anti-correlation, not reward-hack — see Brier node)
- Nano: acc #10 → comp #6 (suspiciously low A1=0.144 at 0% HCH accuracy)
- DeepSeek: acc #4= → comp #10 (entirely from <think> bug contamination; true rank unknown)

### NOTES

- A2 values capped at 1.0 for composite: Nano raw=59.61, Qwen-Think=18.87, Qwen-Instruct=22.78, Flash-Lite=5.96, DeepSeek=12.90, GPT-OSS=5.88. All invalid for cross-model comparison — driven by verbosity artifacts, not calibration.
- Q44 CTF (flag{no_zeros}) blocked or failed EVERY arm. Requires code execution, not reasoning. Recommend replacing in v3 question set.
- Q43 truncated for Haiku, Qwen-Think, and Sonnet — pattern across 3 arms suggests this Q produces near-context-limit outputs regardless of max_tokens setting.
- GPT-OSS composite is provisional (n=2 for A1/A2). D_hch=0.292 is the single most surprising finding — best final-answer calibration in the suite at only 17% HCH accuracy.
- Decomp payoff rates: DeepSeek 3/8 (37.5%) and GPT-base 2/5 (40%) are only arms with meaningful payoff. All others 0-20%. Selective decomposition (Pro: 1/9, Sonnet: 5/11) beats compulsive (Haiku/Qwen: 12/12).

## Related

- [juan-brier-decomp-11arm](juan-brier-decomp-11arm.md)
- [juan-v3-spec-recs](juan-v3-spec-recs.md)
- [jose-brier-decomp-analysis](jose-brier-decomp-analysis.md)
- [emi-hch-v2-9arm-synthesis](emi-hch-v2-9arm-synthesis.md)

[[task_1776261532883qv5]]
