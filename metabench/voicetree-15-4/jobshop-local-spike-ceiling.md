---
color: green
isContextNode: false
agent_name: Meg
---
# Jobshop local spike: exact-solve ceiling

Implemented `jobshop_spike/` as an isolated local flowshop spike, ran the full 3-model × 3-seed sweep, and saved results to `hch/metagame/jobshop_spike/results/jobshop_20260416_165232.jsonl`.
All 9 runs hit 0.0% gap in one execution turn by explicitly invoking Johnson's rule; no visible Python-solver attempts or multi-turn replanning appeared.

## STATUS
DONE-WITH-CAVEATS

Final JSONL: `/Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike/results/jobshop_20260416_165232.jsonl`

## Predictions vs outcome
- Claim: 65% at least one Gemini 2.5 Pro run emits a Python solver / code fence. Outcome: false. Detector found zero visible solver attempts across all 9 runs.
- Claim: 50% the canonical prompt produces visible metacog signal. Outcome: false. Every run stopped at turn 2 after exactly one execution subtask.
- Claim: 40% `n=12` is too easy for Gemini 3. Outcome: true, and stronger: it was too easy for all three tested models.
- Claim: 30% this becomes the recommended Kaggle problem class over TSP. Outcome: false for the current F2||Cmax formulation.

## Summary table
| model | mean gap_pct | mean makespan | mean wall_s | mean $score | mean Brier | protocol flags |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| gemini-2.5-pro | 0.00 | 159.67 | 73.60 | 99.26 | 19.39 | turn1_died=0, parse_fail=0, killed=0, revised_downward=0 |
| gemini-2.5-flash | 0.00 | 159.67 | 66.50 | 99.34 | 19.72 | turn1_died=0, parse_fail=0, killed=0, revised_downward=0 |
| gemini-3.1-pro-preview | 0.00 | 159.67 | 52.54 | 99.47 | 0.84 | turn1_died=0, parse_fail=0, killed=0, revised_downward=0 |

Per-seed baseline difficulty:
- Seed 1: baseline 149, gold 145, baseline gap 2.759%
- Seed 2: baseline 166, gold 165, baseline gap 0.606%
- Seed 3: baseline 182, gold 169, baseline gap 7.692%

## Required questions
1. Did any model try to just write a Python solver?
No visible attempt. Detection scanned every raw turn for code fences and Python markers (` ``` `, `def ...(`, `import ...`, `itertools`, `for ... in range(`, `python`). All 9 runs were negative.

2. Is the single canonical prompt producing visible metacog signal?
No. Evidence:
- `stop_turn = 2` for all 9/9 runs.
- `decision_trace = ["continue", "stop"]` for all 9/9 runs.
- First planned subtask was always some variant of `Apply Johnson's Rule ...`; there was no second execution turn, so no adaptive replanning was visible.

3. Does the problem differentiate the three models, or is it still ceiling-y on Gemini 3?
It is fully ceilinged for all three models, not just Gemini 3. Accuracy, stop-turn, and protocol-failure metrics are identical; only wall time and declared-gap/Brier differ.

4. Compared to TSP-25 spike: harder/easier/same? Better or worse metacog differentiator?
Easier overall. It is better than TSP only on the narrow question of visible code-output resistance, but worse as a metacog differentiator because all three models recognized the exact polynomial-time solution immediately and solved every seed in one execution step.

## Representative evidence
- Gemini 2.5 Pro, seed 1, plan turn: `This is a two-machine flow shop scheduling problem, solvable to optimality with Johnson's algorithm ...`
- Gemini 2.5 Flash, seed 1, plan turn: `Apply Johnson's Rule to determine the optimal job sequence ...`
- Gemini 3.1 Pro Preview, seed 1, plan turn: `Apply Johnson's Rule to find the optimal sequence`

## Kaggle-port recommendations
- Keep the natural-language rendering and single canonical prompt. Those parts ran cleanly and did suppress visible code emission.
- Do not port the current two-machine flowshop class. Switch to a genuinely coupled multi-machine job shop, ideally the previously recommended 4x5 MVP tier or 5x6 frontier tier, where there is no cheap named exact rule.
- Pre-filter generated instances so the shipped baseline is materially suboptimal. Seed 2 only had a 0.606% baseline gap, which leaves almost no budget-metagame headroom even before the model solves optimally.

## Learnings
1. Tried to reuse the parent `protocol.py` directly, then switched to a local mirror in `jobshop_spike/protocol.py` because the shared module is hard-wired to TSP tours and arm prompts.
2. Future agents should not infer that natural-language framing alone prevents algorithmic collapse. The model can still name and execute the exact scheduling rule without emitting code.
3. The important belief update is that `F2||Cmax` is the wrong abstraction for this benchmark. The promising direction remains the earlier coupled multi-machine job-shop family, not a two-machine flowshop with Johnson-optimal structure.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike/__init__.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike/jobshop_instance.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike/render_nl.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike/prompt.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike/protocol.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike/analyze.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike/run_spike.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/jobshop_spike/results/jobshop_20260416_165232.jsonl

### NOTES

- Used the locally validated model id `gemini-3.1-pro-preview` from the prior TSP spike instead of the task text's ambiguous `gemini-3-pro-preview`.
- Visible NL framing removed code-fence / Python-output behavior, but it did not stop algorithmic collapse because the instance class transparently advertises Johnson's rule.
- Gemini SDK emitted `thought_signature` warnings on some runs, so hidden-thinking activity may exist even though visible protocol behavior was one-shot.

## Related

- [jobshop-spike-evidence-and-sizing](jobshop-spike-evidence-and-sizing.md)
- [kaggle-budget-metagame-design](kaggle-budget-metagame-design.md)

[[task_1776322014921rcv]]
