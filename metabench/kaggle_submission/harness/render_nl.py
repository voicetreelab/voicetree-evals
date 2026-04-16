from __future__ import annotations

import json
from typing import Any


def render_nl(
    instance: dict[str, Any],
    cls: str,
    components: list[Any] | None = None,
) -> str:
    if not isinstance(instance, dict):
        raise TypeError("instance must be a dict")

    problem_statement = instance.get("problem_statement")
    base_nl: str
    if isinstance(problem_statement, str) and problem_statement.strip():
        base_nl = problem_statement
    else:
        renderer = _FALLBACK_RENDERERS.get(cls, _render_generic)
        base_nl = renderer(instance)

    if cls == "portfolio" and components:
        return _render_portfolio(base_nl, components)
    return base_nl


def _render_portfolio(base_nl: str, components: list[Any]) -> str:
    try:
        from verifiers import CLASS_TO_BEST_GUESS_SCHEMA
    except Exception:
        CLASS_TO_BEST_GUESS_SCHEMA = {}

    parts: list[str] = [base_nl.rstrip(), ""]
    for comp in components:
        if not isinstance(comp, dict):
            continue
        sub_cls = comp.get("class")
        sub_inst = comp.get("sub_instance", {}) or {}
        pid = comp.get("problem_id")
        value_cap = comp.get("value_cap")
        parts.append(f"=== {pid} (class={sub_cls}, value_cap={value_cap}) ===")

        sub_ps = sub_inst.get("problem_statement")
        if isinstance(sub_ps, str) and sub_ps.strip():
            parts.append(sub_ps.rstrip())
        else:
            renderer = _FALLBACK_RENDERERS.get(sub_cls, _render_generic)
            parts.append(renderer(sub_inst))

        contract = sub_inst.get("answer_contract")
        if isinstance(contract, str) and contract.strip():
            parts.append(f"Answer contract for {pid}: {contract}")

        schema = CLASS_TO_BEST_GUESS_SCHEMA.get(sub_cls) if isinstance(sub_cls, str) else None
        if schema:
            parts.append(f"ANSWER SCHEMA for {pid} (class={sub_cls}):\n{schema}")
        parts.append("")

    parts.append(
        "Return a single BEST_GUESS JSON object whose top-level keys are the component "
        "problem_ids above, each mapped to an object obeying that component's ANSWER SCHEMA. "
        "Do not wrap the answers under an `answers` key."
    )
    return "\n".join(parts)


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


def _render_mbj(instance: dict[str, Any]) -> str:
    jobs = instance.get("jobs")
    n_machines = instance.get("n_machines", "?")
    return (
        f"Masked block job-shop instance with "
        f"{len(jobs) if isinstance(jobs, list) else '?'} jobs and {n_machines} machines."
    )


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
    "mbj": _render_mbj,
    "mwis": _render_mwis,
    "steiner": _render_steiner,
    "tsp": _render_tsp,
    "ve": _render_ve,
}
