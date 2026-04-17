---
color: green
agent_name: Ayu
---

# Portfolio fix verification — seed14 across 3 local models

## Re-ran `portfolio_medium_seed14` on `gemini-flash-latest`, `claude-sonnet-4.6`, and `gpt-5.4-mini` after Amit's prompt/seeding fixes. Verdict: fixes worked; top-level feasibility improved from `0/3` to `3/3`, and the prior MWIS/Steiner schema failures disappeared.

| Model | Top-level before->after | CJS before->after | MWIS before->after | Steiner before->after | Score | wall_s | parse_path | stop_reason |
|---|---|---|---|---|---:|---:|---|---|
| `gemini-flash-latest` | `False -> True` | `True (none) -> True (none)` | `False (submission must be an object) -> True (none)` | `False (frequencies must be an object) -> True (none)` | `61.07` | `546.0` | `strict_protocol_cf` | `decision_stop` |
| `claude-sonnet-4.6` | `False -> True` | `True (none) -> True (none)` | `False (selected_vertices must be a list) -> True (none)` | `True (none) -> True (none)` | `38.81` | `511.9` | `strict_protocol_cf` | `decision_stop` |
| `gpt-5.4-mini` | `False -> True` | `True (none) -> True (none)` | `False (submission must be an object) -> True (none)` | `True (none) -> True (none)` | `41.29` | `19.4` | `strict_protocol_cf` | `decision_stop` |

## MWIS BEST_GUESS excerpts

All three final submissions came from `cf_parsed.best_guess`.

`gemini-flash-latest`
```json
{"selected_vertices":["V001","V010","V011","V013","V016","V029","V030","V035","V036","V041","V043","V045","V048","V050","V051","V052","V057","V059","V068","V069","V073","V074","V075","V077","V081","V085","V089","V090","V099"],"total_weight":354}
```

`claude-sonnet-4.6`
```json
{"selected_vertices":["V006","V010","V011","V013","V016","V017","V018","V019","V021","V029","V033","V035","V041","V045","V048","V049","V050","V051","V054","V057","V063","V065","V068","V069","V073","V074","V075","V077","V095","V099"],"total_weight":375}
```

`gpt-5.4-mini`
```json
{"selected_vertices":["V001","V010","V011","V013","V016","V029","V035","V036","V041","V045","V048","V049","V050","V051","V052","V057","V059","V068","V069","V073","V074","V075","V077","V081","V089","V090","V099"],"total_weight":348}
```

## Files Changed

- `kaggle_submission/results/runs/gemini-flash-latest/portfolio_medium_seed14.json` - generated rerun artifact
- `kaggle_submission/results/runs/claude-sonnet-4.6/portfolio_medium_seed14.json` - generated rerun artifact
- `kaggle_submission/results/runs/gpt-5.4-mini/portfolio_medium_seed14.json` - generated rerun artifact
- `voicetree-16-4/portfolio-fix-verification-seed14-3-local-models.md` - progress node

## DIFF

No manual production-code edits. This task only generated fresh run artifacts under `kaggle_submission/results/runs/`.

### NOTES

- All three reruns ended top-level feasible after one exec turn; the fix clearly repaired the broken portfolio output contract for this row.
- Feasibility improved, not necessarily score quality: Sonnet and GPT still returned feasible but weak CJS/Steiner solutions, which is acceptable for this verification task.
- Tried the prescribed serial reruns first and kept that approach; it matched the safety note about API quota contention and required no retries.
- Do not read `results/full/portfolio_medium_seed14/*.json` as the rerun output; those remain the old failing references.
- The non-obvious detail is that the final accepted submission lives under `cf_parsed.best_guess`, not `submission`, so follow-up inspections should read `final_submission_source` before quoting artifacts.

verification follow-up [[task_1776373751566rv9.md]]
