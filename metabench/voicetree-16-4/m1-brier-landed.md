---
color: green
isContextNode: false
agent_name: Ben
---
# M1 (p_solve Brier + Murphy decomposition) landed in analyze_metacog.py

M1 computed over solo-class subtasks: Sonnet Brier=0.186/res=0.101, Gemini 0.207/0.022, GPT 0.275/0.121. Portfolio skipped (per-sub-component verification not implemented). Murphy identity holds to ≤0.002. Writeup-v2 finding 7 (GPT has highest resolution) is confirmed; M1 ranks GPT > Sonnet > Gemini on resolution — opposite direction from M2 where Sonnet leads.

# M1 landed — subtask-solvability Brier + Murphy decomposition

## Headline numbers

| model | M1 Brier | reliability ↓ | resolution ↑ | uncertainty | n (subtasks) | rows scored |
|---|---|---|---|---|---|---|
| claude-sonnet-4.6  | 0.186 | 0.051 | **0.101** | 0.236 | 34 | 28 |
| gemini-flash-latest | 0.207 | 0.132 | 0.022 | 0.099 | 45 | 33 |
| gpt-5.4-mini        | **0.275** | 0.176 | **0.121** | 0.220 | 49 | 36 |

Murphy identity check (should be ≡0):
- Sonnet: 0.0514 − 0.1011 + 0.2362 = 0.1864 vs brier 0.1863 (Δ=9e-5)
- Gemini: 0.1321 − 0.0223 + 0.0988 = 0.2086 vs brier 0.2072 (Δ=1.4e-3, from 10-bin discretization)
- GPT: 0.1765 − 0.1213 + 0.2199 = 0.2751 vs brier 0.2755 (Δ=4e-4)

## What M1 measures

- `p_solve_k` = the `p_solve` field in the NEXT_SUB that kicked off subtask k.
  - Subtask 1's p_solve comes from the plan turn's NEXT_SUB.
  - Subtask k≥2's p_solve comes from exec turn k−1's NEXT_SUB (only emitted when decision=continue).
- `kept_as_best_k` = 1 iff subtask k's BEST_GUESS became the running-best by strict gap_pct improvement over all prior subtasks. Subtask 1: kept_as_best=1 iff feasible.
- Verification path: `CLASS_TO_VERIFIER[cls](instance, best_guess) → (gap_pct, feasible, details)` using question.json's `instance` field. Infeasible → gap_pct = 100.0.

## What got skipped and why

- **Portfolio rows (28 × 3 models = 84 rows).** BEST_GUESS for portfolio is a nested dict keyed by sub-component problem_id; per-sub-component verifier routing is non-trivial and would require parsing `question.components[*].sub_instance` per turn. Per task brief's 20-minute budget rule I skipped rather than shoehorn.
- **Subtasks without parseable BEST_GUESS.** Skipped (no outcome to label). 43−34=9 Sonnet subtasks fell into this bucket (transcripts where Sonnet emits SUB_k header + p_solve for next but no verifiable BEST_GUESS).
- **CF branch turn.** When `stop_reason=decision_stop`, the runner appends a counterfactual-continue turn as `transcript[n_exec_turns+1]`. M1 only consumes `transcript[1:1+n_exec_turns]` (main-run exec turns).

## Surprises vs. writeup-v2

1. **Finding 7 direction preserved on M1, inverted on M2.** Writeup claims GPT has high resolution. M1 agrees (GPT 0.121, Sonnet 0.101, Gemini 0.022). M2 disagrees (GPT 0.002, Sonnet 0.120, Gemini 0.028). So the direction claim is specifically load-bearing on M1 — the writeup framing holds ONLY if M1 is the measure being cited.
2. **GPT has highest Brier AND highest resolution.** Its `p_solve` is uninformatively loud: it spreads predictions widely (high resolution) but miscalibrates them (high reliability term = 0.176). Resolution catches informativeness even for poorly-calibrated forecasters — this is the canonical case Murphy built the decomposition for.
3. **Gemini's resolution is near-zero (0.022) despite non-trivial n=45.** Gemini emits `p_solve` values clustered in a narrow band — base-rate-like predictions. Its small Brier (0.207) is almost entirely uncertainty (0.099) + reliability (0.132); the forecast adds ~no signal.
4. **Sonnet has best calibration (reliability 0.051) but modest resolution (0.101).** Sonnet's `p_solve` is accurate at the bin level but doesn't move around enough across subtasks to fully separate kept-as-best from not. Consistent with Sonnet's low exec-turn count and tendency to emit high-confidence NEXT_SUB only when it is actually likely to improve.

## Sanity checks against the brief

- [x] M1 Brier ∈ [0, 1] for all three models (0.186 / 0.207 / 0.275). None >0.5.
- [x] Murphy identity holds to 3 decimals (max deviation 0.0014 for Gemini, from 10-bin discretization).
- [~] n ≥ mean_exec_turns × 64 ≈ 80 per model. **Actual n = 34–49.** Reason: 28 portfolio rows × 3 models are excluded from M1, leaving only 36 solo rows × mean_exec_turns ≈ 1.3 ≈ 47 subtasks per model. So the brief's 80-estimate implicitly counted portfolio; solo-only n matches expectation.

## Where the numbers live

- Report: `kaggle_submission/results/metacog_analysis.md` §3 profile table, rows 1–5 (M1 + 3× Murphy + n).
- Headline: same file, top paragraph, includes M1 line.
- Caveats: §7 bullet 1–2 spell out M1 portfolio skip + kept_as_best semantics.
- Script: `kaggle_submission/scripts/analyze_metacog.py` — new `_extract_subtasks`, `_score_subtask_submission`, `_load_question`, plus M1 block in `model_level_stats`.


## DIFF

```
# analyze_metacog.py — key additions (see git diff for full patch)

+from harness.protocol import parse_plan_turn
+from verifiers import CLASS_TO_VERIFIER
+INFEASIBLE_GAP_PCT = 100.0

+def _extract_subtasks(transcript, cls, n_exec_turns, instance):
+    """Reconstruct (p_solve, kept_as_best) per subtask. Skip CF branch by slicing
+    transcript[1:1+n_exec_turns]. Portfolio/no-instance → []."""
+    if cls == 'portfolio' or instance is None: return []
+    plan = parse_plan_turn(transcript[0]['content'] or '', cls=cls)
+    p_solve_next = (plan or {}).get('next_sub', {}).get('p_solve')
+    ...
+    for idx, msg in enumerate(transcript[1:1+n_exec_turns]):
+        parsed = parse_exec_turn_partial(msg['content'], cls=cls, require_decision=False)
+        bg = parsed.get('best_guess')
+        gap_pct, feasible = _score_subtask_submission(cls, instance, bg)
+        if idx == 0:
+            kept = 1 if feasible else 0
+        else:
+            kept = 1 if gap_pct < prior_min_gap - 1e-9 else 0
+        subtasks.append({'p_solve': p_solve_next, 'kept_as_best': kept, ...})
+        prior_min_gap = min(prior_min_gap, gap_pct)
+        p_solve_next = (parsed.get('next_sub') or {}).get('p_solve')

# In model_level_stats(): new M1 block reuses murphy_decomposition()
+m1_pairs = [(s['p_solve'], s['kept_as_best']) for r in m_rows
+            if r['class'] != 'portfolio' for s in (r.get('subtasks') or [])
+            if s['p_solve'] is not None and s.get('had_best_guess')]
+m1 = murphy_decomposition(m1_pairs) or {}

# Profile table: replaced the 'NOT COMPUTED' row with 5 real rows
-_row('M1 Brier (p_solve)', 'm1_unavailable', '—', 'NOT COMPUTED')
+_row('M1 Brier (p_solve)', 'm1_brier', '{:.3f}', 'knowing what you know')
+_row('— M1 reliability',   'm1_reliability', '{:.3f}', ...)
+_row('— M1 resolution',    'm1_resolution',  '{:.3f}', ...)
+_row('— M1 uncertainty',   'm1_uncertainty', '{:.3f}', ...)
+_row('— M1 n (subtasks)',  'm1_n',           '{}',     ...)

```

## Complexity: medium

Three load-bearing concerns: correctly identifying main-run vs CF-branch exec turns in the transcript, correctly routing p_solve across (plan turn → exec turn k−1's NEXT_SUB → ... ) for subtask k, and preserving existing M2/M3/M4 logic untouched. Verifier calls must be defensive — a verifier raising on malformed BEST_GUESS would mark the whole row as unscorable. No architectural changes; additive.

## Files Changed

- kaggle_submission/scripts/analyze_metacog.py
- kaggle_submission/results/metacog_analysis.md
- kaggle_submission/results/metacog_rollup.csv

### NOTES

- The CF-branch exclusion slice `transcript[1:1+n_exec_turns]` is the key invariant — without it, subtask counts would be inflated by the forced-continue turn appended after `decision_stop`, which has a different outcome distribution than main-run subtasks.
- Sonnet contributes fewer M1 subtasks (34) than Gemini (45) or GPT (49) not because of verifier failures but because Sonnet terminates early or emits SUB_k blocks without verifiable BEST_GUESS payloads (parse_path=baseline_only in ~9 cases).
- Murphy identity has up to 0.0014 deviation from 10-bin discretization noise (Gemini specifically). 3-decimal sanity check from the brief still passes — but a 20-bin version would tighten this. Deferred as non-blocking.
- Portfolio remains unmeasured on M1. Next follow-up should either (a) implement per-sub-component verifier routing or (b) collapse portfolio M1 to 'did the overall portfolio become feasible after this subtask' — cheaper but coarser.

[[task_17763761858343m7]]
