# Worker 4 Generation Notes

- rows_written: 12
- output: `kaggle_submission/scratch/round1/worker4/questions.partial.jsonl`
- probe_ids_by_cell: ['mwis_medium_seed3', 'mwis_medium_seed7', 'mwis_medium_seed10', 've_medium_seed2']

## mwis medium requested 2-4
- requested `mwis_medium_seed2` -> actual `mwis_medium_seed3`
  - seed=2: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed [0.39s]
  - gold wall_s: 0.04
- requested `mwis_medium_seed3` -> actual `mwis_medium_seed4`
  - seed=3: skipped duplicate actual_seed
  - gold wall_s: 0.03
- requested `mwis_medium_seed4` -> actual `mwis_medium_seed5`
  - seed=4: skipped duplicate actual_seed
  - gold wall_s: 0.09
## mwis medium requested 5-7
- requested `mwis_medium_seed5` -> actual `mwis_medium_seed7`
  - seed=5: skipped duplicate actual_seed
  - seed=6: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed [0.29s]
  - gold wall_s: 0.13
- requested `mwis_medium_seed6` -> actual `mwis_medium_seed8`
  - seed=6: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed [0.29s]
  - seed=7: skipped duplicate actual_seed
  - gold wall_s: 0.03
- requested `mwis_medium_seed7` -> actual `mwis_medium_seed9`
  - seed=7: skipped duplicate actual_seed
  - seed=8: skipped duplicate actual_seed
  - gold wall_s: 0.22
## mwis medium requested 8-10
- requested `mwis_medium_seed8` -> actual `mwis_medium_seed10`
  - seed=8: skipped duplicate actual_seed
  - seed=9: skipped duplicate actual_seed
  - gold wall_s: 0.10
- requested `mwis_medium_seed9` -> actual `mwis_medium_seed12`
  - seed=9: skipped duplicate actual_seed
  - seed=10: skipped duplicate actual_seed
  - seed=11: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed [0.33s]
  - gold wall_s: 0.28
- requested `mwis_medium_seed10` -> actual `mwis_medium_seed13`
  - seed=10: skipped duplicate actual_seed
  - seed=11: RuntimeError: failed to generate a treewidth MWIS instance meeting the pre-flight checks: attempt 35 at n=180 produced bridge nodes that did not separate the graph when removed [0.37s]
  - seed=12: skipped duplicate actual_seed
  - gold wall_s: 0.04
## ve medium requested 2-4
- requested `ve_medium_seed2` -> actual `ve_medium_seed2`; builder note: Used exact posterior as gold_objective. Set baseline_objective=0.5 as a trivial uninformed binary-probability baseline; ordering difficulty metadata remains inside instance.
  - gold wall_s: 0.54
- requested `ve_medium_seed3` -> actual `ve_medium_seed3`; builder note: Used exact posterior as gold_objective. Set baseline_objective=0.5 as a trivial uninformed binary-probability baseline; ordering difficulty metadata remains inside instance.
  - gold wall_s: 0.54
- requested `ve_medium_seed4` -> actual `ve_medium_seed4`; builder note: Used exact posterior as gold_objective. Set baseline_objective=0.5 as a trivial uninformed binary-probability baseline; ordering difficulty metadata remains inside instance.
  - gold wall_s: 0.55
