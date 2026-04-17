#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, replace
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from generators import cjs, graphcol, mbj, mwis, steiner, tsp, ve
from verifiers import CLASS_TO_VERIFIER
from verifiers import ve as ve_verifier
from verifiers.ve import _instance_from_payload, evaluate_exact_probability

WALL_BUDGET_S = 1800
SOLO_VALUE_CAP = 100.0
SOLO_CLASSES = ("cjs", "steiner", "graphcol", "tsp", "mwis", "ve", "mbj")
PORTFOLIO_COMPONENT_CAPS = (33.0, 33.0, 34.0)
MEDIUM_PORTFOLIO_COMPONENT_IDS = (
    "cjs_medium_seed1",
    "steiner_medium_seed1",
    "tsp_medium_seed1",
)
HARD_PORTFOLIO_COMPONENT_CLASSES = ("cjs", "steiner", "tsp")
# Classes unsafe for inclusion in portfolio-hard class pools. mwis-hard's
# bridge-separator pre-flight is probabilistic and fails deterministically at
# many seed positions, blocking ~67% of requested portfolio-hard rows when
# sampled (R2 W6). See voicetree-16-4/discussion-of-results.md Finding 7 +
# Bug 3. Workers doing random class sampling for portfolio-hard must subtract
# this set from SOLO_CLASSES before sampling.
PORTFOLIO_HARD_EXCLUDE_CLASSES = frozenset({"mwis"})
PORTFOLIO_HARD_SAFE_SOLO_CLASSES = tuple(
    cls for cls in SOLO_CLASSES if cls not in PORTFOLIO_HARD_EXCLUDE_CLASSES
)
MAX_HARD_SEED_OFFSET = 4
MAX_GENERATED_SEED = 7
MEDIUM_SOLO_SPECS = tuple((cls, "medium", 1) for cls in SOLO_CLASSES)
HARD_SOLO_SPECS = tuple(
    (cls, "hard", seed)
    for cls in SOLO_CLASSES
    for seed in (1, 2, 3)
)
HARD_SIZE_FALLBACKS: dict[str, tuple[tuple[str, int], ...]] = {
    "mwis": (("n_nodes", mwis.DIFFICULTY_CONFIG["medium"]["n_nodes"]),),
    "steiner": (("n", steiner.DIFFICULTY_CONFIGS["medium"]["n"]),),
    "ve": (("requested_total_variables", ve_verifier.DIFFICULTY_TO_VARIABLES["medium"]),),
    "mbj": (
        ("n_jobs", mbj.DIFFICULTY_CONFIGS["medium"]["n_jobs"]),
        ("n_machines", mbj.DIFFICULTY_CONFIGS["medium"]["n_machines"]),
    ),
}


@dataclass(frozen=True)
class SmokeRow:
    row: dict[str, Any]
    notes: str | None = None
    wall_s_to_compute_gold: float | None = None
    requested_seed: int | None = None


def _generate_cjs_instance(seed: int, difficulty: str, config_override: dict[str, Any] | None = None) -> dict[str, Any]:
    if config_override is None:
        return cjs.generate(seed=seed, difficulty=difficulty)

    config = dict(cjs.DIFFICULTY_CONFIGS[difficulty])
    config.update(config_override)
    instance = cjs.build_instance(
        seed=seed,
        n_jobs=int(config["n_jobs"]),
        n_machines=int(config["n_machines"]),
        min_baseline_gap_pct=float(config["min_baseline_gap_pct"]),
    )
    gold_objective = instance.optimal_makespan
    baseline_objective = instance.baseline_makespan
    baseline_gap_pct = 100.0 * (baseline_objective - gold_objective) / gold_objective
    return {
        "class": "cjs",
        "difficulty": difficulty,
        "seed": seed,
        "n_jobs": instance.n_jobs,
        "n_machines": instance.n_machines,
        "metric_name": "makespan",
        "answer_contract": (
            'Object with "factory_a", "factory_b", and "makespan". '
            'Each factory maps machine names to lists of ["J<id>", start, end] triples.'
        ),
        "jobs": [cjs._job_to_dict(job) for job in instance.jobs],
        "baseline_submission": instance.baseline_schedule,
        "gold_submission": instance.optimal_schedule,
        "baseline_objective": baseline_objective,
        "gold_objective": gold_objective,
        "baseline_gap_pct": baseline_gap_pct,
        "problem_statement": instance.problem_statement,
    }


def _build_cjs_row(seed: int, difficulty: str, *, config_override: dict[str, Any] | None = None) -> SmokeRow:
    instance = _generate_cjs_instance(seed=seed, difficulty=difficulty, config_override=config_override)
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


def _generate_steiner_instance(
    seed: int,
    difficulty: str,
    config_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if config_override is None:
        return steiner.generate(seed=seed, difficulty=difficulty)

    config = dict(steiner.DIFFICULTY_CONFIGS[difficulty])
    config.update(config_override)
    return steiner._build_instance(seed=seed, difficulty=difficulty, **config)


def _build_steiner_row(seed: int, difficulty: str, *, config_override: dict[str, Any] | None = None) -> SmokeRow:
    instance = _generate_steiner_instance(seed=seed, difficulty=difficulty, config_override=config_override)
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


def _generate_graphcol_instance(
    seed: int,
    difficulty: str,
    config_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if config_override is None:
        return graphcol.generate(seed=seed, difficulty=difficulty)

    difficulty_key = difficulty.lower()
    config = {
        "n_nodes": 30,
        "num_colors": 4,
        "min_baseline_gap_pct": graphcol.DIFFICULTY_TO_MIN_BASELINE_GAP_PCT[difficulty_key],
    }
    config.update(config_override)
    instance = graphcol._build_instance(seed=seed, difficulty=difficulty_key, **config)
    return graphcol._serialize_instance(instance)


def _build_graphcol_row(seed: int, difficulty: str, *, config_override: dict[str, Any] | None = None) -> SmokeRow:
    instance = _generate_graphcol_instance(seed=seed, difficulty=difficulty, config_override=config_override)
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


def _build_tsp_row(seed: int, difficulty: str, *, config_override: dict[str, Any] | None = None) -> SmokeRow:
    if config_override is not None:
        raise RuntimeError("tsp does not expose a size override path from build_questions.py")
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


def _generate_mwis_instance(
    seed: int,
    difficulty: str,
    config_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if config_override is None:
        return mwis.generate(seed=seed, difficulty=difficulty)

    config = dict(mwis.DIFFICULTY_CONFIG[difficulty])
    config.update(config_override)
    instance = mwis.build_instance(seed=seed, difficulty=difficulty, **config)
    return mwis._instance_to_json(instance)


def _build_mwis_row(seed: int, difficulty: str, *, config_override: dict[str, Any] | None = None) -> SmokeRow:
    instance = _generate_mwis_instance(seed=seed, difficulty=difficulty, config_override=config_override)
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


def _generate_ve_instance(
    seed: int,
    difficulty: str,
    config_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if config_override is None:
        return ve.generate(seed=seed, difficulty=difficulty)

    requested_total_variables = int(
        config_override.get(
            "requested_total_variables",
            ve_verifier._difficulty_to_requested_total_variables(difficulty),
        )
    )
    instance = ve_verifier.build_instance(
        seed=seed,
        difficulty=difficulty,
        requested_total_variables=requested_total_variables,
    )
    return ve_verifier._instance_to_payload(instance)


def _generate_mbj_instance(
    seed: int,
    difficulty: str,
    config_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if config_override is None:
        return mbj.generate(seed=seed, difficulty=difficulty)

    config = dict(mbj.DIFFICULTY_CONFIGS[difficulty])
    config.update(config_override)
    instance = mbj.build_instance(
        seed=seed,
        n_jobs=int(config["n_jobs"]),
        n_machines=int(config["n_machines"]),
        min_baseline_gap_pct=float(config["min_baseline_gap_pct"]),
        min_heuristic_spread_pct=float(config["min_heuristic_spread_pct"]),
        max_heuristic_spread_pct=float(config["max_heuristic_spread_pct"]),
        max_generation_attempts=int(config["max_generation_attempts"]),
        cp_time_limit_s=float(config["cp_time_limit_s"]),
        require_optimal=bool(config.get("require_optimal", True)),
    )
    gold_objective = instance.optimal_objective
    baseline_objective = instance.baseline_objective
    baseline_gap_pct = 100.0 * (baseline_objective - gold_objective) / max(1, gold_objective)
    return {
        "class": "mbj",
        "difficulty": difficulty,
        "seed": seed,
        "n_jobs": instance.n_jobs,
        "n_machines": instance.n_machines,
        "metric_name": "objective",
        "answer_contract": (
            'Object with "machines", "makespan", "weighted_tardiness", and "objective". '
            '"machines" maps each machine name (M1..Mk) to a list of ["J<id>", start, end] triples.'
        ),
        "jobs": [mbj._job_to_dict(job) for job in instance.jobs],
        "baseline_submission": instance.baseline_schedule,
        "gold_submission": instance.optimal_schedule,
        "baseline_objective": baseline_objective,
        "gold_objective": gold_objective,
        "baseline_gap_pct": baseline_gap_pct,
        "problem_statement": instance.problem_statement,
    }


def _build_mbj_row(seed: int, difficulty: str, *, config_override: dict[str, Any] | None = None) -> SmokeRow:
    instance = _generate_mbj_instance(seed=seed, difficulty=difficulty, config_override=config_override)
    row = _solo_row(
        cls="mbj",
        difficulty=difficulty,
        seed=seed,
        instance=instance,
        gold_objective=float(instance["gold_objective"]),
        baseline_objective=float(instance["baseline_objective"]),
    )
    return SmokeRow(row=row)


def _build_ve_row(seed: int, difficulty: str, *, config_override: dict[str, Any] | None = None) -> SmokeRow:
    instance = _generate_ve_instance(seed=seed, difficulty=difficulty, config_override=config_override)
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


def _merge_notes(*notes: str | None) -> str | None:
    parts = [note.strip() for note in notes if note and note.strip()]
    if not parts:
        return None
    return " ".join(parts)


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


def _build_portfolio_row(
    *,
    solo_rows: list[SmokeRow],
    difficulty: str,
    seed: int,
    component_ids: tuple[str, str, str],
) -> SmokeRow:
    solo_by_id = {entry.row["id"]: entry.row for entry in solo_rows}
    components: list[dict[str, Any]] = []
    for problem_id, value_cap in zip(component_ids, PORTFOLIO_COMPONENT_CAPS, strict=True):
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
        "seed": seed,
        "difficulty": difficulty,
        "n_components": len(components),
        "problem_statement": _portfolio_problem_statement(components),
    }
    row = {
        "id": f"portfolio_{difficulty}_seed{seed}",
        "class": "portfolio",
        "difficulty": difficulty,
        "seed": seed,
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
        wall_s_to_compute_gold=0.0,
        requested_seed=seed,
    )


def _build_timed_row(
    builder: Any,
    seed: int,
    difficulty: str,
    *,
    config_override: dict[str, Any] | None = None,
) -> SmokeRow:
    started_at = perf_counter()
    built = builder(seed, difficulty, config_override=config_override)
    return replace(built, wall_s_to_compute_gold=perf_counter() - started_at)


def _seed_candidates(requested_seed: int) -> range:
    return range(requested_seed, min(requested_seed + MAX_HARD_SEED_OFFSET, MAX_GENERATED_SEED) + 1)


def _error_summary(exc: Exception) -> str:
    message = " ".join(str(exc).split())
    if not message:
        return type(exc).__name__
    return message


def _seed_failure_summary(seed_failures: list[tuple[int, str]]) -> str:
    return "; ".join(f"seed={seed}: {reason}" for seed, reason in seed_failures)


def _build_fallback_note(
    *,
    cls: str,
    difficulty: str,
    requested_seed: int,
    actual_seed: int,
    seed_failures: list[tuple[int, str]],
    size_override: tuple[str, int] | None = None,
) -> str | None:
    if actual_seed == requested_seed and not seed_failures and size_override is None:
        return None

    parts = [f"Requested slot {cls}_{difficulty}_seed{requested_seed} generated as {cls}_{difficulty}_seed{actual_seed}."]
    if size_override is not None:
        key, value = size_override
        parts.append(f"Applied size fallback {key}={value}.")
    if seed_failures:
        parts.append(f"Earlier attempts failed or were skipped: {_seed_failure_summary(seed_failures)}.")
    return " ".join(parts)


def _annotate_row(smoke_row: SmokeRow, *, requested_seed: int, note: str | None = None) -> SmokeRow:
    return replace(
        smoke_row,
        requested_seed=requested_seed,
        notes=_merge_notes(note, smoke_row.notes),
    )


def _build_hard_row_with_fallback(
    *,
    cls: str,
    requested_seed: int,
    builder: Any,
    used_actual_seeds: set[int],
) -> SmokeRow:
    seed_failures: list[tuple[int, str]] = []
    candidate_seeds = list(_seed_candidates(requested_seed))
    for candidate_seed in candidate_seeds:
        if candidate_seed in used_actual_seeds:
            seed_failures.append((candidate_seed, "skipped because that actual seed was already used earlier"))
            continue
        try:
            built = _build_timed_row(builder, candidate_seed, "hard")
        except Exception as exc:
            seed_failures.append((candidate_seed, _error_summary(exc)))
            continue

        used_actual_seeds.add(candidate_seed)
        note = _build_fallback_note(
            cls=cls,
            difficulty="hard",
            requested_seed=requested_seed,
            actual_seed=candidate_seed,
            seed_failures=seed_failures,
        )
        return _annotate_row(built, requested_seed=requested_seed, note=note)

    for size_override in HARD_SIZE_FALLBACKS.get(cls, ()):
        override_dict = {size_override[0]: size_override[1]}
        for candidate_seed in candidate_seeds:
            if candidate_seed in used_actual_seeds:
                continue
            try:
                built = _build_timed_row(
                    builder,
                    candidate_seed,
                    "hard",
                    config_override=override_dict,
                )
            except Exception as exc:
                seed_failures.append((candidate_seed, f"{size_override[0]}={size_override[1]} -> {_error_summary(exc)}"))
                continue

            used_actual_seeds.add(candidate_seed)
            note = _build_fallback_note(
                cls=cls,
                difficulty="hard",
                requested_seed=requested_seed,
                actual_seed=candidate_seed,
                seed_failures=seed_failures,
                size_override=size_override,
            )
            return _annotate_row(built, requested_seed=requested_seed, note=note)

    failure_summary = _seed_failure_summary(seed_failures) or "no attempts recorded"
    raise RuntimeError(
        f"failed to generate {cls}_hard_seed{requested_seed} after seed fallback and size fallback: "
        f"{failure_summary}"
    )


def _build_rows() -> list[SmokeRow]:
    builders = {
        "cjs": _build_cjs_row,
        "steiner": _build_steiner_row,
        "graphcol": _build_graphcol_row,
        "tsp": _build_tsp_row,
        "mwis": _build_mwis_row,
        "ve": _build_ve_row,
        "mbj": _build_mbj_row,
    }
    medium_rows = [
        _annotate_row(_build_timed_row(builders[cls], seed, difficulty), requested_seed=seed)
        for cls, difficulty, seed in MEDIUM_SOLO_SPECS
    ]
    used_hard_actual_seeds = {cls: set() for cls in SOLO_CLASSES}
    hard_rows = [
        _build_hard_row_with_fallback(
            cls=cls,
            requested_seed=seed,
            builder=builders[cls],
            used_actual_seeds=used_hard_actual_seeds[cls],
        )
        for cls, difficulty, seed in HARD_SOLO_SPECS
    ]
    hard_rows_by_requested_slot = {
        (entry.row["class"], entry.requested_seed): entry
        for entry in hard_rows
    }
    hard_portfolio_component_ids = tuple(
        hard_rows_by_requested_slot[(cls, 2)].row["id"]
        for cls in HARD_PORTFOLIO_COMPONENT_CLASSES
    )
    rows = list(medium_rows)
    rows.append(
        _build_portfolio_row(
            solo_rows=medium_rows,
            difficulty="medium",
            seed=1,
            component_ids=MEDIUM_PORTFOLIO_COMPONENT_IDS,
        )
    )
    rows.extend(hard_rows)
    rows.append(
        _build_portfolio_row(
            solo_rows=hard_rows,
            difficulty="hard",
            seed=2,
            component_ids=hard_portfolio_component_ids,
        )
    )
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

    _write_jsonl(ROOT / "questions.jsonl", questions)
    shutil.rmtree(ROOT / "gold", ignore_errors=True)
    print(f"Wrote {len(rows)} rows to questions.jsonl. Deleted gold/. Verified schema round-trip.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
