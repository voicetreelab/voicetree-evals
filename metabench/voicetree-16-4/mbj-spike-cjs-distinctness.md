---
color: blue
isContextNode: false
agent_name: Bob
---
# MBJ vs CJS — distinct classes, not a duplicate

The brief asked explicitly: if MBJ is functionally identical to CJS, stop and report. Answer: MBJ is genuinely distinct. Different objective (makespan + weighted tardiness vs. makespan only), different constraint structure (single shop vs. two coupled factories), different hidden generator mechanics (job families/bridges/outliers).

# MBJ is distinct from CJS

Compared `hch/masked_block_jobshop/jobshop_instance.py` against `kaggle_submission/generators/cjs.py` and `kaggle_submission/verifiers/cjs.py`.

| Axis | CJS | MBJ |
|---|---|---|
| **Structure** | Two coupled factories A → B; each job has two ordered routes on disjoint machine pools (MA*/MB*) | Single job-shop; all jobs share one machine pool M1..Mk |
| **Objective** | `makespan` only | `20 * makespan + Σ_j w_j * max(0, C_j − d_j)` (weighted tardiness added) |
| **Per-job data** | `factory_a: [...], factory_b: [...]` | `operations: [...], due_date, tardiness_weight` |
| **Coupling** | Factory B job Jx cannot start until Factory A job Jx fully completes | No inter-job coupling |
| **Generator hidden structure** | Random disjoint-machine route sampling with uniqueness | 4 hidden **job families**; bridge jobs couple families; outlier jobs 3× longer; family-weighted preferred-machine sampling |
| **Pre-flight** | `min_baseline_gap_pct` only | `min_baseline_gap_pct` + `min/max_heuristic_spread_pct` (ensures the instance has a non-trivial range of solutions across 4 different dispatch rules) |
| **Schedule schema** | `{"factory_a": {...}, "factory_b": {...}, "makespan": int}` | `{"machines": {...}, "makespan": int, "weighted_tardiness": int, "objective": int}` |

## Why the schemas are not interchangeable

CJS's verifier parses `schedule["factory_a"]` and `schedule["factory_b"]` and checks the A→B coupling on every job. It has no concept of due dates or weighted tardiness. Passing an MBJ `machines`-keyed schedule would immediately fail the CJS key-extraction (`KeyError: factory_a`) — and even if you renamed the key, CJS scores against `makespan` alone, so MBJ's tardiness signal is invisible.

## Pilot lineage note

`cjs` is documented internally as MBJ's **descendant** (simplified / two-factory variant). Porting MBJ adds back the tardiness dimension and family-coupling structure that CJS dropped. Different problem, not a redundant port.

justifies the port [[mbj-spike-landed]]
