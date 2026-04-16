from __future__ import annotations

import json
from typing import Any


def render_nl(instance: dict[str, Any], cls: str) -> str:
    if not isinstance(instance, dict):
        raise TypeError("instance must be a dict")

    problem_statement = instance.get("problem_statement")
    if isinstance(problem_statement, str) and problem_statement.strip():
        return problem_statement

    renderer = _FALLBACK_RENDERERS.get(cls, _render_generic)
    return renderer(instance)


def _render_generic(instance: dict[str, Any]) -> str:
    return json.dumps(instance, indent=2, sort_keys=True)


def _render_tsp(instance: dict[str, Any]) -> str:
    coords = instance.get("coords", [])
    coord_lines = []
    for index, coord in enumerate(coords):
        if isinstance(coord, (list, tuple)) and len(coord) == 2:
            coord_lines.append(f"- {index}: ({coord[0]}, {coord[1]})")
    baseline = instance.get("baseline_tour")
    baseline_line = f"Baseline tour: {baseline}" if isinstance(baseline, list) else ""
    return (
        "Euclidean TSP instance.\n"
        + ("\n".join(coord_lines) + "\n" if coord_lines else "")
        + baseline_line
    ).strip()


def _render_graphcol(instance: dict[str, Any]) -> str:
    n_nodes = instance.get("n_nodes", "?")
    num_colors = instance.get("num_colors", "?")
    edges = instance.get("edges", [])
    return (
        f"Graph coloring instance with {n_nodes} nodes, {len(edges)} edges, "
        f"and {num_colors} available colors."
    )


def _render_cjs(instance: dict[str, Any]) -> str:
    jobs = instance.get("jobs")
    machines = instance.get("machines")
    return f"Coupled job-shop instance with {len(jobs) if isinstance(jobs, list) else '?'} jobs and {len(machines) if isinstance(machines, list) else '?'} machines."


def _render_steiner(instance: dict[str, Any]) -> str:
    nodes = instance.get("nodes", [])
    terminals = instance.get("terminals", [])
    return (
        f"Steiner x coloring instance with {len(nodes)} nodes and {len(terminals)} terminals."
    )


def _render_mwis(instance: dict[str, Any]) -> str:
    nodes = instance.get("nodes", [])
    edges = instance.get("edges", [])
    return f"MWIS instance with {len(nodes)} nodes and {len(edges)} edges."


def _render_ve(instance: dict[str, Any]) -> str:
    variables = instance.get("variables", [])
    query = instance.get("query")
    evidence = instance.get("evidence", {})
    return (
        f"Bayesian VE instance with {len(variables)} variables, query={query}, "
        f"and {len(evidence) if isinstance(evidence, dict) else '?'} evidence assignments."
    )


_FALLBACK_RENDERERS = {
    "cjs": _render_cjs,
    "graphcol": _render_graphcol,
    "mwis": _render_mwis,
    "steiner": _render_steiner,
    "tsp": _render_tsp,
    "ve": _render_ve,
}
