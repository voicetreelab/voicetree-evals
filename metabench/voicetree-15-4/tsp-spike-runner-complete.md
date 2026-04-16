---
color: green
isContextNode: false
agent_name: Lou
---
# TSP spike runner complete: 27-row sweep + final analysis

STATUS: DONE. Completed the local TSP spike end-to-end across 3 models x 3 arms x 3 seeds, merged the campaign artifacts into a deduped 27-row JSONL, and ran the final analyzer. Applied one runner-side protocol fix before the sweep: strict `SUB_n` enforcement on exec turns plus spec-shaped cost fields in the injected stats prompt.

## Final artifact
- Final merged JSONL: `/Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/results/spike_20260416_merged_final.jsonl`
- Row count: `27`

## Final `analyze.py` output
```text
model  arm  n  mean_gap  mean_wall_s  mean_score  mean_brier  turn1_died  killed  downward  errors
gemini-2.5-flash      exhaustive  3       19.65       216.83       78.18      118.96  0           0       1         0
gemini-2.5-flash      greedy      3       17.24       170.69       81.06       49.62  0           0       2         0
gemini-2.5-flash      smart       3       11.88       480.09       83.32       94.59  0           0       3         0
gemini-2.5-pro        exhaustive  3        7.98       569.01       86.33     2360.53  0           0       0         0
gemini-2.5-pro        greedy      3        9.74       148.90       88.78      327.78  0           0       0         0
gemini-2.5-pro        smart       3        4.40       320.35       92.40     1470.43  0           0       0         0
gemini-3.1-pro-preview  exhaustive  3        1.24       330.40       95.45     4101.73  0           0       0         0
gemini-3.1-pro-preview  greedy      3        1.26       298.76       95.76     3362.99  0           0       0         0
gemini-3.1-pro-preview  smart       3        1.79       274.07       95.47     4060.42  0           0       0         0
```

## Key observations
- `gemini-3.1-pro-preview` dominated route quality and objective score overall. Best mean score was `greedy = 95.76`; all three arms were near-ceiling on TSP-25.
- `gemini-2.5-pro` showed the clearest smart-arm advantage: `smart` beat both `greedy` and `exhaustive` on mean score (`92.40` vs `88.78` vs `86.33`) and on mean gap (`4.40%` vs `9.74%` vs `7.98%`).
- `gemini-2.5-flash` also improved under `smart` on mean gap and score, but it paid for that with much higher mean wall time (`480s`).
- The smart arm did **not** dominate for the strongest model. On `gemini-3.1-pro-preview`, `greedy` slightly outscored `smart` because the task is easy enough that extra deliberation mostly adds time penalty.
- Across the full 27 rows, stop behavior was stable: `26` rows ended with `subtask_stop`; `1` row ended with `subtask_parse_fail` (`gemini-2.5-flash` greedy seed 1). No `turn1_died` and no timeout kills fired in the final campaign.
- Calibration remained noisy and often poor. The strongest model still posted extremely bad Brier scores despite excellent tours, which suggests the declared-gap field is not a reliable self-assessment measure in this prompt format.

## Prediction checks
- `50%` chance the sweep needs >=1 code fix before completion: **hit**. One runner-side protocol fix was needed before the successful sweep.
- `40%` chance at least one model 404s on initial ID: **miss** for this run. No live model-ID failure occurred after verifying the current Gemini model list.
- `60%` chance the smart arm shows a visibly different Pareto point: **partially hit**. Clear for `gemini-2.5-pro` and `gemini-2.5-flash`; not true for `gemini-3.1-pro-preview` where the task appears too easy.

## Design note carried upward
The run completed under the locked three-arm spec, but the numbers reinforce the simplification critique: for a main benchmark leaderboard, a **single canonical objective-optimizing prompt** is likely cleaner. Keep `greedy/exhaustive/smart` only as an ablation layer rather than the primary benchmark structure.

## Learnings
- I first tried a single serial 27-row sweep. That was the wrong execution shape because long exhaustive rows monopolized the queue; I switched to one live process per model family so expensive rows only blocked their own slice.
- The easy mistake for a successor is to treat long quiet periods as hangs. In this harness, silence often just means the model is consuming a large execution-turn budget before the next row is flushed.
- The strongest current belief after finishing the run is: the harness is operationally stable enough for end-to-end sweeps, but TSP-25 is already near-ceiling for `gemini-3.1-pro-preview`, so benchmark-design conclusions should not be overfit to that model's arm behavior.

## DIFF

```
diff --git a/metabench/hch/metagame/protocol.py b/metabench/hch/metagame/protocol.py
@@
-def parse_exec_turn(text: str) -> dict[str, Any] | None:
+def parse_exec_turn(text: str, expected_subtask_id: int | None = None) -> dict[str, Any] | None:
@@
-    if best_guess is None or p_correct is None or decision is None:
+    if best_guess is None or p_correct is None or decision is None or subtask_id is None:
+        return None
+    if expected_subtask_id is not None and subtask_id != expected_subtask_id:
         return None
@@
-def format_exec_prompt(
+def format_exec_prompt(
     turn_number: int,
     previous_turn: dict[str, Any],
     elapsed_s: float,
     baseline_tour: list[int],
+    subtask_budget_s: int,
 ) -> str:
@@
-        f"total_tok={_fmt_token(prev_total)}\n"
-        f"CUMULATIVE: wall={elapsed_s:.1f}s / {TOTAL_BUDGET_S}s, remaining={remaining_s:.1f}s\n"
-        f"SUBTASK BUDGET: {SUBTASK_BUDGET_S}s per turn (hard kill).\n"
+        "cost=$NA\n"
+        f"CUMULATIVE: wall={elapsed_s:.1f}s / {TOTAL_BUDGET_S}s, cost=$NA\n"
+        f"LOCAL_USAGE: total_tok={_fmt_token(prev_total)}, remaining={remaining_s:.1f}s\n"
+        f"SUBTASK BUDGET: {subtask_budget_s}s per turn (hard kill).\n"
@@
-        exec_parsed = None if exec_response["timed_out"] else parse_exec_turn(exec_response["text"])
+        exec_parsed = (
+            None
+            if exec_response["timed_out"]
+            else parse_exec_turn(exec_response["text"], expected_subtask_id=next_sub["id"])
+        )
```

## Complexity: low

One small protocol hardening patch plus execution/orchestration work to complete the sweep and merge artifacts. No structural refactor.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/protocol.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/results/spike_20260416_pro_seeds23.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/results/spike_20260416_flash_3x3.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/results/spike_20260416_gemini31_3x3.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/results/spike_20260416_merged_final.jsonl

### NOTES

- The main operational bottleneck was long execution turns, especially in exhaustive arms, not startup failures or env issues.
- Luis produced a companion research-assessment node at `tsp-spike-partial-assessment-extended.md` and remains open for human review as requested.
- No live `run_spike.py` processes remain after completion.

## Related

- [tsp-spike-partial-results-snapshot](tsp-spike-partial-results-snapshot.md)
- [tsp-spike-partial-assessment-extended](tsp-spike-partial-assessment-extended.md)
- [tsp-spike-arm-rationale-clarification](tsp-spike-arm-rationale-clarification.md)

[[task_1776317933629sza]]
