from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from random import Random
from typing import Any

FREQ_PENALTY = 15
NAME_POOL = (
    "Port",
    "Bay",
    "Cliff",
    "Pine",
    "Rock",
    "Dune",
    "Mill",
    "Cape",
    "Harbor",
    "Grove",
    "Ridge",
    "Cove",
)


@dataclass(frozen=True)
class EdgeSpec:
    u: str
    v: str
    cost: int

    @property
    def key(self) -> tuple[str, str]:
        return canonical_edge(self.u, self.v)


@dataclass(frozen=True)
class SteinerColoringInstance:
    seed: int
    n: int
    k: int
    villages: tuple[str, ...]
    terminals: tuple[str, ...]
    edges: tuple[EdgeSpec, ...]
    interference_pairs: tuple[tuple[str, str], ...]
    baseline_answer: dict[str, Any]
    baseline_cost: int
    cable_only_answer: dict[str, Any] | None
    cable_only_cost: int | None
    optimal_answer: dict[str, Any] | None
    optimal_cost: int | None
    problem_statement: str

    @property
    def village_order(self) -> dict[str, int]:
        return {village: index for index, village in enumerate(self.villages)}

    @property
    def edge_lookup(self) -> dict[tuple[str, str], int]:
        return {edge.key: edge.cost for edge in self.edges}


def canonical_edge(u: str, v: str) -> tuple[str, str]:
    if u == v:
        raise ValueError(f"self loops are not allowed: {u}")
    return (u, v) if u < v else (v, u)


def ordered_edges(edge_keys: set[tuple[str, str]] | tuple[tuple[str, str], ...], villages: tuple[str, ...]) -> list[tuple[str, str]]:
    order = {village: index for index, village in enumerate(villages)}
    return sorted(edge_keys, key=lambda item: (order[item[0]], order[item[1]]))


def active_villages_for_edges(terminals: tuple[str, ...], edge_keys: set[tuple[str, str]] | tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    active = set(terminals)
    for u, v in edge_keys:
        active.add(u)
        active.add(v)
    return tuple(sorted(active))


def interference_graph(
    active_villages: tuple[str, ...] | list[str],
    interference_pairs: tuple[tuple[str, str], ...],
) -> dict[str, set[str]]:
    active = set(active_villages)
    graph = {village: set() for village in active}
    for u, v in interference_pairs:
        if u in active and v in active:
            graph[u].add(v)
            graph[v].add(u)
    return graph


def greedy_color_active(
    active_villages: tuple[str, ...],
    villages: tuple[str, ...],
    interference_pairs: tuple[tuple[str, str], ...],
) -> dict[str, int]:
    graph = interference_graph(active_villages, interference_pairs)
    order = {village: index for index, village in enumerate(villages)}
    assignment: dict[str, int] = {}
    nodes = sorted(active_villages, key=lambda village: (-len(graph[village]), order[village]))
    for village in nodes:
        blocked = {assignment[neighbor] for neighbor in graph[village] if neighbor in assignment}
        color = 1
        while color in blocked:
            color += 1
        assignment[village] = color
    return {village: assignment[village] for village in sorted(assignment, key=lambda name: order[name])}


def build_instance(
    seed: int,
    n: int = 8,
    k: int = 3,
    n_terminals: int = 3,
    min_baseline_gap_pct: float = 10.0,
    require_coupling: bool = True,
    max_generation_attempts: int = 80,
    skip_exact_gold: bool = False,
) -> SteinerColoringInstance:
    if n > len(NAME_POOL):
        raise ValueError(f"n={n} exceeds available village-name pool ({len(NAME_POOL)})")
    from verify import verify_answer

    if not skip_exact_gold:
        from steiner_coloring_gold import solve_cable_only_then_color, solve_joint_optimum

    last_reason = "no attempt made"
    for attempt in range(max_generation_attempts):
        if seed == 1 and n == 8 and k == 3 and n_terminals == 3 and attempt == 0:
            villages, terminals, edges, interference_pairs = _canonical_spec()
        else:
            attempt_seed = seed if attempt == 0 else seed * 10_000 + attempt
            villages, terminals, edges, interference_pairs = _generate_candidate(
                seed=attempt_seed,
                n=n,
                k=k,
                n_terminals=n_terminals,
            )

        baseline_answer = build_baseline_answer(villages, terminals, edges, interference_pairs)
        stub = SteinerColoringInstance(
            seed=seed,
            n=n,
            k=k,
            villages=villages,
            terminals=terminals,
            edges=edges,
            interference_pairs=interference_pairs,
            baseline_answer=baseline_answer,
            baseline_cost=0,
            cable_only_answer={},
            cable_only_cost=0,
            optimal_answer={},
            optimal_cost=0,
            problem_statement="",
        )

        baseline_check = verify_answer(stub, baseline_answer)
        if not baseline_check.feasible or baseline_check.computed_cost is None or baseline_check.normalized_answer is None:
            raise RuntimeError(f"internal error: baseline answer is infeasible: {baseline_check.failure_reason}")

        baseline_cost = baseline_check.computed_cost
        if skip_exact_gold:
            instance_stub = SteinerColoringInstance(
                seed=seed,
                n=n,
                k=k,
                villages=villages,
                terminals=terminals,
                edges=edges,
                interference_pairs=interference_pairs,
                baseline_answer=baseline_check.normalized_answer,
                baseline_cost=baseline_cost,
                cable_only_answer=None,
                cable_only_cost=None,
                optimal_answer=None,
                optimal_cost=None,
                problem_statement="",
            )
            problem_statement = render_problem(instance_stub)
            return SteinerColoringInstance(
                seed=seed,
                n=n,
                k=k,
                villages=villages,
                terminals=terminals,
                edges=edges,
                interference_pairs=interference_pairs,
                baseline_answer=baseline_check.normalized_answer,
                baseline_cost=baseline_cost,
                cable_only_answer=None,
                cable_only_cost=None,
                optimal_answer=None,
                optimal_cost=None,
                problem_statement=problem_statement,
            )

        cable_only_answer, cable_only_cost = solve_cable_only_then_color(stub)
        optimal_answer, optimal_cost = solve_joint_optimum(stub)

        cable_check = verify_answer(stub, cable_only_answer)
        optimal_check = verify_answer(stub, optimal_answer)
        if not cable_check.feasible or cable_check.computed_cost != cable_only_cost:
            raise RuntimeError(f"internal error: cable-only exact solution failed verification: {cable_check.failure_reason}")
        if not optimal_check.feasible or optimal_check.computed_cost != optimal_cost:
            raise RuntimeError(f"internal error: optimal exact solution failed verification: {optimal_check.failure_reason}")

        baseline_gap_pct = 100.0 * (baseline_cost - optimal_cost) / optimal_cost
        coupling_gap = cable_only_cost - optimal_cost
        if seed == 1 and attempt == 0:
            accepted = True
        else:
            accepted = baseline_gap_pct >= min_baseline_gap_pct
            if require_coupling:
                accepted = accepted and coupling_gap > 0
        if not accepted:
            last_reason = (
                f"baseline_gap_pct={baseline_gap_pct:.2f}, coupling_gap={coupling_gap}"
            )
            continue

        instance_stub = SteinerColoringInstance(
            seed=seed,
            n=n,
            k=k,
            villages=villages,
            terminals=terminals,
            edges=edges,
            interference_pairs=interference_pairs,
            baseline_answer=baseline_check.normalized_answer,
            baseline_cost=baseline_cost,
            cable_only_answer=cable_check.normalized_answer or cable_only_answer,
            cable_only_cost=cable_only_cost,
            optimal_answer=optimal_check.normalized_answer or optimal_answer,
            optimal_cost=optimal_cost,
            problem_statement="",
        )
        problem_statement = render_problem(instance_stub)
        return SteinerColoringInstance(
            seed=seed,
            n=n,
            k=k,
            villages=villages,
            terminals=terminals,
            edges=edges,
            interference_pairs=interference_pairs,
            baseline_answer=baseline_check.normalized_answer,
            baseline_cost=baseline_cost,
            cable_only_answer=cable_check.normalized_answer or cable_only_answer,
            cable_only_cost=cable_only_cost,
            optimal_answer=optimal_check.normalized_answer or optimal_answer,
            optimal_cost=optimal_cost,
            problem_statement=problem_statement,
        )

    raise RuntimeError(
        "failed to generate a Steiner-coloring instance with enough headroom after "
        f"{max_generation_attempts} attempts; last rejection was {last_reason}"
    )


def build_baseline_answer(
    villages: tuple[str, ...],
    terminals: tuple[str, ...],
    edges: tuple[EdgeSpec, ...],
    interference_pairs: tuple[tuple[str, str], ...],
) -> dict[str, Any]:
    root = terminals[0]
    edge_lookup = {edge.key: edge.cost for edge in edges}
    selected: set[tuple[str, str]] = set()
    for terminal in terminals[1:]:
        selected.update(shortest_path_edges(root, terminal, edge_lookup))
    spanning = _kruskal_spanning_tree(selected, edge_lookup)
    pruned = _prune_nonterminal_leaves(spanning, terminals)
    active = active_villages_for_edges(terminals, pruned)
    frequencies = greedy_color_active(active, villages, interference_pairs)
    return {
        "edges": [list(edge) for edge in ordered_edges(pruned, villages)],
        "frequencies": frequencies,
    }


def shortest_path_edges(
    start: str,
    goal: str,
    edge_lookup: dict[tuple[str, str], int],
) -> list[tuple[str, str]]:
    adjacency: dict[str, list[tuple[str, int]]] = {}
    for (u, v), cost in edge_lookup.items():
        adjacency.setdefault(u, []).append((v, cost))
        adjacency.setdefault(v, []).append((u, cost))

    queue: list[tuple[int, str]] = [(0, start)]
    dist = {start: 0}
    prev: dict[str, str] = {}
    while queue:
        best_dist, node = heapq.heappop(queue)
        if node == goal:
            break
        if best_dist != dist.get(node):
            continue
        for neighbor, cost in adjacency.get(node, []):
            candidate = best_dist + cost
            if candidate < dist.get(neighbor, math.inf):
                dist[neighbor] = candidate
                prev[neighbor] = node
                heapq.heappush(queue, (candidate, neighbor))

    if goal not in dist:
        raise RuntimeError(f"no path between {start} and {goal}")

    path_edges: list[tuple[str, str]] = []
    cursor = goal
    while cursor != start:
        parent = prev[cursor]
        path_edges.append(canonical_edge(cursor, parent))
        cursor = parent
    path_edges.reverse()
    return path_edges


def render_problem(instance: SteinerColoringInstance) -> str:
    edge_lines = [
        f"- {edge.u}-{edge.v}: cost {edge.cost}"
        for edge in ordered_edge_specs(instance.edges, instance.villages)
    ]
    interference_lines = [f"- {u} / {v}" for u, v in ordered_edges(instance.interference_pairs, instance.villages)]
    baseline_summary = solution_summary(instance, instance.baseline_answer, instance.baseline_cost)
    return f"""Coastal Emergency scenario:
Storm season is coming. You need to wire a resilient emergency communication network across coastal villages.

You may choose any subset of the available cable links, but the chosen cable network must be a single connected tree that includes every required terminal village.
Every village that lies in your chosen network is active and must be assigned a radio frequency.
If an interference pair is active on both ends, those two villages must use different frequencies.

Objective:
total_cost = sum(cable costs used) + {FREQ_PENALTY} * num_frequencies_used

Villages:
- {", ".join(instance.villages)}

Required terminals:
- {", ".join(instance.terminals)}

Available cable links:
{chr(10).join(edge_lines)}

Interference pairs:
{chr(10).join(interference_lines)}

Rules:
- Your cable choice must be a tree, not a cyclic network.
- All required terminals must lie in one connected component.
- Frequencies matter only for active villages in the chosen network.
- If you stop immediately or fail to produce a valid answer, the baseline below is what gets scored.

Baseline total cost: {instance.baseline_cost}
Baseline answer summary:
{baseline_summary}
"""


def solution_summary(
    instance: SteinerColoringInstance,
    answer: dict[str, Any],
    total_cost: int | None = None,
) -> str:
    edge_lookup = instance.edge_lookup
    raw_edges = {
        canonical_edge(*edge)
        for edge in answer.get("edges", [])
        if isinstance(edge, list | tuple) and len(edge) == 2
    }
    ordered = ordered_edges(raw_edges, instance.villages)
    edge_cost = sum(edge_lookup[edge] for edge in ordered if edge in edge_lookup)
    active = active_villages_for_edges(instance.terminals, raw_edges)
    frequencies = answer.get("frequencies", {})
    active_freqs = {village: frequencies[village] for village in active if village in frequencies}
    used_colors = sorted(set(active_freqs.values()))
    total = total_cost if total_cost is not None else edge_cost + FREQ_PENALTY * len(used_colors)
    edge_bits = ", ".join(f"{u}-{v}({edge_lookup[(u, v)]})" for u, v in ordered)
    freq_bits = ", ".join(f"{village}={active_freqs.get(village, '?')}" for village in active)
    return (
        f"Edges: {edge_bits}\n"
        f"Active villages: {', '.join(active)}\n"
        f"Frequencies: {freq_bits}\n"
        f"Edge cost: {edge_cost}\n"
        f"Frequencies used: {len(used_colors)}\n"
        f"Total cost: {total}"
    )


def ordered_edge_specs(edges: tuple[EdgeSpec, ...], villages: tuple[str, ...]) -> list[EdgeSpec]:
    order = {village: index for index, village in enumerate(villages)}
    return sorted(edges, key=lambda edge: (order[edge.u], order[edge.v]))


def _canonical_spec() -> tuple[tuple[str, ...], tuple[str, ...], tuple[EdgeSpec, ...], tuple[tuple[str, str], ...]]:
    villages = ("Port", "Bay", "Cliff", "Pine", "Rock", "Dune", "Mill", "Cape")
    terminals = ("Port", "Rock", "Cape")
    edges = (
        EdgeSpec("Port", "Bay", 3),
        EdgeSpec("Port", "Cliff", 8),
        EdgeSpec("Bay", "Cliff", 3),
        EdgeSpec("Bay", "Pine", 5),
        EdgeSpec("Cliff", "Pine", 4),
        EdgeSpec("Cliff", "Rock", 4),
        EdgeSpec("Pine", "Rock", 3),
        EdgeSpec("Pine", "Dune", 4),
        EdgeSpec("Rock", "Dune", 2),
        EdgeSpec("Rock", "Mill", 5),
        EdgeSpec("Dune", "Mill", 3),
        EdgeSpec("Dune", "Cape", 4),
        EdgeSpec("Mill", "Cape", 2),
    )
    interference_pairs = tuple(
        ordered_edges(
            {
                canonical_edge("Port", "Bay"),
                canonical_edge("Port", "Cliff"),
                canonical_edge("Bay", "Cliff"),
                canonical_edge("Cliff", "Rock"),
                canonical_edge("Pine", "Rock"),
                canonical_edge("Rock", "Mill"),
                canonical_edge("Mill", "Cape"),
                canonical_edge("Dune", "Cape"),
            },
            villages,
        )
    )
    return villages, terminals, edges, interference_pairs


def _generate_candidate(
    *,
    seed: int,
    n: int,
    k: int,
    n_terminals: int,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[EdgeSpec, ...], tuple[tuple[str, str], ...]]:
    rng = Random(seed)
    villages = tuple(NAME_POOL[:n])
    points = {village: (rng.randint(0, 30), rng.randint(0, 30)) for village in villages}
    complete_edges: list[tuple[int, tuple[str, str]]] = []
    for index, u in enumerate(villages):
        for v in villages[index + 1 :]:
            x1, y1 = points[u]
            x2, y2 = points[v]
            cost = max(2, int(round(math.hypot(x1 - x2, y1 - y2))))
            complete_edges.append((cost, canonical_edge(u, v)))

    mst_edges = _minimum_spanning_tree(villages, complete_edges)
    selected = set(mst_edges)
    neighbors: dict[str, list[tuple[int, str]]] = {village: [] for village in villages}
    for cost, (u, v) in complete_edges:
        neighbors[u].append((cost, v))
        neighbors[v].append((cost, u))
    for village in villages:
        for _, other in sorted(neighbors[village], key=lambda item: (item[0], item[1]))[:k]:
            selected.add(canonical_edge(village, other))

    edge_costs = {edge: cost for cost, edge in complete_edges}
    edges = tuple(
        EdgeSpec(u=edge[0], v=edge[1], cost=edge_costs[edge])
        for edge in ordered_edges(selected, villages)
    )
    terminals = tuple(sorted(rng.sample(list(villages), n_terminals), key=lambda item: villages.index(item)))
    interference_pairs = _build_interference_pairs(rng, villages, terminals, edge_costs)
    return villages, terminals, edges, interference_pairs


def _minimum_spanning_tree(
    villages: tuple[str, ...],
    complete_edges: list[tuple[int, tuple[str, str]]],
) -> set[tuple[str, str]]:
    parent = {village: village for village in villages}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: str, right: str) -> bool:
        root_left = find(left)
        root_right = find(right)
        if root_left == root_right:
            return False
        parent[root_right] = root_left
        return True

    selected: set[tuple[str, str]] = set()
    for _, (u, v) in sorted(complete_edges, key=lambda item: (item[0], item[1][0], item[1][1])):
        if union(u, v):
            selected.add(canonical_edge(u, v))
        if len(selected) == len(villages) - 1:
            break
    return selected


def _build_interference_pairs(
    rng: Random,
    villages: tuple[str, ...],
    terminals: tuple[str, ...],
    edge_costs: dict[tuple[str, str], int],
) -> tuple[tuple[str, str], ...]:
    root = terminals[0]
    seed_edges: set[tuple[str, str]] = set()
    for terminal in terminals[1:]:
        seed_edges.update(shortest_path_edges(root, terminal, edge_costs))
    active = list(active_villages_for_edges(terminals, seed_edges))
    if len(active) < 3:
        active = list(villages)

    interference: set[tuple[str, str]] = set()
    triangle_count = 2 if len(villages) >= 7 else 1
    rng.shuffle(active)
    used: set[str] = set()
    for _ in range(triangle_count):
        pool = [village for village in active if village not in used]
        if len(pool) < 3:
            pool = list(villages)
        anchor = pool[0]
        near = sorted(
            [village for village in villages if village != anchor],
            key=lambda village: (edge_costs.get(canonical_edge(anchor, village), 10_000), village),
        )
        trio = [anchor]
        for village in near:
            if village not in trio:
                trio.append(village)
            if len(trio) == 3:
                break
        if len(trio) == 3:
            used.update(trio)
            for index, u in enumerate(trio):
                for v in trio[index + 1 :]:
                    interference.add(canonical_edge(u, v))

    extras = sorted(edge_costs, key=lambda item: (edge_costs[item], item[0], item[1]))
    rng.shuffle(extras)
    for edge in extras:
        if len(interference) >= triangle_count * 3 + 2:
            break
        interference.add(edge)
    return tuple(ordered_edges(interference, villages))


def _kruskal_spanning_tree(
    edge_keys: set[tuple[str, str]],
    edge_lookup: dict[tuple[str, str], int],
) -> set[tuple[str, str]]:
    nodes = {node for edge in edge_keys for node in edge}
    parent = {node: node for node in nodes}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: str, right: str) -> bool:
        root_left = find(left)
        root_right = find(right)
        if root_left == root_right:
            return False
        parent[root_right] = root_left
        return True

    chosen: set[tuple[str, str]] = set()
    for edge in sorted(edge_keys, key=lambda item: (edge_lookup[item], item[0], item[1])):
        if union(edge[0], edge[1]):
            chosen.add(edge)
    return chosen


def _prune_nonterminal_leaves(
    edge_keys: set[tuple[str, str]],
    terminals: tuple[str, ...],
) -> set[tuple[str, str]]:
    adjacency: dict[str, set[str]] = {}
    for u, v in edge_keys:
        adjacency.setdefault(u, set()).add(v)
        adjacency.setdefault(v, set()).add(u)

    terminals_set = set(terminals)
    changed = True
    while changed:
        changed = False
        for village in list(adjacency):
            neighbors = adjacency.get(village, set())
            if village not in terminals_set and len(neighbors) == 1:
                neighbor = next(iter(neighbors))
                adjacency[neighbor].remove(village)
                if not adjacency[neighbor]:
                    adjacency.pop(neighbor)
                adjacency.pop(village)
                changed = True
    pruned: set[tuple[str, str]] = set()
    for u, neighbors in adjacency.items():
        for v in neighbors:
            if u < v:
                pruned.add((u, v))
    return pruned
