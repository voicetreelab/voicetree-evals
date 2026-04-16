from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any

try:
    from ortools.sat.python import cp_model
except ImportError:  # pragma: no cover - exercised in dependency-blocked environments
    cp_model = None


DIFFICULTY_TO_MIN_BASELINE_GAP_PCT = {
    "medium": 200.0,
    "hard": 300.0,
}


def _require_ortools() -> Any:
    if cp_model is None:
        raise RuntimeError(
            "ortools is not installed. Install kaggle_submission dependencies before building graph-coloring instances."
        )
    return cp_model


@dataclass(frozen=True)
class VerificationResult:
    feasible: bool
    computed_cost: int | None
    conflict_count: int | None
    failure_reason: str | None
    normalized_answer: dict[str, Any] | None


@dataclass(frozen=True)
class GraphColoringInstance:
    seed: int
    difficulty: str
    n_nodes: int
    num_colors: int
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    baseline_answer: dict[str, Any]
    baseline_conflicts: int
    optimal_answer: dict[str, Any]
    optimal_conflicts: int
    problem_statement: str


def generate(seed: int, difficulty: str) -> dict[str, Any]:
    difficulty_key = difficulty.lower()
    if difficulty_key not in DIFFICULTY_TO_MIN_BASELINE_GAP_PCT:
        allowed = ", ".join(sorted(DIFFICULTY_TO_MIN_BASELINE_GAP_PCT))
        raise ValueError(f"unsupported graphcol difficulty {difficulty!r}; expected one of: {allowed}")

    instance = _build_instance(
        seed=seed,
        difficulty=difficulty_key,
        n_nodes=30,
        num_colors=4,
        min_baseline_gap_pct=DIFFICULTY_TO_MIN_BASELINE_GAP_PCT[difficulty_key],
    )
    return _serialize_instance(instance)


def _build_instance(
    *,
    seed: int,
    difficulty: str,
    n_nodes: int,
    num_colors: int,
    min_baseline_gap_pct: float | None,
    max_generation_attempts: int = 80,
) -> GraphColoringInstance:
    last_gap_pct: float | None = None
    for attempt in range(max_generation_attempts):
        attempt_seed = seed if attempt == 0 else seed * 10_000 + attempt
        nodes, planted_assignment, edges = _generate_candidate(
            seed=attempt_seed,
            n_nodes=n_nodes,
            num_colors=num_colors,
        )

        baseline_answer = _build_baseline_answer(nodes, edges, num_colors)
        stub = GraphColoringInstance(
            seed=seed,
            difficulty=difficulty,
            n_nodes=n_nodes,
            num_colors=num_colors,
            nodes=nodes,
            edges=edges,
            baseline_answer={},
            baseline_conflicts=0,
            optimal_answer={},
            optimal_conflicts=0,
            problem_statement="",
        )
        baseline_check = _verify_answer(stub, baseline_answer)
        if (
            not baseline_check.feasible
            or baseline_check.conflict_count is None
            or baseline_check.normalized_answer is None
        ):
            raise RuntimeError(f"internal error: baseline coloring is infeasible: {baseline_check.failure_reason}")

        baseline_instance = GraphColoringInstance(
            seed=seed,
            difficulty=difficulty,
            n_nodes=n_nodes,
            num_colors=num_colors,
            nodes=nodes,
            edges=edges,
            baseline_answer=baseline_check.normalized_answer,
            baseline_conflicts=baseline_check.conflict_count,
            optimal_answer={},
            optimal_conflicts=0,
            problem_statement="",
        )
        optimal_answer, optimal_conflicts = _solve_exact_coloring(baseline_instance)
        optimal_check = _verify_answer(
            GraphColoringInstance(
                seed=seed,
                difficulty=difficulty,
                n_nodes=n_nodes,
                num_colors=num_colors,
                nodes=nodes,
                edges=edges,
                baseline_answer=baseline_check.normalized_answer,
                baseline_conflicts=baseline_check.conflict_count,
                optimal_answer=optimal_answer,
                optimal_conflicts=optimal_conflicts,
                problem_statement="",
            ),
            optimal_answer,
        )
        if not optimal_check.feasible or optimal_check.conflict_count != optimal_conflicts:
            raise RuntimeError(f"internal error: optimal coloring failed verification: {optimal_check.failure_reason}")

        baseline_cost = num_colors + baseline_check.conflict_count
        optimal_cost = num_colors + optimal_conflicts
        last_gap_pct = 100.0 * (baseline_cost - optimal_cost) / optimal_cost
        if min_baseline_gap_pct is not None and last_gap_pct < min_baseline_gap_pct:
            continue

        instance = GraphColoringInstance(
            seed=seed,
            difficulty=difficulty,
            n_nodes=n_nodes,
            num_colors=num_colors,
            nodes=nodes,
            edges=edges,
            baseline_answer=baseline_check.normalized_answer,
            baseline_conflicts=baseline_check.conflict_count,
            optimal_answer=optimal_check.normalized_answer or optimal_answer,
            optimal_conflicts=optimal_conflicts,
            problem_statement="",
        )
        return GraphColoringInstance(
            seed=seed,
            difficulty=difficulty,
            n_nodes=n_nodes,
            num_colors=num_colors,
            nodes=nodes,
            edges=edges,
            baseline_answer=baseline_check.normalized_answer,
            baseline_conflicts=baseline_check.conflict_count,
            optimal_answer=optimal_check.normalized_answer or optimal_answer,
            optimal_conflicts=optimal_conflicts,
            problem_statement=_render_problem(instance),
        )

    raise RuntimeError(
        "failed to generate a graph-coloring instance meeting minimum baseline gap "
        f"{min_baseline_gap_pct} after {max_generation_attempts} attempts; last gap was {last_gap_pct}"
    )


def _serialize_instance(instance: GraphColoringInstance) -> dict[str, Any]:
    return {
        "class": "graphcol",
        "seed": instance.seed,
        "difficulty": instance.difficulty,
        "label": f"Slack graph coloring {instance.n_nodes} nodes",
        "metric_name": "scored_cost",
        "n_nodes": instance.n_nodes,
        "num_colors": instance.num_colors,
        "nodes": list(instance.nodes),
        "edges": [[left, right] for left, right in instance.edges],
        "baseline_answer": instance.baseline_answer,
        "baseline_conflicts": instance.baseline_conflicts,
        "baseline_scored_cost": instance.num_colors + instance.baseline_conflicts,
        "gold_answer": instance.optimal_answer,
        "gold_conflicts": instance.optimal_conflicts,
        "gold_scored_cost": instance.num_colors + instance.optimal_conflicts,
        "problem_statement": instance.problem_statement,
        "answer_contract_hint": 'Object with "assignment": {"N01": 1, ..., "N30": 4}.',
    }


def _generate_candidate(
    *,
    seed: int,
    n_nodes: int,
    num_colors: int,
) -> tuple[tuple[str, ...], dict[str, int], tuple[tuple[str, str], ...]]:
    rng = Random(seed)
    nodes = tuple(f"N{index:02d}" for index in range(1, n_nodes + 1))
    shuffled = list(nodes)
    rng.shuffle(shuffled)

    color_buckets: dict[int, list[str]] = {color: [] for color in range(1, num_colors + 1)}
    planted_assignment: dict[str, int] = {}
    for index, node in enumerate(shuffled):
        color = (index % num_colors) + 1
        color_buckets[color].append(node)
        planted_assignment[node] = color

    edges: set[tuple[str, str]] = set()

    # Force chi >= 4 via a planted K4.
    anchors = [color_buckets[color][0] for color in range(1, num_colors + 1)]
    for index, left in enumerate(anchors):
        for right in anchors[index + 1 :]:
            edges.add(_edge(left, right))

    # Preserve the planted coloring while giving each node multiple cross-color constraints.
    for node in nodes:
        own_color = planted_assignment[node]
        for other_color in range(1, num_colors + 1):
            if other_color == own_color:
                continue
            target = rng.choice(color_buckets[other_color])
            edges.add(_edge(node, target))

    for index, left in enumerate(nodes):
        for right in nodes[index + 1 :]:
            if planted_assignment[left] == planted_assignment[right]:
                continue
            if rng.random() < 0.23:
                edges.add(_edge(left, right))

    return nodes, planted_assignment, tuple(sorted(edges))


def _build_baseline_answer(
    nodes: tuple[str, ...],
    edges: tuple[tuple[str, str], ...],
    num_colors: int,
) -> dict[str, Any]:
    adjacency = _adjacency(nodes, edges)
    assignment: dict[str, int] = {}
    for index, node in enumerate(nodes):
        preferred = (index % num_colors) + 1
        best_color = preferred
        best_key = None
        for color in range(1, num_colors + 1):
            conflicts = sum(1 for neighbor in adjacency[node] if assignment.get(neighbor) == color)
            key = (conflicts, abs(color - preferred), color)
            if best_key is None or key < best_key:
                best_key = key
                best_color = color
        assignment[node] = best_color
    return {"assignment": {node: assignment[node] for node in nodes}}


def _solve_exact_coloring(instance: GraphColoringInstance) -> tuple[dict[str, Any], int]:
    cp = _require_ortools()
    model = cp.CpModel()
    node_vars = {
        node: model.NewIntVar(1, instance.num_colors, f"color_{node}")
        for node in instance.nodes
    }
    conflict_vars = []
    for index, (left, right) in enumerate(instance.edges):
        same = model.NewBoolVar(f"same_{index}")
        model.Add(node_vars[left] == node_vars[right]).OnlyEnforceIf(same)
        model.Add(node_vars[left] != node_vars[right]).OnlyEnforceIf(same.Not())
        conflict_vars.append(same)

    model.Minimize(sum(conflict_vars))
    solver = cp.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    if status != cp.OPTIMAL:
        raise RuntimeError(
            "failed to obtain exact optimum for graph-coloring instance: "
            f"{solver.StatusName(status)}"
        )

    assignment = {node: solver.Value(node_vars[node]) for node in instance.nodes}
    return {"assignment": assignment}, int(solver.ObjectiveValue())


def _verify_answer(instance: GraphColoringInstance, answer: dict[str, Any] | None) -> VerificationResult:
    if not isinstance(answer, dict):
        return VerificationResult(False, None, None, "answer must be an object", None)
    raw_assignment = answer.get("assignment", answer)
    if not isinstance(raw_assignment, dict):
        return VerificationResult(False, None, None, "assignment must be an object", None)

    normalized: dict[str, int] = {}
    for node in instance.nodes:
        if node not in raw_assignment:
            return VerificationResult(False, None, None, f"missing color for {node}", None)
        try:
            color = int(raw_assignment[node])
        except Exception:
            return VerificationResult(False, None, None, f"color for {node} is not an integer", None)
        if not 1 <= color <= instance.num_colors:
            return VerificationResult(
                False,
                None,
                None,
                f"color for {node} must be between 1 and {instance.num_colors}",
                None,
            )
        normalized[node] = color

    conflict_count = sum(1 for left, right in instance.edges if normalized[left] == normalized[right])
    return VerificationResult(
        True,
        instance.num_colors + conflict_count,
        conflict_count,
        None,
        {"assignment": {node: normalized[node] for node in instance.nodes}},
    )


def _render_problem(instance: GraphColoringInstance) -> str:
    edge_lines = "\n".join(f"- {left}-{right}" for left, right in instance.edges)
    baseline_summary = _solution_summary(instance, instance.baseline_answer, instance.baseline_conflicts)
    return f"""Slack graph coloring:
Assign each node a color in {{1, 2, 3, 4}}.

Objective:
scored_cost = 4 + number_of_conflicting_edges
where a conflicting edge has the same color on both endpoints.

Nodes:
- {", ".join(instance.nodes)}

Edges:
{edge_lines}

Rules:
- Every node must receive one integer color in {{1, 2, 3, 4}}.
- Lower scored_cost is better.
- This graph is 4-colorable, but there are multiple valid 4-colorings.
- If you stop immediately or fail to produce a valid answer, the baseline below is what gets scored.

Baseline summary:
{baseline_summary}
"""


def _solution_summary(
    instance: GraphColoringInstance,
    answer: dict[str, Any],
    conflict_count: int | None = None,
) -> str:
    raw_assignment = answer.get("assignment", {})
    assignment = {
        node: int(raw_assignment[node])
        for node in instance.nodes
        if node in raw_assignment
    }
    conflicts = (
        conflict_count
        if conflict_count is not None
        else sum(1 for left, right in instance.edges if assignment.get(left) == assignment.get(right))
    )
    assignment_bits = ", ".join(f"{node}={assignment.get(node, '?')}" for node in instance.nodes)
    conflict_edges = [f"{left}-{right}" for left, right in instance.edges if assignment.get(left) == assignment.get(right)]
    preview = ", ".join(conflict_edges[:12]) if conflict_edges else "none"
    if len(conflict_edges) > 12:
        preview += ", ..."
    return (
        f"Conflicts: {conflicts}\n"
        f"Scored cost: {instance.num_colors + conflicts}\n"
        f"Conflicting edges: {preview}\n"
        f"Assignment: {assignment_bits}"
    )


def _adjacency(
    nodes: tuple[str, ...],
    edges: tuple[tuple[str, str], ...],
) -> dict[str, set[str]]:
    adjacency = {node: set() for node in nodes}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    return adjacency


def _edge(left: str, right: str) -> tuple[str, str]:
    return (left, right) if left < right else (right, left)
