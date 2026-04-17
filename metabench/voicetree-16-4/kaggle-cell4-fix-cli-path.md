---
title: Kaggle Cell 4 Fix — CLI path works, browser-edit chosen to protect live session
color: green
---
# Kaggle Cell 4 Fix — CLI path works, browser-edit chosen to protect live session

Task brief claimed `kaggle kernels push` API token was 401 — **stale.** Re-verified with `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle.json` (same key as `~/.kaggle/kaggle.json`): `kaggle kernels status manumasson/meta-hch-bench` returns a real status. Pulled kernel, patched the 1-line `_t.evaluate` fix locally in `/tmp/kaggle_pull/meta-hch-bench.ipynb`, staged but **did not push** — user had a 27-minute Interactive Session running and a push triggers a browser refresh prompt that likely kills the session. Handed the user the exact code block to paste instead.

## Two bugs, not one

Task brief only flagged the `_t.evaluate(kbench.llm, evaluation_data=df)` TypeError. While assisting, user hit a second error from the live cell:
```
_tasks = kbench.tasks()
TypeError: 'module' object is not callable
```
`kbench.tasks` is a module (contains `Task` class + helpers). Correct registry lookup is `kbench.client.registry.values()` — a dict of registered tasks. Either user live-edited and introduced it, or task-brief diagnosis missed it. Both fixes are needed together.

## Correct cell-4 block (copied to user clipboard)
```python
_tasks = [t for t in kbench.client.registry.values()]
if len(_tasks) != 1:
    raise RuntimeError(f"Expected exactly one registered @kbench.task, found {len(_tasks)}: {[t.name for t in _tasks]}")
_t = _tasks[0]
print(f"running .evaluate() over {len(df)} rows against task={_t.name}")
result = _t.evaluate(evaluation_data=df, llm=[kbench.llm])
print(f"aggregate result: {result}")
```

## Browser-automation attempts (for future agents)
Monaco editor sits in iframe `notebook-editor-cells` on origin `kkb-production.jupyter-proxy.kaggle.net`. From top-frame `kaggle.com`:
- `javascript_tool` cannot cross the origin boundary — confirmed
- `computer.left_click` at viewport (500, 500) **does** focus Monaco (saw caret appear inside code)
- `computer.key("cmd+alt+f")` goes to top-frame event handler, not Monaco — it opens Kaggle's "Active Events" panel instead of Monaco replace
- `zoom` region tool cannot capture cross-origin iframe content (returns white)
- Screenshot tool *does* capture iframe content (OS-level), but its pixel grid (1568x773) is scaled relative to viewport (1640x809) by ~0.955×, and the `computer.click` coordinate input is in the same ~scaled system

Never reached a working Monaco shortcut path. CLI route would have been much faster if tried first.

## Paths
- Pulled notebook + metadata: `/tmp/kaggle_pull/`
- Patched ipynb ready to push: `/tmp/kaggle_pull/meta-hch-bench.ipynb`
- Original backup: `/tmp/kaggle_pull/meta-hch-bench.ipynb.bak`
- Local cell-3 reference: `metabench/kaggle_submission/kaggle/cell3_subset_evaluate.py`

## For the next agent
**What to believe:** the Kaggle CLI auth is fine for this account. Always `kaggle kernels status` before trusting a prior agent's claim that it's down.

**What they'll get wrong:** opening Monaco find/replace via keyboard from outside the iframe. Shortcuts route to Kaggle's top frame, not Monaco. Either click deep inside the iframe to focus Monaco AND then rely that subsequent keys still route there (unreliable), or just use the CLI.

**Non-obvious:** `kbench.tasks` (plural) is a module; `kbench.task` (singular) is the decorator factory. `kbench.client.registry` is the dict of tasks registered via the decorator.

**Session preservation:** `kaggle kernels push` creates a new version without directly killing running Interactive Sessions, but the browser editor tab typically prompts a refresh to pull the new version — refresh usually disconnects the session. If user has a warm session, prefer in-browser paste over CLI push.
