---
color: green
isContextNode: false
agent_name: Fei
---
# S0 VE Port

Ported Bayesian variable-elimination generation and verification into `kaggle_submission/` as a self-contained verifier plus thin generator wrapper, and added a deterministic seed-1 medium smoke fixture. The required smoke command passed with `OK`, and hard-mode generation also sanity-checked at requested/actual size `26/26`.

## Sources Read
- `voicetree-16-4/task_177634927058110l.md`
- `voicetree-16-4/kaggle-submission-filetree.md`
- `voicetree-16-4/kaggle-submission-design.md`
- `hch/bayesnet_ve/bayesnet_instance.py`
- `hch/bayesnet_ve/protocol.py`
- `voicetree-15-4/bayesnet-ve-proposal.md`
- `voicetree-15-4/bayesian-ve-v1-gemini3pro-seed1-result-2026-04-16.md`

## Files Written
- `kaggle_submission/verifiers/ve.py`
- `kaggle_submission/generators/ve.py`
- `kaggle_submission/tests/fixtures/ve_smoke.json`

## Smoke Result
Command:
```bash
python -c "from generators.ve import generate; from verifiers.ve import verify; inst = generate(seed=1, difficulty='medium'); import json; fixture = json.load(open('tests/fixtures/ve_smoke.json')); s, f, d = verify(fixture['instance'], fixture['gold_submission']); assert f and s == 0.0, (s, f, d); print('OK')"
```
Output:
```text
OK
```

Hard-mode sanity:
```bash
python -c "from generators.ve import generate; inst = generate(seed=1, difficulty='hard'); print(inst['requested_total_variables']); print(inst['total_variables'])"
```
Output:
```text
26
26
```

## BEST_GUESS Schema
```json
{
  "p_query_given_evidence": 0.49014481565752194,
  "ordering_used": ["B6", "A1", "B5", "BR01", "C5", "C1", "A4", "C4", "B2", "C3", "B3", "A3", "A2", "A5", "BR12", "D0"],
  "peak_factor_size_self_report": 6
}
```

## Decisions
- `medium` maps to requested 22 variables and keeps the source spike's special escalation path when 22-variable candidates are too easy; `hard` maps to requested 26 variables.
- `verify()` returns posterior relative error percentage as `gap_pct`: `100 * abs(p_hat - p*) / p*`. Invalid BEST_GUESS payloads return `(100.0, False, {failure_reason})` so the shared solo scoring path still bottoms out cleanly.
- The verifier is self-contained and does not import `hch/`; the generator is only a thin wrapper over `build_instance_payload()` because v2 ships verifiers, not generators, inside the Kaggle bundle.
- The generated instance payload keeps rich metadata (`exact_posterior`, gold/baseline orderings, heuristic summaries, `problem_statement`) so question-freezing can derive `gold_objective` / `baseline_objective` later without another utility file.

## Learnings
1. Tried to avoid duplication by leaning on the existing `hch/bayesnet_ve` module, but switched to a self-contained verifier because the v2 architecture embeds `verifiers/*.py` into `task.py` and cannot rely on repo-relative imports at Kaggle runtime.
2. A future agent could incorrectly score VE with the original spike's log-gap-in-nats as the top-level `gap_pct`. The shared harness contract is percentage-shaped, so I kept log-gap only in verifier details and exposed relative probability error as the primary gap.
3. The source spike only auto-escalates when the requested size is 22 and min-fill peak size stays `<= 4`; that asymmetry is intentional and preserved here, so `hard` currently means "start at 26" rather than "run a second escalation policy."

## Files Changed

- kaggle_submission/generators/ve.py
- kaggle_submission/verifiers/ve.py
- kaggle_submission/tests/fixtures/ve_smoke.json

### NOTES

- No files outside the VE write path were modified.
- `tests/fixtures/ve_smoke.json` is generated from the new implementation's deterministic seed-1 medium payload, so the smoke fixture stays aligned with the code.
- The worktree contains many unrelated user/agent changes; this port ignored them and did not revert anything.

[[task_177634927058110l]]
