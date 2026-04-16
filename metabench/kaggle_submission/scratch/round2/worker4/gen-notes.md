# Worker 4 Generation Notes

- rows_written: 12
- output: `kaggle_submission/scratch/round2/worker4/questions.partial.jsonl`
- probe_ids_by_cell: ['ve_hard_seed10', 'mwis_hard_seed5', 'mwis_hard_seed9', 'mwis_hard_seed13']

## ve hard requested 10-12
- requested `ve_hard_seed10` -> actual `ve_hard_seed10`; builder note: Used exact posterior as gold_objective. Set baseline_objective=0.5 as a trivial uninformed binary-probability baseline; ordering difficulty metadata remains inside instance.
  - gold wall_s: 0.71
- requested `ve_hard_seed11` -> actual `ve_hard_seed11`; builder note: Used exact posterior as gold_objective. Set baseline_objective=0.5 as a trivial uninformed binary-probability baseline; ordering difficulty metadata remains inside instance.
  - gold wall_s: 0.71
- requested `ve_hard_seed12` -> actual `ve_hard_seed12`; builder note: Used exact posterior as gold_objective. Set baseline_objective=0.5 as a trivial uninformed binary-probability baseline; ordering difficulty metadata remains inside instance.
  - gold wall_s: 0.71

## mwis hard requested 5-7
- requested `mwis_hard_seed5` -> actual `mwis_hard_seed5`; builder note: size fallback requested_n_nodes=120, realized_n_nodes=120
  - seed=5: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=6: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=7: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=8: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=9: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - gold wall_s: 0.09
- requested `mwis_hard_seed6` -> actual `mwis_hard_seed7`; builder note: size fallback requested_n_nodes=120, realized_n_nodes=120
  - seed=6: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=7: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=8: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=9: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=10: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=6: n_nodes=120 -> RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed
  - gold wall_s: 0.15
- requested `mwis_hard_seed7` -> actual `mwis_hard_seed8`; builder note: size fallback requested_n_nodes=120, realized_n_nodes=120
  - seed=7: skipped duplicate actual_seed
  - seed=8: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=9: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=10: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=11: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=7: skipped duplicate actual_seed for size fallback n_nodes=120
  - gold wall_s: 0.03

## mwis hard requested 8-10
- requested `mwis_hard_seed8` -> actual `mwis_hard_seed9`; builder note: size fallback requested_n_nodes=120, realized_n_nodes=150
  - seed=8: skipped duplicate actual_seed
  - seed=9: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=10: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=11: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=12: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=8: skipped duplicate actual_seed for size fallback n_nodes=120
  - gold wall_s: 0.21
- requested `mwis_hard_seed9` -> actual `mwis_hard_seed10`; builder note: size fallback requested_n_nodes=120, realized_n_nodes=120
  - seed=9: skipped duplicate actual_seed
  - seed=10: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=11: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=12: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=13: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=9: skipped duplicate actual_seed for size fallback n_nodes=120
  - gold wall_s: 0.14
- requested `mwis_hard_seed10` -> actual `mwis_hard_seed12`; builder note: size fallback requested_n_nodes=120, realized_n_nodes=180
  - seed=10: skipped duplicate actual_seed
  - seed=11: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=12: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=13: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=14: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=10: skipped duplicate actual_seed for size fallback n_nodes=120
  - seed=11: n_nodes=120 -> RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed
  - gold wall_s: 0.25

## mwis hard requested 11-13
- requested `mwis_hard_seed11` -> actual `mwis_hard_seed13`; builder note: size fallback requested_n_nodes=120, realized_n_nodes=120
  - seed=11: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=12: skipped duplicate actual_seed
  - seed=13: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=14: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=15: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=11: n_nodes=120 -> RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed
  - seed=12: skipped duplicate actual_seed for size fallback n_nodes=120
  - gold wall_s: 0.04
- requested `mwis_hard_seed12` -> actual `mwis_hard_seed16`; builder note: size fallback requested_n_nodes=120, realized_n_nodes=150
  - seed=12: skipped duplicate actual_seed
  - seed=13: skipped duplicate actual_seed
  - seed=14: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=15: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=16: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=12: skipped duplicate actual_seed for size fallback n_nodes=120
  - seed=13: skipped duplicate actual_seed for size fallback n_nodes=120
  - seed=14: n_nodes=120 -> RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed
  - seed=15: n_nodes=120 -> RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed
  - gold wall_s: 0.17
- requested `mwis_hard_seed13` -> actual `mwis_hard_seed14`; builder note: size fallback requested_n_nodes=100, realized_n_nodes=100
  - seed=13: skipped duplicate actual_seed
  - seed=14: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=15: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=16: skipped duplicate actual_seed
  - seed=17: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=140 produced bridge nodes that did not separate the graph when removed
  - seed=13: skipped duplicate actual_seed for size fallback n_nodes=120
  - seed=14: n_nodes=120 -> RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed
  - seed=15: n_nodes=120 -> RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed
  - seed=16: skipped duplicate actual_seed for size fallback n_nodes=120
  - seed=17: n_nodes=120 -> RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed
  - seed=13: skipped duplicate actual_seed for size fallback n_nodes=100
  - gold wall_s: 0.07
