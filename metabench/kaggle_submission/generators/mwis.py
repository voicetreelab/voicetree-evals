from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
from random import Random
import time
from typing import Any

try:
    from ortools.sat.python import cp_model
except ImportError:  # pragma: no cover - exercised in dependency-blocked environments
    cp_model = None


DIFFICULTY_CONFIG = {
    "medium": {
        "n_nodes": 120,
        "min_baseline_gap_pct": 10.0,
        "max_generation_attempts": 36,
        "cp_time_limit_s": 120.0,
    },
    "hard": {
        "n_nodes": 140,
        "min_baseline_gap_pct": 10.0,
        "max_generation_attempts": 36,
        "cp_time_limit_s": 120.0,
    },
}


def _require_ortools() -> Any:
    if cp_model is None:
        raise RuntimeError(
            "ortools is not installed. Add ortools before generating MWIS instances."
        )
    return cp_model


@dataclass(frozen=True)
class SolveResult:
    answer: dict[str, Any]
    total_weight: int
    is_optimal: bool
    status_name: str
    wall_seconds: float


@dataclass(frozen=True)
class GenerationTuning:
    intra_block_p: float
    inter_block_p: float
    bridge_target_p: float
    bridge_offtarget_p: float
    bridge_count: int
    bridge_extra_target_prob: float
    decoy_bonus: int
    neighbor_bonus: int
    weight_scale: float


@dataclass(frozen=True)
class GeneratedCandidate:
    generation_seed: int
    attempt_index: int
    n_nodes: int
    vertices: tuple[str, ...]
    weights: dict[str, int]
    edges: tuple[tuple[str, str], ...]
    adjacency: dict[str, tuple[str, ...]]
    hidden_block_membership: dict[str, str]
    bridge_vertices: tuple[str, ...]
    bridge_targets: dict[str, tuple[str, ...]]
    decoy_vertices: tuple[str, ...]
    tuning: GenerationTuning


@dataclass(frozen=True)
class VerificationResult:
    is_feasible: bool
    verified_total_weight: int | None
    failure_reason: str | None
    normalized_answer: dict[str, Any] | None
    selected_count: int | None


@dataclass(frozen=True)
class MWISInstance:
    seed: int
    difficulty: str
    generation_seed: int
    requested_n_nodes: int
    n_nodes: int
    vertices: tuple[str, ...]
    weights: dict[str, int]
    edges: tuple[tuple[str, str], ...]
    adjacency: dict[str, tuple[str, ...]]
    baseline_answer: dict[str, Any]
    baseline_objective: int
    optimal_answer: dict[str, Any]
    optimal_objective: int
    optimal_proven: bool
    solver_status: str
    solver_wall_seconds: float
    baseline_gap_pct: float
    problem_statement: str
    hidden_block_membership: dict[str, str]
    bridge_vertices: tuple[str, ...]
    bridge_targets: dict[str, tuple[str, ...]]
    decoy_vertices: tuple[str, ...]
    tuning: GenerationTuning
    attempt_index: int

    @property
    def node_order(self) -> dict[str, int]:
        return {vertex: index for index, vertex in enumerate(self.vertices)}


def generate(seed: int, difficulty: str) -> dict[str, Any]:
    config = DIFFICULTY_CONFIG.get(difficulty)
    if config is None:
        allowed = ", ".join(sorted(DIFFICULTY_CONFIG))
        raise ValueError(f"unknown difficulty {difficulty!r}; expected one of {allowed}")

    instance = build_instance(seed=seed, difficulty=difficulty, **config)
    return _instance_to_json(instance)


def build_instance(
    *,
    seed: int,
    difficulty: str,
    n_nodes: int,
    min_baseline_gap_pct: float | None,
    max_generation_attempts: int,
    cp_time_limit_s: float,
) -> MWISInstance:
    size_queue = [n_nodes]
    if n_nodes == 120:
        size_queue.extend([150, 180])

    last_failure = "no candidate evaluated"
    for size_index, size in enumerate(size_queue):
        for attempt_index in range(max_generation_attempts):
            generation_seed = seed + size_index * 100_000 + attempt_index * 10_007
            tuning = _generation_tuning(size=size, attempt_index=attempt_index)
            candidate = _generate_candidate(
                generation_seed=generation_seed,
                attempt_index=attempt_index,
                n_nodes=size,
                tuning=tuning,
            )
            hidden_cut_check = _separator_stats(
                vertices=candidate.vertices,
                adjacency=candidate.adjacency,
                cut_vertices=set(candidate.bridge_vertices),
            )
            if not hidden_cut_check["did_separate"]:
                last_failure = (
                    f"attempt {attempt_index} at n={size} produced bridge nodes that did not separate "
                    "the graph when removed"
                )
                continue

            baseline_answer = build_baseline_answer(
                vertices=candidate.vertices,
                weights=candidate.weights,
                adjacency=candidate.adjacency,
            )
            stub = MWISInstance(
                seed=seed,
                difficulty=difficulty,
                generation_seed=generation_seed,
                requested_n_nodes=n_nodes,
                n_nodes=size,
                vertices=candidate.vertices,
                weights=candidate.weights,
                edges=candidate.edges,
                adjacency=candidate.adjacency,
                baseline_answer=baseline_answer,
                baseline_objective=baseline_answer["total_weight"],
                optimal_answer={},
                optimal_objective=0,
                optimal_proven=False,
                solver_status="",
                solver_wall_seconds=0.0,
                baseline_gap_pct=0.0,
                problem_statement="",
                hidden_block_membership=candidate.hidden_block_membership,
                bridge_vertices=candidate.bridge_vertices,
                bridge_targets=candidate.bridge_targets,
                decoy_vertices=candidate.decoy_vertices,
                tuning=candidate.tuning,
                attempt_index=attempt_index,
            )
            baseline_check = verify_answer(stub, baseline_answer)
            if not baseline_check.is_feasible or baseline_check.normalized_answer is None:
                raise RuntimeError(
                    f"internal error: baseline answer is infeasible: {baseline_check.failure_reason}"
                )

            solve_result = solve_exact_mwis(
                vertices=candidate.vertices,
                weights=candidate.weights,
                edges=candidate.edges,
                time_limit_s=cp_time_limit_s,
            )
            if not solve_result.is_optimal:
                last_failure = (
                    f"attempt {attempt_index} at n={size} did not prove optimal "
                    f"(status={solve_result.status_name}, best={solve_result.total_weight})"
                )
                continue

            baseline_total = baseline_check.verified_total_weight or baseline_answer["total_weight"]
            gap_pct = 100.0 * (solve_result.total_weight - baseline_total) / solve_result.total_weight
            if min_baseline_gap_pct is not None and gap_pct < min_baseline_gap_pct:
                last_failure = (
                    f"attempt {attempt_index} at n={size} had baseline gap only {gap_pct:.2f}%"
                )
                continue

            solved_stub = MWISInstance(
                seed=seed,
                difficulty=difficulty,
                generation_seed=generation_seed,
                requested_n_nodes=n_nodes,
                n_nodes=size,
                vertices=candidate.vertices,
                weights=candidate.weights,
                edges=candidate.edges,
                adjacency=candidate.adjacency,
                baseline_answer=baseline_check.normalized_answer,
                baseline_objective=baseline_total,
                optimal_answer=solve_result.answer,
                optimal_objective=solve_result.total_weight,
                optimal_proven=solve_result.is_optimal,
                solver_status=solve_result.status_name,
                solver_wall_seconds=solve_result.wall_seconds,
                baseline_gap_pct=gap_pct,
                problem_statement="",
                hidden_block_membership=candidate.hidden_block_membership,
                bridge_vertices=candidate.bridge_vertices,
                bridge_targets=candidate.bridge_targets,
                decoy_vertices=candidate.decoy_vertices,
                tuning=candidate.tuning,
                attempt_index=attempt_index,
            )
            optimal_check = verify_answer(solved_stub, solve_result.answer)
            if not optimal_check.is_feasible or optimal_check.verified_total_weight != solve_result.total_weight:
                raise RuntimeError(
                    f"internal error: optimal answer failed verification: {optimal_check.failure_reason}"
                )

            final_stub = MWISInstance(
                seed=seed,
                difficulty=difficulty,
                generation_seed=generation_seed,
                requested_n_nodes=n_nodes,
                n_nodes=size,
                vertices=candidate.vertices,
                weights=candidate.weights,
                edges=candidate.edges,
                adjacency=candidate.adjacency,
                baseline_answer=baseline_check.normalized_answer,
                baseline_objective=baseline_total,
                optimal_answer=optimal_check.normalized_answer or solve_result.answer,
                optimal_objective=solve_result.total_weight,
                optimal_proven=solve_result.is_optimal,
                solver_status=solve_result.status_name,
                solver_wall_seconds=solve_result.wall_seconds,
                baseline_gap_pct=gap_pct,
                problem_statement="",
                hidden_block_membership=candidate.hidden_block_membership,
                bridge_vertices=candidate.bridge_vertices,
                bridge_targets=candidate.bridge_targets,
                decoy_vertices=candidate.decoy_vertices,
                tuning=candidate.tuning,
                attempt_index=attempt_index,
            )
            return MWISInstance(
                seed=seed,
                difficulty=difficulty,
                generation_seed=generation_seed,
                requested_n_nodes=n_nodes,
                n_nodes=size,
                vertices=candidate.vertices,
                weights=candidate.weights,
                edges=candidate.edges,
                adjacency=candidate.adjacency,
                baseline_answer=baseline_check.normalized_answer,
                baseline_objective=baseline_total,
                optimal_answer=optimal_check.normalized_answer or solve_result.answer,
                optimal_objective=solve_result.total_weight,
                optimal_proven=solve_result.is_optimal,
                solver_status=solve_result.status_name,
                solver_wall_seconds=solve_result.wall_seconds,
                baseline_gap_pct=gap_pct,
                problem_statement=render_problem(final_stub),
                hidden_block_membership=candidate.hidden_block_membership,
                bridge_vertices=candidate.bridge_vertices,
                bridge_targets=candidate.bridge_targets,
                decoy_vertices=candidate.decoy_vertices,
                tuning=candidate.tuning,
                attempt_index=attempt_index,
            )

    raise RuntimeError(
        "failed to generate a treewidth MWIS instance meeting the pre-flight checks: "
        f"{last_failure}"
    )


def build_baseline_answer(
    *,
    vertices: tuple[str, ...],
    weights: dict[str, int],
    adjacency: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    selected: list[str] = []
    selected_set: set[str] = set()
    for vertex in sorted(vertices, key=lambda item: (-weights[item], -len(adjacency[item]), item)):
        if any(neighbor in selected_set for neighbor in adjacency[vertex]):
            continue
        selected.append(vertex)
        selected_set.add(vertex)
    total_weight = sum(weights[vertex] for vertex in selected)
    return {
        "selected_vertices": selected,
        "total_weight": total_weight,
    }


def solve_exact_mwis(
    *,
    vertices: tuple[str, ...],
    weights: dict[str, int],
    edges: tuple[tuple[str, str], ...],
    time_limit_s: float = 120.0,
) -> SolveResult:
    cp = _require_ortools()
    model = cp.CpModel()
    vertex_vars = {
        vertex: model.NewBoolVar(f"take_{vertex}")
        for vertex in vertices
    }
    for left, right in edges:
        model.Add(vertex_vars[left] + vertex_vars[right] <= 1)
    model.Maximize(sum(weights[vertex] * vertex_vars[vertex] for vertex in vertices))

    solver = cp.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_s
    solver.parameters.num_search_workers = 8
    start = time.monotonic()
    status = solver.Solve(model)
    wall_seconds = time.monotonic() - start
    selected_vertices = [vertex for vertex in vertices if solver.Value(vertex_vars[vertex])]
    total_weight = sum(weights[vertex] for vertex in selected_vertices)
    return SolveResult(
        answer={
            "selected_vertices": selected_vertices,
            "total_weight": total_weight,
        },
        total_weight=total_weight,
        is_optimal=(status == cp.OPTIMAL),
        status_name=solver.StatusName(status),
        wall_seconds=wall_seconds,
    )


def verify_answer(instance: MWISInstance, answer: dict[str, Any] | None) -> VerificationResult:
    if not isinstance(answer, dict):
        return VerificationResult(False, None, "answer must be an object", None, None)

    raw_vertices = answer.get("selected_vertices")
    if not isinstance(raw_vertices, list):
        return VerificationResult(False, None, "selected_vertices must be a list", None, None)

    raw_total_weight = answer.get("total_weight")
    try:
        claimed_total_weight = int(raw_total_weight)
    except Exception:
        return VerificationResult(False, None, "total_weight must be an integer", None, None)

    seen: set[str] = set()
    normalized_vertices: list[str] = []
    for raw_vertex in raw_vertices:
        if not isinstance(raw_vertex, str):
            return VerificationResult(False, None, "selected_vertices entries must be strings", None, None)
        vertex = raw_vertex.strip()
        if vertex not in instance.weights:
            return VerificationResult(False, None, f"unknown vertex {raw_vertex!r}", None, None)
        if vertex in seen:
            return VerificationResult(False, None, f"duplicate vertex {vertex}", None, None)
        seen.add(vertex)
        normalized_vertices.append(vertex)

    selected_set = set(normalized_vertices)
    for left, right in instance.edges:
        if left in selected_set and right in selected_set:
            return VerificationResult(
                False,
                None,
                f"selected set is not independent: edge {left}-{right} is internal",
                None,
                len(normalized_vertices),
            )

    verified_total_weight = sum(instance.weights[vertex] for vertex in normalized_vertices)
    if verified_total_weight != claimed_total_weight:
        return VerificationResult(
            False,
            None,
            f"claimed total_weight {claimed_total_weight} does not match computed {verified_total_weight}",
            None,
            len(normalized_vertices),
        )

    ordered_vertices = sorted(normalized_vertices, key=instance.node_order.__getitem__)
    return VerificationResult(
        True,
        verified_total_weight,
        None,
        {
            "selected_vertices": ordered_vertices,
            "total_weight": verified_total_weight,
        },
        len(ordered_vertices),
    )


def render_problem(instance: MWISInstance) -> str:
    vertex_entries = [f"{vertex}={instance.weights[vertex]}" for vertex in instance.vertices]
    edge_entries = [f"{left}-{right}" for left, right in instance.edges]
    baseline_summary = solution_summary(instance, instance.baseline_answer)
    return f"""Maximum weighted independent set on an undirected graph with {instance.n_nodes} vertices.

Objective:
- Choose a subset of vertices with no edge between any chosen pair.
- total_weight = sum(weights[v] for v in selected_vertices)
- Higher total_weight is better.

Vertex weights:
{_format_entries(vertex_entries, per_line=10)}

Edges:
{_format_entries(edge_entries, per_line=10)}

Constraints:
- `BEST_GUESS` must be valid JSON with keys `selected_vertices` and `total_weight`.
- Every selected vertex must appear at most once.
- No selected pair may share an edge.
- `total_weight` must equal the exact sum of the selected vertex weights.

A deterministic greedy baseline is provided below. If you stop immediately or fail to produce a valid answer, this baseline is what gets scored.
Baseline total_weight: {instance.baseline_objective}
Baseline summary:
{baseline_summary}
"""


def solution_summary(instance: MWISInstance, answer: dict[str, Any]) -> str:
    selected_vertices = answer.get("selected_vertices", [])
    if not isinstance(selected_vertices, list):
        selected_vertices = []
    total_weight = answer.get("total_weight", 0)
    try:
        total_weight_int = int(total_weight)
    except Exception:
        total_weight_int = 0
    return "\n".join(
        [
            f"Selected count: {len(selected_vertices)}",
            f"Total weight: {total_weight_int}",
            "Selected vertices:",
            _format_entries([str(vertex) for vertex in selected_vertices], per_line=12),
        ]
    )


def _instance_to_json(instance: MWISInstance) -> dict[str, Any]:
    return {
        "class": "mwis",
        "seed": instance.seed,
        "difficulty": instance.difficulty,
        "generation_seed": instance.generation_seed,
        "requested_n_nodes": instance.requested_n_nodes,
        "n_nodes": instance.n_nodes,
        "vertices": [
            {
                "vertex_id": vertex,
                "weight": instance.weights[vertex],
                "hidden_block": instance.hidden_block_membership[vertex],
            }
            for vertex in instance.vertices
        ],
        "edges": [[left, right] for left, right in instance.edges],
        "baseline_answer": instance.baseline_answer,
        "baseline_objective": instance.baseline_objective,
        "optimal_answer": instance.optimal_answer,
        "optimal_objective": instance.optimal_objective,
        "optimal_proven": instance.optimal_proven,
        "solver_status": instance.solver_status,
        "solver_wall_seconds": instance.solver_wall_seconds,
        "baseline_gap_pct": instance.baseline_gap_pct,
        "problem_statement": instance.problem_statement,
        "bridge_vertices": list(instance.bridge_vertices),
        "bridge_targets": {
            bridge: list(targets)
            for bridge, targets in instance.bridge_targets.items()
        },
        "decoy_vertices": list(instance.decoy_vertices),
        "tuning": asdict(instance.tuning),
        "attempt_index": instance.attempt_index,
    }


def _generation_tuning(size: int, attempt_index: int) -> GenerationTuning:
    intra_values = [0.18, 0.20, 0.22]
    inter_values = [0.006, 0.010, 0.014]
    bridge_target_values = [0.28, 0.34, 0.40]
    bridge_offtarget_values = [0.0, 0.02, 0.04]
    decoy_bonus_values = [10, 14, 18]
    neighbor_bonus_values = [2, 4, 6]
    weight_scales = [5.0, 7.0, 9.0]
    bridge_extra_target_values = [0.25, 0.40, 0.55]
    bridge_count = 6 if size <= 140 else 8
    return GenerationTuning(
        intra_block_p=intra_values[attempt_index % len(intra_values)],
        inter_block_p=inter_values[(attempt_index // 2) % len(inter_values)],
        bridge_target_p=bridge_target_values[(attempt_index // 3) % len(bridge_target_values)],
        bridge_offtarget_p=bridge_offtarget_values[(attempt_index // 5) % len(bridge_offtarget_values)],
        bridge_count=bridge_count,
        bridge_extra_target_prob=bridge_extra_target_values[(attempt_index // 7) % len(bridge_extra_target_values)],
        decoy_bonus=decoy_bonus_values[(attempt_index // 11) % len(decoy_bonus_values)],
        neighbor_bonus=neighbor_bonus_values[(attempt_index // 13) % len(neighbor_bonus_values)],
        weight_scale=weight_scales[(attempt_index // 17) % len(weight_scales)],
    )


def _generate_candidate(
    *,
    generation_seed: int,
    attempt_index: int,
    n_nodes: int,
    tuning: GenerationTuning,
) -> GeneratedCandidate:
    rng = Random(generation_seed)
    vertices = tuple(f"V{index:03d}" for index in range(1, n_nodes + 1))
    shuffled = list(vertices)
    rng.shuffle(shuffled)

    bridge_vertices = tuple(sorted(shuffled[: tuning.bridge_count]))
    core_vertices = shuffled[tuning.bridge_count :]

    block_sizes = [len(core_vertices) // 4] * 4
    for index in range(len(core_vertices) % 4):
        block_sizes[index] += 1

    blocks: dict[str, list[str]] = {}
    hidden_block_membership: dict[str, str] = {vertex: "bridge" for vertex in bridge_vertices}
    cursor = 0
    for block_index, block_size in enumerate(block_sizes, start=1):
        block_name = f"block_{block_index}"
        members = sorted(core_vertices[cursor : cursor + block_size])
        cursor += block_size
        blocks[block_name] = members
        for vertex in members:
            hidden_block_membership[vertex] = block_name

    edges: set[tuple[str, str]] = set()
    for members in blocks.values():
        for index, left in enumerate(members):
            for right in members[index + 1 :]:
                if rng.random() < tuning.intra_block_p:
                    edges.add(_edge(left, right))

    block_names = sorted(blocks)
    for index, left_block in enumerate(block_names):
        for right_block in block_names[index + 1 :]:
            for left in blocks[left_block]:
                for right in blocks[right_block]:
                    if rng.random() < tuning.inter_block_p:
                        edges.add(_edge(left, right))

    bridge_targets: dict[str, tuple[str, ...]] = {}
    for bridge in bridge_vertices:
        target_count = 2 + int(rng.random() < tuning.bridge_extra_target_prob)
        target_blocks = tuple(sorted(rng.sample(block_names, k=min(len(block_names), target_count))))
        bridge_targets[bridge] = target_blocks
        for block_name, members in blocks.items():
            edge_prob = tuning.bridge_target_p if block_name in target_blocks else tuning.bridge_offtarget_p
            for member in members:
                if rng.random() < edge_prob:
                    edges.add(_edge(bridge, member))

    for index, left in enumerate(bridge_vertices):
        for right in bridge_vertices[index + 1 :]:
            if rng.random() < 0.20:
                edges.add(_edge(left, right))

    adjacency = _adjacency(vertices, tuple(sorted(edges)))
    if not _is_connected(vertices, adjacency):
        edges = _connect_components(vertices, edges, rng)
        adjacency = _adjacency(vertices, tuple(sorted(edges)))

    densest_block = max(block_names, key=lambda block_name: _edge_density(blocks[block_name], edges))
    block_degrees = {
        vertex: len(adjacency[vertex])
        for vertex in blocks[densest_block]
    }
    decoy_vertices = tuple(
        sorted(
            sorted(
                blocks[densest_block],
                key=lambda vertex: (-block_degrees[vertex], vertex),
            )[: min(8, len(blocks[densest_block]))]
        )
    )

    weights: dict[str, int] = {}
    for vertex in vertices:
        sampled = int(round(rng.expovariate(1.0 / tuning.weight_scale)))
        weights[vertex] = max(1, 3 + sampled)

    for offset, vertex in enumerate(decoy_vertices):
        weights[vertex] += tuning.decoy_bonus + (offset % 3)

    neighbor_bonus_targets: set[str] = set()
    for vertex in decoy_vertices:
        same_block_neighbors = [
            neighbor
            for neighbor in adjacency[vertex]
            if hidden_block_membership.get(neighbor) == densest_block
        ]
        rng.shuffle(same_block_neighbors)
        neighbor_bonus_targets.update(same_block_neighbors[:2])
    for vertex in neighbor_bonus_targets:
        weights[vertex] += tuning.neighbor_bonus

    upper_quartile_index = max(0, int(0.75 * (len(vertices) - 1)))
    sorted_weights = sorted(weights.values())
    upper_quartile_floor = sorted_weights[upper_quartile_index]
    for offset, vertex in enumerate(decoy_vertices):
        weights[vertex] = max(weights[vertex], upper_quartile_floor + 2 + (offset % 4))

    return GeneratedCandidate(
        generation_seed=generation_seed,
        attempt_index=attempt_index,
        n_nodes=n_nodes,
        vertices=vertices,
        weights=weights,
        edges=tuple(sorted(edges)),
        adjacency=_adjacency(vertices, tuple(sorted(edges))),
        hidden_block_membership=hidden_block_membership,
        bridge_vertices=bridge_vertices,
        bridge_targets=bridge_targets,
        decoy_vertices=decoy_vertices,
        tuning=tuning,
    )


def _connect_components(
    vertices: tuple[str, ...],
    edges: set[tuple[str, str]],
    rng: Random,
) -> set[tuple[str, str]]:
    adjacency = _adjacency(vertices, tuple(sorted(edges)))
    components = _connected_components(vertices, adjacency, excluded=set())
    if len(components) <= 1:
        return edges
    reps = [sorted(component)[0] for component in components]
    rng.shuffle(reps)
    for index in range(len(reps) - 1):
        edges.add(_edge(reps[index], reps[index + 1]))
    return edges


def _separator_stats(
    *,
    vertices: tuple[str, ...],
    adjacency: dict[str, tuple[str, ...]],
    cut_vertices: set[str],
) -> dict[str, Any]:
    remaining_vertices = tuple(vertex for vertex in vertices if vertex not in cut_vertices)
    if len(remaining_vertices) < 2:
        return {
            "did_separate": False,
            "component_count": 0 if not remaining_vertices else 1,
            "component_sizes": (len(remaining_vertices),) if remaining_vertices else (),
        }
    components = _connected_components(remaining_vertices, adjacency, excluded=cut_vertices)
    component_sizes = tuple(sorted((len(component) for component in components), reverse=True))
    return {
        "did_separate": len(components) > 1,
        "component_count": len(components),
        "component_sizes": component_sizes,
    }


def _connected_components(
    vertices: tuple[str, ...],
    adjacency: dict[str, tuple[str, ...]],
    excluded: set[str],
) -> list[tuple[str, ...]]:
    remaining = [vertex for vertex in vertices if vertex not in excluded]
    unseen = set(remaining)
    components: list[tuple[str, ...]] = []
    while unseen:
        start = unseen.pop()
        queue: deque[str] = deque([start])
        component = [start]
        while queue:
            vertex = queue.popleft()
            for neighbor in adjacency[vertex]:
                if neighbor in excluded or neighbor not in unseen:
                    continue
                unseen.remove(neighbor)
                component.append(neighbor)
                queue.append(neighbor)
        components.append(tuple(sorted(component)))
    return components


def _is_connected(vertices: tuple[str, ...], adjacency: dict[str, tuple[str, ...]]) -> bool:
    return len(_connected_components(vertices, adjacency, excluded=set())) == 1


def _edge_density(vertices: list[str], edges: set[tuple[str, str]]) -> float:
    if len(vertices) < 2:
        return 0.0
    possible_edges = len(vertices) * (len(vertices) - 1) / 2
    actual_edges = 0
    for index, left in enumerate(vertices):
        for right in vertices[index + 1 :]:
            if _edge(left, right) in edges:
                actual_edges += 1
    return actual_edges / possible_edges


def _adjacency(
    vertices: tuple[str, ...],
    edges: tuple[tuple[str, str], ...],
) -> dict[str, tuple[str, ...]]:
    neighbors: dict[str, set[str]] = {vertex: set() for vertex in vertices}
    for left, right in edges:
        neighbors[left].add(right)
        neighbors[right].add(left)
    return {vertex: tuple(sorted(adjacent)) for vertex, adjacent in neighbors.items()}


def _edge(left: str, right: str) -> tuple[str, str]:
    return (left, right) if left < right else (right, left)


def _format_entries(entries: list[str], per_line: int) -> str:
    if not entries:
        return "(none)"
    lines: list[str] = []
    for index in range(0, len(entries), per_line):
        lines.append(", ".join(entries[index : index + per_line]))
    return "\n".join(lines)
