---
color: green
isContextNode: false
agent_name: John
---
# HCH runner timeout defaults bumped to 40-min ceiling

Patched task-timeout=2400s, idle-wait=60s, sleep-between=15s defaults in all 3 runner scripts. CLI overrides intact. `--help` confirmed new defaults.

## Files Changed

| File | Was | Now |
|------|-----|-----|
| `run_hch_hle12.py` | task-timeout=180, idle-wait=25, sleep-between=20 | task-timeout=2400, idle-wait=60, sleep-between=15 |
| `run_hch_hle12_with_model.py` (temp) | task-timeout=240, idle-wait=25, sleep-between=25 | task-timeout=2400, idle-wait=60, sleep-between=15 |
| `run_flashlite.py` (temp) | task-timeout=90, idle-wait=20, sleep-between=10 | task-timeout=2400, idle-wait=60, sleep-between=15 |

## Sanity check
```
--idle-wait IDLE_WAIT    Seconds to wait for kernel idle (default 60)
--task-timeout TASK_TIMEOUT  Seconds timeout per task (default 2400)
--sleep-between SLEEP_BETWEEN  Seconds to sleep between tasks (default 15)
```

## Bridge-level flag
`kernel_bridge.py::JupyterKernelBridge.run()` has its own default of `timeout_seconds=30.0`, but every runner script passes the argparse value explicitly — so bridge default is never used in practice. No change needed, but note it if someone calls the bridge directly.

## DIFF

```
--- run_hch_hle12.py
+def run_one_task(bridge, task_file, timeout_s: float = 2400.0) -> dict:  # Default 2400s — HLE questions can take up to 40 min on strong models
-def run_one_task(bridge, task_file, timeout_s: float = 180.0) -> dict:
...
-    ap.add_argument("--idle-wait", type=float, default=25.0, ...)
+    ap.add_argument("--idle-wait", type=float, default=60.0, ...)
-    ap.add_argument("--task-timeout", type=float, default=180.0, ...)
+    ap.add_argument("--task-timeout", type=float, default=2400.0, ...)  # Default 2400s — HLE questions can take up to 40 min on strong models
-    ap.add_argument("--sleep-between", type=float, default=20.0, ...)
+    ap.add_argument("--sleep-between", type=float, default=15.0, ...)
```

```
--- run_hch_hle12_with_model.py
-def run_one_task(..., timeout_s: float = 240.0) -> dict:
+def run_one_task(..., timeout_s: float = 2400.0) -> dict:  # Default 2400s ...
-    ap.add_argument("--idle-wait", default=25.0)
+    ap.add_argument("--idle-wait", default=60.0)
-    ap.add_argument("--task-timeout", default=240.0)
+    ap.add_argument("--task-timeout", default=2400.0)  # Default 2400s ...
-    ap.add_argument("--sleep-between", default=25.0)
+    ap.add_argument("--sleep-between", default=15.0)
```

```
--- run_flashlite.py
-def run_one_task(..., timeout_s: float = 90.0) -> dict:
+def run_one_task(..., timeout_s: float = 2400.0) -> dict:  # Default 2400s ...
-    ap.add_argument("--idle-wait", default=20.0)
+    ap.add_argument("--idle-wait", default=60.0)
-    ap.add_argument("--task-timeout", default=90.0)
+    ap.add_argument("--task-timeout", default=2400.0)  # Default 2400s ...
-    ap.add_argument("--sleep-between", default=10.0)
+    ap.add_argument("--sleep-between", default=15.0)
```

## Complexity: low

Pure constant/default changes in argparse and function signatures — no logic changes.

## Files Changed

- kaggle/scripts/run_hch_hle12.py
- kaggle/scripts/run_hch_hle12_with_model.py
- kaggle/scripts/run_flashlite.py

### NOTES

- run_hch_hle12_with_model.py and run_flashlite.py are marked 'DO NOT CHECK IN — temporary script' — patched in place per task spec, but not to be committed.
- kernel_bridge.py::run() has a standalone default of 30s — irrelevant for current runners (all pass explicit timeout), but would bite anyone calling the bridge directly.

[[task_1776255847412icn]]
