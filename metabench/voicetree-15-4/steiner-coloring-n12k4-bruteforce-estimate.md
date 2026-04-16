---
color: green
isContextNode: false
agent_name: Ren
---
# Brute-force runtime estimate for seed-1 n=12,k=4

Measured the scale of the current generated graph and timed a representative sample of the real `_solve_exact()` loop body. The current `seed=1, n=12, k=4` graph has 32 edges, and the sample projects about 1.01 hours for one joint exact pass.

## Generated case inspected
Command:
```bash
python - <<'PY'
from steiner_coloring_instance import _generate_candidate
villages, terminals, edges, interference_pairs = _generate_candidate(seed=1, n=12, k=4, n_terminals=3)
print('terminals', terminals)
print('edge_count', len(edges))
print('interference_count', len(interference_pairs))
PY
```

Observed facts:
```text
terminals ('Port', 'Rock', 'Cape')
edge_count 32
interference_count 8
```

## Combinatorics of the current solver
`_solve_exact()` loops over all edge masks.

Command:
```bash
python - <<'PY'
from math import comb
m = 32
relevant = sum(comb(m, r) for r in range(2, 12))
print('total_masks', (1<<m)-1)
print('subsets_with_2_to_11_edges', relevant)
print('fraction_with_2_to_11_edges', relevant/((1<<m)-1))
PY
```

Observed output:
```text
total_masks 4294967295
subsets_with_2_to_11_edges 236618660
fraction_with_2_to_11_edges 0.05509207492114326
```

## Representative loop-body timing
Command:
```bash
python - <<'PY'
import random, time
from steiner_coloring_gold import _is_connected_tree, _solve_exact_coloring
from steiner_coloring_instance import _generate_candidate, SteinerColoringInstance

seed = 1
villages, terminals, edges, interference_pairs = _generate_candidate(seed=seed, n=12, k=4, n_terminals=3)
instance = SteinerColoringInstance(seed=seed, n=12, k=4, villages=villages, terminals=terminals, edges=edges, interference_pairs=interference_pairs, baseline_answer={}, baseline_cost=0, cable_only_answer={}, cable_only_cost=0, optimal_answer={}, optimal_cost=0, problem_statement='')

m = len(edges)
order = instance.village_order
color_cache = {}
samples = 5_000_000
rng = random.Random(0)
accepted = 0
color_calls = 0
start = time.perf_counter()
for _ in range(samples):
    mask = rng.randrange(1, 1 << m)
    edge_count = mask.bit_count()
    if edge_count < len(terminals) - 1 or edge_count >= len(villages):
        continue
    chosen = [edges[index] for index in range(len(edges)) if mask & (1 << index)]
    active = set(terminals)
    for edge in chosen:
        active.add(edge.u)
        active.add(edge.v)
    if edge_count != len(active) - 1:
        continue
    if not _is_connected_tree(active, chosen):
        continue
    active_key = tuple(sorted(active, key=lambda village: order[village]))
    if active_key not in color_cache:
        color_cache[active_key] = _solve_exact_coloring(instance, active_key)
        color_calls += 1
    accepted += 1
elapsed = time.perf_counter() - start
rate = samples / elapsed
print('samples', samples)
print('elapsed_s', elapsed)
print('sample_rate_masks_per_s', rate)
print('accepted_tree_masks', accepted)
print('color_calls', color_calls)
print('projected_total_seconds', ((1 << m) - 1) / rate)
print('projected_total_hours', (((1 << m) - 1) / rate) / 3600)
PY
```

Observed output:
```text
samples 5000000
elapsed_s 4.226584916003048
sample_rate_masks_per_s 1182988.180615651
accepted_tree_masks 16779
color_calls 157
projected_total_seconds 3630.6087967546828
projected_total_hours 1.0085024435429675
```

## Conclusion
One `solve_joint_optimum()` pass is projected at about `1.01 hours` on this machine for the current seed-1 graph.

supports [[steiner-coloring-n12k4-exact-solve-verdict]]
