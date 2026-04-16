from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Any, Callable

from graph_coloring_instance import (
    GraphColoringInstance,
    build_instance as build_graph_coloring_instance,
    solution_summary as graph_coloring_summary,
    solve_exact_coloring,
    verify_answer as verify_graph_coloring_answer,
)
from jobshop_instance import (
    CoupledJobShopInstance,
    build_instance as build_jobshop_instance,
    schedule_summary,
    solve_exact_schedule,
    verify_schedule,
)
from steiner_coloring_gold import solve_joint_optimum
from steiner_coloring_instance import (
    SteinerColoringInstance,
    build_instance as build_steiner_instance,
    solution_summary as steiner_solution_summary,
)
from tsp_instance import (
    TSPInstance,
    build_instance as build_tsp_instance,
    solve_exact_tour,
    tour_summary,
    verify_tour,
)
from verify import verify_answer as verify_steiner_answer


Forecast = dict[str, float]


@dataclass(frozen=True)
class VerificationOutcome:
    feasible: bool
    score: float | None
    failure_reason: str | None
    normalized_answer: Any | None
    details: dict[str, Any]


@dataclass(frozen=True)
class PreparedProblem:
    problem_id: str
    label: str
    short_label: str
    value_cap: int
    metric_name: str
    baseline_score: float
    gold_score: float
    baseline_answer: Any
    gold_answer: Any
    problem_statement: str
    answer_contract: str
    instance: Any
    gold_method: str
    gold_wall_seconds: float
    verify_answer: Callable[[Any], VerificationOutcome]
    summarize_answer: Callable[[Any, float | None], str]

    @property
    def baseline_gap_pct(self) -> float:
        return 100.0 * (self.baseline_score - self.gold_score) / self.gold_score

    def gap_pct_for_score(self, score: float) -> float:
        return 100.0 * (score - self.gold_score) / self.gold_score

    def value_captured(self, score: float) -> float:
        denom = self.baseline_score - self.gold_score
        if denom <= 0:
            return 0.0
        ratio = (self.baseline_score - score) / denom
        clipped = max(0.0, min(1.0, ratio))
        return self.value_cap * clipped

    def realized_bucket(self, score: float) -> str:
        gap_pct = self.gap_pct_for_score(score)
        if gap_pct <= 5.0:
            return "within_5pct"
        if gap_pct <= 10.0:
            return "within_10pct"
        if gap_pct <= 20.0:
            return "within_20pct"
        if gap_pct <= 50.0:
            return "within_50pct"
        return "miss"


def build_portfolio(seed: int, min_baseline_gap_pct: float = 15.0) -> list[PreparedProblem]:
    return [
        _build_jobshop_problem(seed=seed, min_baseline_gap_pct=min_baseline_gap_pct),
        _build_steiner_problem(seed=seed, min_baseline_gap_pct=min_baseline_gap_pct),
        _build_tsp_problem(seed=seed, min_baseline_gap_pct=min_baseline_gap_pct),
        _build_graph_coloring_problem(seed=seed, min_baseline_gap_pct=min_baseline_gap_pct),
    ]


def forecast_event_map(problem: PreparedProblem, score: float) -> dict[str, float]:
    gap_pct = problem.gap_pct_for_score(score)
    return {
        "p_within_5pct": float(gap_pct <= 5.0),
        "p_within_10pct": float(gap_pct <= 10.0),
        "p_within_20pct": float(gap_pct <= 20.0),
        "p_within_50pct": float(gap_pct <= 50.0),
    }


def threshold_brier_mean(forecasts: list[Forecast], realized_score: float, problem: PreparedProblem) -> dict[str, float | None]:
    events = forecast_event_map(problem, realized_score)
    output: dict[str, float | None] = {}
    for key, event in events.items():
        if not forecasts:
            output[key] = None
            continue
        output[key] = sum((forecast[key] - event) ** 2 for forecast in forecasts) / len(forecasts)
    return output


def _build_jobshop_problem(seed: int, min_baseline_gap_pct: float) -> PreparedProblem:
    instance = build_jobshop_instance(
        seed=seed,
        n_jobs=5,
        n_machines=6,
        min_baseline_gap_pct=min_baseline_gap_pct,
    )
    gold_start = time.monotonic()
    gold_answer, gold_score = solve_exact_schedule(instance.jobs, instance.n_machines)
    gold_wall_seconds = time.monotonic() - gold_start
    if gold_wall_seconds > 60.0:
        raise RuntimeError(f"P1 gold solve exceeded 60s ({gold_wall_seconds:.2f}s)")
    if gold_score != instance.optimal_makespan:
        raise RuntimeError("P1 gold re-solve disagreed with stored optimum")

    def verify(answer: Any) -> VerificationOutcome:
        result = verify_schedule(
            jobs=instance.jobs,
            n_machines=instance.n_machines,
            schedule=answer,
        )
        return VerificationOutcome(
            feasible=result.is_feasible,
            score=float(result.verified_makespan) if result.verified_makespan is not None else None,
            failure_reason=result.failure_reason,
            normalized_answer=answer if result.is_feasible else None,
            details={
                "verified_makespan": result.verified_makespan,
            },
        )

    return PreparedProblem(
        problem_id="P1",
        label="Coupled jobshop 5x6",
        short_label="Jobshop",
        value_cap=50,
        metric_name="makespan",
        baseline_score=float(instance.baseline_makespan),
        gold_score=float(instance.optimal_makespan),
        baseline_answer=instance.baseline_schedule,
        gold_answer=gold_answer,
        problem_statement=instance.problem_statement,
        answer_contract=(
            'Object with "factory_a", "factory_b", and "makespan". '
            'Each factory maps every machine name to a list of [job_id, start, end] triples.'
        ),
        instance=instance,
        gold_method="CP-SAT exact schedule",
        gold_wall_seconds=gold_wall_seconds,
        verify_answer=verify,
        summarize_answer=lambda answer, score: schedule_summary(answer),
    )


def _build_steiner_problem(seed: int, min_baseline_gap_pct: float) -> PreparedProblem:
    instance = build_steiner_instance(
        seed=seed,
        n=8,
        k=4,
        n_terminals=3,
        min_baseline_gap_pct=min_baseline_gap_pct,
        require_coupling=True,
    )
    gold_start = time.monotonic()
    gold_answer, gold_score = solve_joint_optimum(instance)
    gold_wall_seconds = time.monotonic() - gold_start
    if gold_wall_seconds > 60.0:
        raise RuntimeError(f"P2 gold solve exceeded 60s ({gold_wall_seconds:.2f}s)")
    if gold_score != instance.optimal_cost:
        raise RuntimeError("P2 gold re-solve disagreed with stored optimum")

    def verify(answer: Any) -> VerificationOutcome:
        result = verify_steiner_answer(instance, answer)
        return VerificationOutcome(
            feasible=result.feasible,
            score=float(result.computed_cost) if result.computed_cost is not None else None,
            failure_reason=result.failure_reason,
            normalized_answer=result.normalized_answer,
            details={
                "edge_cost": result.edge_cost,
                "num_frequencies_used": result.num_frequencies_used,
                "computed_cost": result.computed_cost,
            },
        )

    return PreparedProblem(
        problem_id="P2",
        label="Steiner x coloring N=8 K=4",
        short_label="Steiner",
        value_cap=60,
        metric_name="total_cost",
        baseline_score=float(instance.baseline_cost),
        gold_score=float(instance.optimal_cost),
        baseline_answer=instance.baseline_answer,
        gold_answer=gold_answer,
        problem_statement=instance.problem_statement,
        answer_contract='Object with "edges": [["Port", "Bay"], ...] and "frequencies": {"Port": 1, ...}.',
        instance=instance,
        gold_method="Exact joint enumeration",
        gold_wall_seconds=gold_wall_seconds,
        verify_answer=verify,
        summarize_answer=lambda answer, score: steiner_solution_summary(instance, answer, int(score) if score is not None else None),
    )


def _build_tsp_problem(seed: int, min_baseline_gap_pct: float) -> PreparedProblem:
    instance = build_tsp_instance(
        seed=seed,
        n_cities=20,
        min_baseline_gap_pct=min_baseline_gap_pct,
    )
    gold_start = time.monotonic()
    gold_answer, gold_score = solve_exact_tour(instance.coords)
    gold_wall_seconds = time.monotonic() - gold_start
    if gold_wall_seconds > 60.0:
        raise RuntimeError(f"P3 gold solve exceeded 60s ({gold_wall_seconds:.2f}s)")
    if not math.isclose(gold_score, instance.optimal_length, rel_tol=0.0, abs_tol=1e-6):
        raise RuntimeError("P3 gold re-solve disagreed with stored optimum")

    def verify(answer: Any) -> VerificationOutcome:
        result = verify_tour(instance, answer)
        return VerificationOutcome(
            feasible=result.feasible,
            score=result.computed_length,
            failure_reason=result.failure_reason,
            normalized_answer=list(result.normalized_tour) if result.normalized_tour is not None else None,
            details={
                "computed_length": result.computed_length,
            },
        )

    return PreparedProblem(
        problem_id="P3",
        label="Euclidean TSP-20",
        short_label="TSP",
        value_cap=20,
        metric_name="tour_length",
        baseline_score=instance.baseline_length,
        gold_score=instance.optimal_length,
        baseline_answer=list(instance.baseline_tour),
        gold_answer=list(gold_answer),
        problem_statement=instance.problem_statement,
        answer_contract="JSON array of all 20 city indices exactly once.",
        instance=instance,
        gold_method="CP-SAT exact circuit",
        gold_wall_seconds=gold_wall_seconds,
        verify_answer=verify,
        summarize_answer=lambda answer, score: tour_summary(instance, answer, score),
    )


def _build_graph_coloring_problem(seed: int, min_baseline_gap_pct: float) -> PreparedProblem:
    instance = build_graph_coloring_instance(
        seed=seed,
        n_nodes=30,
        num_colors=4,
        min_baseline_gap_pct=min_baseline_gap_pct,
    )
    gold_start = time.monotonic()
    gold_answer, gold_conflicts = solve_exact_coloring(instance)
    gold_wall_seconds = time.monotonic() - gold_start
    if gold_wall_seconds > 60.0:
        raise RuntimeError(f"P4 gold solve exceeded 60s ({gold_wall_seconds:.2f}s)")
    if gold_conflicts != instance.optimal_conflicts:
        raise RuntimeError("P4 gold re-solve disagreed with stored optimum")

    def verify(answer: Any) -> VerificationOutcome:
        result = verify_graph_coloring_answer(instance, answer)
        return VerificationOutcome(
            feasible=result.feasible,
            score=float(result.computed_cost) if result.computed_cost is not None else None,
            failure_reason=result.failure_reason,
            normalized_answer=result.normalized_answer,
            details={
                "conflict_count": result.conflict_count,
                "computed_cost": result.computed_cost,
            },
        )

    return PreparedProblem(
        problem_id="P4",
        label="Slack graph coloring 30 nodes",
        short_label="Coloring",
        value_cap=100,
        metric_name="scored_cost",
        baseline_score=float(4 + instance.baseline_conflicts),
        gold_score=float(4 + instance.optimal_conflicts),
        baseline_answer=instance.baseline_answer,
        gold_answer=gold_answer,
        problem_statement=instance.problem_statement,
        answer_contract='Object with "assignment": {"N01": 1, ..., "N30": 4}.',
        instance=instance,
        gold_method="CP-SAT exact min-conflict coloring",
        gold_wall_seconds=gold_wall_seconds,
        verify_answer=verify,
        summarize_answer=lambda answer, score: graph_coloring_summary(
            instance,
            answer,
            None if score is None else int(score - 4),
        ),
    )
