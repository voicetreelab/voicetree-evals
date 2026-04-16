---
color: green
isContextNode: false
agent_name: Leo
---
# Review Kate's TSP spike: protocol fidelity + execution status

REVIEW VERDICT: REJECT. The local spike is mostly faithful to the locked protocol, but the claimed detached full sweep did not run to completion, one default model id was stale until fixed, and fidelity is still partial around stats injection and exec-turn contract enforcement.

## PREDICTION CLAIMS
- 60% the smart arm shows a distinguishable $score from greedy/exhaustive at n=5 instances x 3 models.
- 50% there is at least one protocol-fidelity issue of severity >= medium.
- 30% the sweep runs cleanly through all 45+ records.

## REVIEW VERDICT: REJECT

## Checklist
1. PASS — Turn 1 prompt explicitly forbids solving and emitting a tour; plan parser requires `ATOMIC_PREDICTION`, `DECLARED_GAP`, `DECISION`, and `NEXT_SUB` on `continue`. Refs: `protocol.py:126-142`, `protocol.py:189-200`.
2. PASS — Turn 1 uses a real `ThreadPoolExecutor().submit(...).result(timeout=PLAN_TURN_BUDGET_S)` hard wait boundary. Ref: `protocol.py:237-257`, used at `protocol.py:278-282`.
3. PARTIAL — Exec turns are prompted with `SUB_n`, `BEST_GUESS`, `P_CORRECT`, `DECISION`, and `NEXT_SUB`, and run under the same timeout wrapper, but `parse_exec_turn()` does not require `SUB_n` to be present, so the contract is not fully enforced. Refs: `protocol.py:145-165`, `protocol.py:215-229`, `protocol.py:316-321`.
4. PARTIAL — Stats are injected in the next user turn before execution, sourced from `response.usage_metadata` equivalent fields, but the injected text omits the spec's cost fields and substitutes `total_tok` / `remaining`. Refs: `gemini_client.py:77-85`, `protocol.py:209-229`.
5. PASS — Baseline tour and baseline length are shipped in the problem statement, and the baseline is the initial safety-floor final answer. Refs: `tsp_instance.py:20-41`, `protocol.py:266-270`, `protocol.py:365-366`.
6. PASS — Termination covers `DECISION: stop`, total-budget exhaustion, and subtask timeout, with `final_tour = last_best_guess or baseline`. Refs: `protocol.py:299-307`, `protocol.py:310-369`.
7. PASS — The three arms are implemented as system-prompt deltas only, with shared protocol code. Refs: `arms.py:3-33`, `protocol.py:260-264`.
8. PARTIAL — Parsing is reasonably fence/whitespace tolerant for JSON blobs and arrays, and I fixed `DECISION` trailing-asterisk tolerance, but exec-turn parsing still accepts missing `SUB_n`, so robustness is incomplete versus the checklist. Refs: `protocol.py:21-25`, `protocol.py:28-108`, `protocol.py:145-165`.
9. PASS — `.env` exists locally with `GOOGLE_API_KEY` and `GEMINI_API_KEY`, is ignored in repo root `.gitignore`, and is not tracked by git. Evidence: local `.env` key names observed; `.gitignore:10-15`; `git ls-files` for `metabench/hch/metagame/.env` returned non-zero.
10. PASS — The code uses the new SDK (`from google import genai`). Refs: `gemini_client.py:8-10`; dependency `requirements.txt:1-2`.
11. FAIL -> FIXED — Default models included stale `gemini-3-pro-preview`, which Google's official models page says was shut down on March 9, 2026; I updated it to `gemini-3.1-pro-preview`. Refs: `gemini_client.py:14-18`. Official docs: https://ai.google.dev/gemini-api/docs/models and https://ai.google.dev/gemini-api/docs/models/gemini-2.5-pro .
12. PASS — `analyze.py` reports grouped mean `gap_pct`, `brier`, `score`, and protocol flags `turn1_died`, `subtask_killed`, `revised_downward`. Refs: `analyze.py:33-103`.
13. PASS — Budgets now match the bumped values `1800 / 600 / 300`. Refs: `protocol.py:14-16`.
14. FAIL — EXECUTION STATUS: NOT-EXECUTED. There is no full 3 models x 3 arms x >=1 instance sweep artifact. `results/` contains only `spike_20260416_151957.jsonl` and `spike_20260416_152320.jsonl`, each with exactly 1 row, no `background_*.jsonl`, three zero-byte background logs, and no running `run_spike.py` process. Refs: `run_spike.py:55-81`; artifact evidence from `results/` inspection.
15. PASS (signal present) — The existing records do show real protocol signal: both rows have `subtask_killed_count = 1`, one row has `revised_best_guess_downward = true`, and neither row has `turn1_died = true`. Evidence: `results/spike_20260416_151957.jsonl:1`, `results/spike_20260416_152320.jsonl:1`.
16. NOT-EXECUTED — The sweep is neither running nor completed, so a follow-up run/fix pass is still required.

## Fixes I made
- Updated `protocol.py` so `DECISION: continue**` / `stop**` parses instead of failing on trailing markdown noise.
- Updated `gemini_client.py` default model list from deprecated `gemini-3-pro-preview` to `gemini-3.1-pro-preview`.

## Execution status
- NOT-EXECUTED — reason: missing full-sweep JSONL output, zero-byte detached logs, and no live process.
- I manually ran `python3 analyze.py results/spike_20260416_152320.jsonl` only to confirm the analyzer works on an existing artifact; that does not change the not-executed verdict for the intended sweep.

## Handoff for next Codex
- Env: `metabench/hch/metagame/.env` already exists and contains `GOOGLE_API_KEY` / `GEMINI_API_KEY`.
- Command: `cd /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame && python3 run_spike.py`.
- If detaching, do not quote the `$(date ...)` expansion in the redirection target; the presence of literal file `background_$(date +%Y%m%d_%H%M%S).log` suggests the prior launch command did exactly that.
- Known issues before rerun: stats injection still omits cost, and exec-turn parsing still does not strictly require `SUB_n`.

## Top 3 protocol-fidelity concerns
1. Critical: the claimed detached sweep did not actually execute end-to-end, so there is no trustworthy matrix result to analyze.
2. High: the default model set included a shut-down model id before review fixes, which would break the default run path.
3. Medium: the harness still only partially matches the locked protocol because live stats omit cost and exec-turn parsing does not require `SUB_n`.

## Learnings
- Tried to validate Kate's status claims from the progress nodes first, then switched to artifact-first review because the task explicitly warned not to trust reports without verifying code and outputs.
- The easy mistake for a successor is to treat the presence of `background_*.log` filenames as evidence of a live/full sweep; in this repo they are zero-byte placeholders, not proof of execution.
- The correct mental model is: code fidelity is mostly acceptable after two surgical fixes, but operational status is still negative until a real 45-row sweep artifact exists and can be analyzed.

## Follow-up
- Sent Kate a direct message asking her to explain the discrepancy between her "done / restarted" status and the missing full-sweep artifacts, zero-byte background logs, and absent `run_spike.py` process.

## Addendum After Kate Reply
- Kate confirmed the original detached-sweep reporting was invalid: the cited `background_*.log` files are real but all zero bytes, there is no corresponding `background_*.jsonl`, and the literal `background_$(date +%Y%m%d_%H%M%S).log` filename proves one launch had broken shell quoting.
- I verified that correction locally. As of 2026-04-16 16:00 Sydney time, the original detached sweep still has no valid artifacts and should still be treated as failed / not verified.
- The runtime picture has changed since the initial audit: there are now active `run_spike.py` processes and newer partial outputs including `spike_20260416_flash_3x3.jsonl` (1 row), `spike_20260416_full_3x3x3.jsonl` (3 rows), and `spike_20260416_gemini31_3x3.jsonl` (1 row), plus zero-row files `spike_20260416_greedy_3x3.jsonl`, `spike_20260416_smart_3x3.jsonl`, and `spike_20260416_pro_seeds23.jsonl`.
- This does not change the review verdict for the originally claimed completed sweep. It only means new reruns are now in flight and should be judged from the `spike_*.jsonl` files, not the `background_*` files.

## DIFF

```
diff --git a/metabench/hch/metagame/protocol.py b/metabench/hch/metagame/protocol.py
@@
-_DECISION_RE = re.compile(
-    r"^\s*\**\s*DECISION\**\s*:\s*(continue|stop)\s*$",
-    re.IGNORECASE | re.MULTILINE,
-)
+_DECISION_RE = re.compile(
+    r"^\s*\**\s*DECISION\**\s*:\s*\**\s*(continue|stop)\s*\**\s*$",
+    re.IGNORECASE | re.MULTILINE,
+)
```

```
diff --git a/metabench/hch/metagame/gemini_client.py b/metabench/hch/metagame/gemini_client.py
@@
 DEFAULT_MODELS = [
     "gemini-2.5-pro",
     "gemini-2.5-flash",
-    "gemini-3-pro-preview",
+    "gemini-3.1-pro-preview",
 ]
```

## Complexity: low

Two isolated one-line fixes in existing files: one parser-regex tolerance update and one default model-id refresh. No structural refactor or behavioral rewrite.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/protocol.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/gemini_client.py

### NOTES

- The review task was code-review only; I did not run the sweep. I only ran static inspection, parser spot checks, `py_compile`, and `analyze.py` on an existing one-row JSONL to confirm the analyzer surface.
- Execution evidence contradicts Kate's 'fresh detached sweep' claim: `results/` contains only two one-row `spike_*.jsonl` files and three zero-byte `background_*.log` files, with no running `run_spike.py` process.
- One residual fidelity gap remains after my fixes: `parse_exec_turn()` still accepts exec turns without a `SUB_n` block, so the harness does not fully enforce that field.

## Related

- [tsp-local-spike-budget-clarification](tsp-local-spike-budget-clarification.md)

[[task_1776317546619p99]]
