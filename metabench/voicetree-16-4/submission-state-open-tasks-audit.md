---
color: green
isContextNode: false
agent_name: Amy
---
# Submission State + Open Tasks for Full 206-row Kaggle Submission

Audit of what's shipped vs. what's open for submitting the full >200q benchmark today (deadline 2026-04-17 09:59 AEST). Bench is at 206 rows, kernel v5 COMPLETE, but Kaggle production sweep has only covered 26/206 rows and only Gemini cleanly. Cover image + benchmark collection slug + writeup final cleanup are missing.

## Shipped
- `kaggle_submission/questions.jsonl` — **206 rows** (26 → 120 R1 → 206 R2). 4 short of 210 due to MWIS hard bridge-check generator limits.
- Local probe results — `kaggle_submission/results/full/` 64 question dirs × 3 models (~192 runs).
- Kaggle kernel — v5 COMPLETE at `kaggle.com/code/manumasson/meta-hch-bench`; `meta_hch_bench` task registered.
- GitHub repo — `voicetreelab/meta-hch-bench` private, 6 commits.
- Writeup — `kaggle_submission/writeup-v2.md` 517 lines; overnight pilot results inserted above Phase-1 tables.
- Analysis — `OVERNIGHT-RESULTS.md`, `discussion-of-results.md`.

## Kaggle production run — incomplete
Only 26 canonical rows swept via Jupyter proxy. Only Gemini clean; Claude + GPT 503'd on every canonical row (provider availability, not config — both smoked fine on 1-row probes).
- Gemini: 26/26 rows, 100% parse, 73% feasibility, mean 62.52, $13.74 total.
- Claude: 26/26 fast-fail 503, all `baseline_only`.
- GPT: same.
- Extra Claude rows (~180) from mid-run questions.jsonl expansion are on disk but out-of-scope for the 26-row canonical report.

## Open tasks (must) — to submit full 206
1. Kaggle prod sweep over remaining 180 rows × 3 models (or retry 206 × Claude + GPT). 503 likely load-based — retry path exists.
2. Cover image (mandatory per Kaggle rules) — none found under `kaggle_submission/`.
3. Kaggle Benchmark collection under a non-clashing slug (e.g. `meta-hch-benchmark`) with `meta_hch_bench` attached via UI. Current `/benchmarks/manumasson/meta-hch-bench` 404s (kernel slug clash).
4. Finalize `writeup-v2.md` — strip the "Self-Evaluation Prompt for Gemini" wrapper at the top; verify ≤1500 words / 3 pages / Metacognition template.
5. Repo publicity flip + "Submit Entry" click on Kaggle.

## Open tasks (quality) — headline signal
6. Portfolio 0/48 feasibility — every portfolio row infeasible across all 3 models. Hypothesis: TSP sub-component format violations. Kills headline portfolio scoring.
7. Sonnet × MWIS-hard 0/6 stop=error — reproducible, likely max_tokens/reasoning-depth.
8. GPT feasible-but-low-score on graphcol/steiner.

## Numbers referenced
- questions.jsonl row count: 206 (verified via `wc -l`).
- Local results/full subdirs: 64 (verified via `ls`).
- kaggle_production file counts: 412 Claude / 52 Gemini / 52 GPT (mixed canonical + drift).
- Latest commit: `33b36da discussion of overnight results + writeup-v2 update`.

parent [[factory-plan_2_0]]
