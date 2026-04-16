#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from generators import cjs, graphcol, mwis, steiner, tsp, ve
from generators import CLASS_TO_GENERATOR
from verifiers import CLASS_TO_VERIFIER
from verifiers.ve import _instance_from_payload, evaluate_exact_probability

WALL_BUDGET_S = 1800
SOLO_VALUE_CAP = 100.0
PORTFOLIO_COMPONENT_CAPS = (33.0, 33.0, 34.0)
PORTFOLIO_COMPONENT_IDS = (
    "cjs_medium_seed1",
    "steiner_medium_seed1",
    "tsp_medium_seed1",
)
SOLO_SPECS = (
    ("cjs", "medium", 1),
    ("steiner", "medium", 1),
    ("graphcol", "medium", 1),
    ("tsp", "medium", 1),
    ("mwis", "medium", 1),
    ("ve", "medium", 1),
)


@dataclass(frozen=True)
class SmokeRow:
    row: dict[str, Any]
    notes: str | None = None


def _build_cjs_row(seed: int, difficulty: str) -> SmokeRow:
    instance = cjs.generate(seed=seed, difficulty=difficulty)
    jobs = tuple(
        cjs.JobSpec(
            job_id=int(raw_job["job_id"]),
            factory_a=tuple(
                cjs.OperationSpec(
                    machine_name=str(raw_op["machine_name"]),
                    duration=int(raw_op["duration"]),
                )
                for raw_op in raw_job["factory_a"]
            ),
            factory_b=tuple(
                cjs.OperationSpec(
                    machine_name=str(raw_op["machine_name"]),
                    duration=int(raw_op["duration"]),
                )
                for raw_op in raw_job["factory_b"]
            ),
            )
        for raw_job in instance["jobs"]
    )
    _, gold_objective = cjs.solve_exact_schedule(jobs=jobs, n_machines=int(instance["n_machines"]))
    baseline_objective = float(instance["baseline_objective"])
    _assert_close("cjs gold_objective", gold_objective, instance["gold_objective"])
    row = _solo_row(
        cls="cjs",
        difficulty=difficulty,
        seed=seed,
        instance=instance,
        gold_objective=float(gold_objective),
        baseline_objective=baseline_objective,
    )
    return SmokeRow(row=row)


def _build_steiner_row(seed: int, difficulty: str) -> SmokeRow:
    instance = steiner.generate(seed=seed, difficulty=difficulty)
    _, gold_cost = steiner._solve_joint_optimum(instance, seed=seed)
    _assert_close("steiner gold_cost", gold_cost, instance["gold_cost"])
    row = _solo_row(
        cls="steiner",
        difficulty=difficulty,
        seed=seed,
        instance=instance,
        gold_objective=float(gold_cost),
        baseline_objective=float(instance["baseline_cost"]),
    )
    return SmokeRow(row=row)


def _build_graphcol_row(seed: int, difficulty: str) -> SmokeRow:
    instance = graphcol.generate(seed=seed, difficulty=difficulty)
    graph_instance = graphcol.GraphColoringInstance(
        seed=int(instance["seed"]),
        difficulty=str(instance["difficulty"]),
        n_nodes=int(instance["n_nodes"]),
        num_colors=int(instance["num_colors"]),
        nodes=tuple(str(node) for node in instance["nodes"]),
        edges=tuple((str(left), str(right)) for left, right in instance["edges"]),
        baseline_answer=dict(instance["baseline_answer"]),
        baseline_conflicts=int(instance["baseline_conflicts"]),
        optimal_answer=dict(instance["gold_answer"]),
        optimal_conflicts=int(instance["gold_conflicts"]),
        problem_statement=str(instance["problem_statement"]),
    )
    _, optimal_conflicts = graphcol._solve_exact_coloring(graph_instance)
    gold_scored_cost = int(instance["num_colors"]) + optimal_conflicts
    _assert_close("graphcol gold_scored_cost", gold_scored_cost, instance["gold_scored_cost"])
    row = _solo_row(
        cls="graphcol",
        difficulty=difficulty,
        seed=seed,
        instance=instance,
        gold_objective=float(gold_scored_cost),
        baseline_objective=float(instance["baseline_scored_cost"]),
    )
    return SmokeRow(row=row)


def _build_tsp_row(seed: int, difficulty: str) -> SmokeRow:
    instance = tsp.generate(seed=seed, difficulty=difficulty)
    coords = tuple((int(x), int(y)) for x, y in instance["coords"])
    _, optimal_length = tsp.solve_exact_tour(coords)
    _assert_close("tsp optimal_length", optimal_length, instance["optimal_length"], tol=1e-6)
    row = _solo_row(
        cls="tsp",
        difficulty=difficulty,
        seed=seed,
        instance=instance,
        gold_objective=float(optimal_length),
        baseline_objective=float(instance["baseline_length"]),
    )
    return SmokeRow(row=row)


def _build_mwis_row(seed: int, difficulty: str) -> SmokeRow:
    instance = mwis.generate(seed=seed, difficulty=difficulty)
    vertices = tuple(str(item["vertex_id"]) for item in instance["vertices"])
    weights = {str(item["vertex_id"]): int(item["weight"]) for item in instance["vertices"]}
    edges = tuple((str(left), str(right)) for left, right in instance["edges"])
    solve_result = mwis.solve_exact_mwis(vertices=vertices, weights=weights, edges=edges)
    if not solve_result.is_optimal:
        raise RuntimeError(f"mwis exact solve was not optimal: {solve_result.status_name}")
    _assert_close("mwis optimal_objective", solve_result.total_weight, instance["optimal_objective"])
    row = _solo_row(
        cls="mwis",
        difficulty=difficulty,
        seed=seed,
        instance=instance,
        gold_objective=float(solve_result.total_weight),
        baseline_objective=float(instance["baseline_objective"]),
    )
    return SmokeRow(row=row)


def _build_ve_row(seed: int, difficulty: str) -> SmokeRow:
    instance = ve.generate(seed=seed, difficulty=difficulty)
    parsed = _instance_from_payload(instance)
    exact_posterior, peak_size = evaluate_exact_probability(parsed, parsed.gold_ordering)
    _assert_close("ve exact_posterior", exact_posterior, instance["exact_posterior"], tol=1e-12)
    _assert_close("ve gold_peak_factor_size", peak_size, instance["gold_peak_factor_size"])
    row = _solo_row(
        cls="ve",
        difficulty=difficulty,
        seed=seed,
        instance=instance,
        gold_objective=float(exact_posterior),
        baseline_objective=0.5,
    )
    return SmokeRow(
        row=row,
        notes=(
            "Used exact posterior as gold_objective. "
            "Set baseline_objective=0.5 as a trivial uninformed binary-probability baseline; "
            "ordering difficulty metadata remains inside instance."
        ),
    )


def _solo_row(
    *,
    cls: str,
    difficulty: str,
    seed: int,
    instance: dict[str, Any],
    gold_objective: float,
    baseline_objective: float,
) -> dict[str, Any]:
    return {
        "id": f"{cls}_{difficulty}_seed{seed}",
        "class": cls,
        "difficulty": difficulty,
        "seed": seed,
        "instance": instance,
        "gold_objective": float(gold_objective),
        "baseline_objective": float(baseline_objective),
        "value_cap": SOLO_VALUE_CAP,
        "wall_budget_s": WALL_BUDGET_S,
        "components": None,
    }


def _portfolio_problem_statement(components: list[dict[str, Any]]) -> str:
    summary_lines = [
        "You are allocating effort across a three-problem optimization portfolio.",
        "Objective: maximize total captured headroom across the listed components.",
        "Each component contributes at most its value_cap when solved to its gold level.",
        "If you fail to improve a component, it stays at its baseline contribution.",
        "",
        "Portfolio components:",
    ]
    for component in components:
        summary_lines.append(
            f"- {component['problem_id']} | class={component['class']} | value_cap={component['value_cap']}"
        )
    summary_lines.extend(
        [
            "",
            "Return answers for the listed sub-problems using the component-specific answer contracts.",
        ]
    )
    return "\n".join(summary_lines)


def _build_portfolio_row(solo_rows: list[SmokeRow]) -> SmokeRow:
    solo_by_id = {entry.row["id"]: entry.row for entry in solo_rows}
    components: list[dict[str, Any]] = []
    for problem_id, value_cap in zip(PORTFOLIO_COMPONENT_IDS, PORTFOLIO_COMPONENT_CAPS, strict=True):
        source = solo_by_id[problem_id]
        components.append(
            {
                "problem_id": problem_id,
                "class": source["class"],
                "value_cap": float(value_cap),
                "sub_instance": source["instance"],
            }
        )

    portfolio_instance = {
        "class": "portfolio",
        "seed": 1,
        "difficulty": "medium",
        "n_components": len(components),
        "problem_statement": _portfolio_problem_statement(components),
    }
    row = {
        "id": "portfolio_medium_seed1",
        "class": "portfolio",
        "difficulty": "medium",
        "seed": 1,
        "instance": portfolio_instance,
        "gold_objective": 100.0,
        "baseline_objective": 0.0,
        "value_cap": 100.0,
        "wall_budget_s": WALL_BUDGET_S,
        "components": components,
    }
    return SmokeRow(
        row=row,
        notes=(
            "Portfolio gold_objective=100 and baseline_objective=0 encode the economic ceiling/floor "
            "for value-capture scoring. No portfolio verifier exists in the checkout yet, so the row "
            "preserves prompt-ready metadata and full component sub_instances for later integration."
        ),
    )


def _build_rows() -> list[SmokeRow]:
    builders = {
        "cjs": _build_cjs_row,
        "steiner": _build_steiner_row,
        "graphcol": _build_graphcol_row,
        "tsp": _build_tsp_row,
        "mwis": _build_mwis_row,
        "ve": _build_ve_row,
    }
    rows = [builders[cls](seed, difficulty) for cls, difficulty, seed in SOLO_SPECS]
    rows.append(_build_portfolio_row(rows))
    return rows


def _assert_close(label: str, actual: float, expected: Any, tol: float = 1e-9) -> None:
    actual_f = float(actual)
    expected_f = float(expected)
    if abs(actual_f - expected_f) > tol:
        raise RuntimeError(f"{label} mismatch: recomputed {actual_f} != stored {expected_f}")


def _sanity_check_round_trip(rows: list[SmokeRow]) -> None:
    for smoke_row in rows:
        encoded = json.dumps(smoke_row.row, sort_keys=True)
        decoded = json.loads(encoded)
        if decoded["class"] == "portfolio":
            components = decoded.get("components")
            if not isinstance(components, list) or len(components) != 3:
                raise RuntimeError("portfolio row components failed round-trip validation")
            total_cap = sum(float(component["value_cap"]) for component in components)
            _assert_close("portfolio component caps", total_cap, 100.0)
            continue

        cls = decoded["class"]
        verifier = CLASS_TO_VERIFIER[cls]
        wrong_submission: Any = [] if cls == "tsp" else {}
        _, feasible, _ = verifier(decoded["instance"], wrong_submission)
        if feasible:
            raise RuntimeError(f"expected infeasible path for {decoded['id']}, but verifier returned feasible")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def main() -> int:
    rows = _build_rows()
    _sanity_check_round_trip(rows)

    questions = [entry.row for entry in rows]
    gold_rows = [
        {
            "id": entry.row["id"],
            "gold_objective": entry.row["gold_objective"],
            "baseline_objective": entry.row["baseline_objective"],
            "value_cap": entry.row["value_cap"],
        }
        for entry in rows
    ]

    _write_jsonl(ROOT / "questions.jsonl", questions)
    _write_jsonl(ROOT / "gold" / "gold.jsonl", gold_rows)
    print("Wrote 7 rows to questions.jsonl; 7 rows to gold/gold.jsonl. Verified schema round-trip.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
