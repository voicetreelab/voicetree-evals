from __future__ import annotations

from dataclasses import dataclass
from random import Random
import time
from typing import Any, Callable, Iterable

try:
    from ortools.sat.python import cp_model
except ImportError:  # pragma: no cover - exercised in dependency-blocked environments
    cp_model = None


def _require_ortools() -> Any:
    if cp_model is None:
        raise RuntimeError(
            "ortools is not installed. Install hch/masked_block_jobshop/requirements.txt before building instances."
        )
    return cp_model


HEURISTIC_ORDER = (
    "baseline",
    "bottleneck_first",
    "family_first",
    "outlier_first",
    "due_date_first",
)
MAKESPAN_WEIGHT = 20


@dataclass(frozen=True)
class OperationSpec:
    machine_name: str
    duration: int


@dataclass(frozen=True)
class JobSpec:
    job_id: int
    operations: tuple[OperationSpec, ...]
    due_date: int
    tardiness_weight: int

    @property
    def total_processing_time(self) -> int:
        return sum(op.duration for op in self.operations)


@dataclass(frozen=True)
class HiddenJobMetadata:
    family_id: int
    is_bridge: bool
    is_outlier: bool
    partner_family_id: int | None


@dataclass(frozen=True)
class VerificationResult:
    is_feasible: bool
    verified_makespan: int | None
    verified_weighted_tardiness: int | None
    verified_objective: int | None
    failure_reason: str | None


@dataclass(frozen=True)
class HeuristicResult:
    name: str
    schedule: dict[str, Any]
    makespan: int
    weighted_tardiness: int
    objective: int
    notes: str
    gap_pct: float | None = None


@dataclass(frozen=True)
class SolveResult:
    schedule: dict[str, Any]
    makespan: int
    weighted_tardiness: int
    objective: int
    is_optimal: bool
    status_name: str
    wall_seconds: float


@dataclass(frozen=True)
class GenerationTuning:
    leak_prob: float
    shared_machine_bonus: int
    tight_due_factor: float
    loose_due_factor: float
    tight_weight_bonus: int


@dataclass(frozen=True)
class GeneratedCandidate:
    seed: int
    attempt_index: int
    n_jobs: int
    n_machines: int
    jobs: tuple[JobSpec, ...]
    hidden_job_metadata: dict[int, HiddenJobMetadata]
    preferred_machine_sets: dict[int, tuple[str, ...]]
    shared_machines: tuple[str, ...]
    tuning: GenerationTuning


@dataclass(frozen=True)
class MaskedBlockJobShopInstance:
    seed: int
    requested_n_jobs: int
    requested_n_machines: int
    n_jobs: int
    n_machines: int
    jobs: tuple[JobSpec, ...]
    baseline_schedule: dict[str, Any]
    baseline_makespan: int
    baseline_weighted_tardiness: int
    baseline_objective: int
    optimal_schedule: dict[str, Any]
    optimal_makespan: int
    optimal_weighted_tardiness: int
    optimal_objective: int
    optimal_proven: bool
    solver_status: str
    solver_wall_seconds: float
    heuristic_results: tuple[HeuristicResult, ...]
    heuristic_spread_pct: float
    problem_statement: str
    hidden_job_metadata: dict[int, HiddenJobMetadata]
    preferred_machine_sets: dict[int, tuple[str, ...]]
    shared_machines: tuple[str, ...]
    tuning: GenerationTuning
    attempt_index: int
    fallback_note: str | None = None

    @property
    def machine_names(self) -> tuple[str, ...]:
        return tuple(f"M{index}" for index in range(1, self.n_machines + 1))

    def jobs_by_id(self) -> dict[int, JobSpec]:
        return {job.job_id: job for job in self.jobs}

    def heuristic_by_name(self, name: str) -> HeuristicResult:
        for result in self.heuristic_results:
            if result.name == name:
                return result
        raise KeyError(name)


def build_instance(
    seed: int,
    n_jobs: int = 25,
    n_machines: int = 15,
    min_baseline_gap_pct: float | None = 20.0,
    min_heuristic_spread_pct: float = 5.0,
    max_heuristic_spread_pct: float = 35.0,
    max_generation_attempts: int = 24,
    cp_time_limit_s: float = 600.0,
) -> MaskedBlockJobShopInstance:
    requested_size = (n_jobs, n_machines)
    fallback_note: str | None = None
    size_queue = [requested_size]
    if requested_size == (25, 15):
        size_queue.append((20, 12))

    last_failure = "no candidate evaluated"
    for size_index, (size_jobs, size_machines) in enumerate(size_queue):
        for attempt_index in range(max_generation_attempts):
            candidate_seed = seed + size_index * 100_000 + attempt_index * 10_007
            tuning = _generation_tuning(attempt_index)
            candidate = _generate_candidate(
                seed=candidate_seed,
                attempt_index=attempt_index,
                n_jobs=size_jobs,
                n_machines=size_machines,
                tuning=tuning,
            )
            heuristic_results = run_preflight_heuristics(candidate.jobs, candidate.n_machines)
            heuristic_spread_pct = compute_heuristic_spread_pct(heuristic_results)
            if heuristic_spread_pct < min_heuristic_spread_pct:
                last_failure = (
                    f"attempt {attempt_index} at {size_jobs}x{size_machines} had only "
                    f"{heuristic_spread_pct:.2f}% heuristic spread"
                )
                continue
            if heuristic_spread_pct > max_heuristic_spread_pct:
                last_failure = (
                    f"attempt {attempt_index} at {size_jobs}x{size_machines} had too much "
                    f"heuristic spread ({heuristic_spread_pct:.2f}%)"
                )
                continue

            solve_result = solve_exact_schedule(
                jobs=candidate.jobs,
                n_machines=candidate.n_machines,
                time_limit_s=cp_time_limit_s,
            )
            if not solve_result.is_optimal and requested_size == (25, 15) and (size_jobs, size_machines) == (25, 15):
                fallback_note = (
                    "25x15 CP-SAT did not prove optimal within 600s "
                    f"(status={solve_result.status_name}, best_objective={solve_result.objective}); "
                    "fell back to 20x12."
                )
                last_failure = fallback_note
                break

            heuristic_with_gaps = tuple(
                HeuristicResult(
                    name=result.name,
                    schedule=result.schedule,
                    makespan=result.makespan,
                    weighted_tardiness=result.weighted_tardiness,
                    objective=result.objective,
                    notes=result.notes,
                    gap_pct=100.0 * (result.objective - solve_result.objective) / solve_result.objective,
                )
                for result in heuristic_results
            )
            baseline = _heuristic_by_name(heuristic_results, "baseline")
            baseline_gap_pct = (
                100.0 * (baseline.objective - solve_result.objective) / solve_result.objective
            )
            if min_baseline_gap_pct is not None and baseline_gap_pct < min_baseline_gap_pct:
                last_failure = (
                    f"attempt {attempt_index} at {size_jobs}x{size_machines} had baseline gap "
                    f"{baseline_gap_pct:.2f}%"
                )
                continue

            instance_stub = MaskedBlockJobShopInstance(
                seed=seed,
                requested_n_jobs=requested_size[0],
                requested_n_machines=requested_size[1],
                n_jobs=size_jobs,
                n_machines=size_machines,
                jobs=candidate.jobs,
                baseline_schedule=baseline.schedule,
                baseline_makespan=baseline.makespan,
                baseline_weighted_tardiness=baseline.weighted_tardiness,
                baseline_objective=baseline.objective,
                optimal_schedule=solve_result.schedule,
                optimal_makespan=solve_result.makespan,
                optimal_weighted_tardiness=solve_result.weighted_tardiness,
                optimal_objective=solve_result.objective,
                optimal_proven=solve_result.is_optimal,
                solver_status=solve_result.status_name,
                solver_wall_seconds=solve_result.wall_seconds,
                heuristic_results=heuristic_with_gaps,
                heuristic_spread_pct=heuristic_spread_pct,
                problem_statement="",
                hidden_job_metadata=candidate.hidden_job_metadata,
                preferred_machine_sets=candidate.preferred_machine_sets,
                shared_machines=candidate.shared_machines,
                tuning=candidate.tuning,
                attempt_index=attempt_index,
                fallback_note=fallback_note,
            )
            problem_statement = render_problem(instance_stub)
            return MaskedBlockJobShopInstance(
                seed=seed,
                requested_n_jobs=requested_size[0],
                requested_n_machines=requested_size[1],
                n_jobs=size_jobs,
                n_machines=size_machines,
                jobs=candidate.jobs,
                baseline_schedule=baseline.schedule,
                baseline_makespan=baseline.makespan,
                baseline_weighted_tardiness=baseline.weighted_tardiness,
                baseline_objective=baseline.objective,
                optimal_schedule=solve_result.schedule,
                optimal_makespan=solve_result.makespan,
                optimal_weighted_tardiness=solve_result.weighted_tardiness,
                optimal_objective=solve_result.objective,
                optimal_proven=solve_result.is_optimal,
                solver_status=solve_result.status_name,
                solver_wall_seconds=solve_result.wall_seconds,
                heuristic_results=heuristic_with_gaps,
                heuristic_spread_pct=heuristic_spread_pct,
                problem_statement=problem_statement,
                hidden_job_metadata=candidate.hidden_job_metadata,
                preferred_machine_sets=candidate.preferred_machine_sets,
                shared_machines=candidate.shared_machines,
                tuning=candidate.tuning,
                attempt_index=attempt_index,
                fallback_note=fallback_note,
            )

        if fallback_note is not None and (size_jobs, size_machines) == requested_size:
            continue

    raise RuntimeError(
        "failed to generate a masked block jobshop instance meeting the pre-flight checks: "
        f"{last_failure}"
    )


def _generation_tuning(attempt_index: int) -> GenerationTuning:
    leak_values = [0.18, 0.20, 0.22, 0.24]
    shared_bonus_values = [3, 5, 7]
    tight_due_values = [0.52, 0.58, 0.64]
    loose_due_values = [0.96, 1.04, 1.12]
    tight_weight_bonus_values = [0, 1, 2]
    return GenerationTuning(
        leak_prob=leak_values[attempt_index % len(leak_values)],
        shared_machine_bonus=shared_bonus_values[(attempt_index // len(leak_values)) % len(shared_bonus_values)],
        tight_due_factor=tight_due_values[(attempt_index // 3) % len(tight_due_values)],
        loose_due_factor=loose_due_values[(attempt_index // 5) % len(loose_due_values)],
        tight_weight_bonus=tight_weight_bonus_values[(attempt_index // 7) % len(tight_weight_bonus_values)],
    )


def _generate_candidate(
    *,
    seed: int,
    attempt_index: int,
    n_jobs: int,
    n_machines: int,
    tuning: GenerationTuning,
) -> GeneratedCandidate:
    rng = Random(seed)
    machine_names = [f"M{index}" for index in range(1, n_machines + 1)]
    shared_machines = tuple(machine_names[:3])
    local_bottlenecks = machine_names[3:7]
    peripheral_machines = machine_names[7:]
    if len(local_bottlenecks) < 4 or len(shared_machines) < 3:
        raise RuntimeError("masked block jobshop requires at least 7 machines")

    preferred_machine_sets: dict[int, tuple[str, ...]] = {}
    for family_id in range(4):
        shared_pair = [
            shared_machines[family_id % len(shared_machines)],
            shared_machines[(family_id + 1) % len(shared_machines)],
        ]
        local_machine = local_bottlenecks[family_id]
        peripheral_pair = [
            peripheral_machines[(2 * family_id) % len(peripheral_machines)],
            peripheral_machines[(2 * family_id + 1) % len(peripheral_machines)],
        ]
        preferred_machine_sets[family_id] = tuple(dict.fromkeys(shared_pair + [local_machine] + peripheral_pair))

    family_sizes = _family_sizes(n_jobs)
    family_jobs: dict[int, list[int]] = {}
    next_job_id = 1
    for family_id, size in enumerate(family_sizes):
        family_jobs[family_id] = list(range(next_job_id, next_job_id + size))
        rng.shuffle(family_jobs[family_id])
        next_job_id += size

    hidden_job_metadata: dict[int, HiddenJobMetadata] = {}
    for family_id, job_ids in family_jobs.items():
        for offset, job_id in enumerate(job_ids):
            partner_family = None
            is_bridge = offset < 2
            if is_bridge:
                partner_candidates = [value for value in range(4) if value != family_id]
                partner_family = partner_candidates[(job_id + family_id + attempt_index) % len(partner_candidates)]
            hidden_job_metadata[job_id] = HiddenJobMetadata(
                family_id=family_id,
                is_bridge=is_bridge,
                is_outlier=False,
                partner_family_id=partner_family,
            )

    outlier_job_ids = _choose_outliers(rng, family_jobs)
    for job_id in outlier_job_ids:
        info = hidden_job_metadata[job_id]
        hidden_job_metadata[job_id] = HiddenJobMetadata(
            family_id=info.family_id,
            is_bridge=info.is_bridge,
            is_outlier=True,
            partner_family_id=info.partner_family_id,
        )

    ops_per_job = 7 if n_machines >= 15 else 6
    raw_jobs: list[tuple[int, tuple[OperationSpec, ...]]] = []
    for job_id in range(1, n_jobs + 1):
        meta = hidden_job_metadata[job_id]
        route = _draw_route(
            rng=rng,
            family_id=meta.family_id,
            partner_family_id=meta.partner_family_id,
            is_bridge=meta.is_bridge,
            n_ops=ops_per_job,
            preferred_machine_sets=preferred_machine_sets,
            shared_machines=shared_machines,
            all_machine_names=machine_names,
            tuning=tuning,
        )
        operations = tuple(
            OperationSpec(
                machine_name=machine_name,
                duration=_draw_duration(
                    rng=rng,
                    machine_name=machine_name,
                    family_id=meta.family_id,
                    preferred_machine_sets=preferred_machine_sets,
                    shared_machines=shared_machines,
                    is_outlier=meta.is_outlier,
                    shared_machine_bonus=tuning.shared_machine_bonus,
                ),
            )
            for machine_name in route
        )
        raw_jobs.append((job_id, operations))

    jobs = _attach_due_dates(
        rng=rng,
        raw_jobs=raw_jobs,
        hidden_job_metadata=hidden_job_metadata,
        machine_names=tuple(machine_names),
        tuning=tuning,
    )
    return GeneratedCandidate(
        seed=seed,
        attempt_index=attempt_index,
        n_jobs=n_jobs,
        n_machines=n_machines,
        jobs=jobs,
        hidden_job_metadata=hidden_job_metadata,
        preferred_machine_sets=preferred_machine_sets,
        shared_machines=shared_machines,
        tuning=tuning,
    )


def _family_sizes(n_jobs: int) -> tuple[int, int, int, int]:
    base = n_jobs // 4
    remainder = n_jobs % 4
    sizes = [base] * 4
    for index in range(remainder):
        sizes[index] += 1
    sizes.sort(reverse=True)
    return tuple(sizes)  # type: ignore[return-value]


def _choose_outliers(rng: Random, family_jobs: dict[int, list[int]]) -> set[int]:
    selected: set[int] = set()
    family_ids = list(family_jobs)
    rng.shuffle(family_ids)
    for family_id in family_ids:
        if len(selected) >= 5:
            break
        selected.add(family_jobs[family_id][0])
    remaining = [job_id for jobs in family_jobs.values() for job_id in jobs if job_id not in selected]
    rng.shuffle(remaining)
    for job_id in remaining:
        if len(selected) >= 5:
            break
        selected.add(job_id)
    return selected


def _draw_route(
    *,
    rng: Random,
    family_id: int,
    partner_family_id: int | None,
    is_bridge: bool,
    n_ops: int,
    preferred_machine_sets: dict[int, tuple[str, ...]],
    shared_machines: tuple[str, ...],
    all_machine_names: list[str],
    tuning: GenerationTuning,
) -> tuple[str, ...]:
    preferred = list(preferred_machine_sets[family_id])
    local_machine = preferred[2]
    other_preferred = [
        machine
        for other_family, machine_set in preferred_machine_sets.items()
        if other_family != family_id
        for machine in machine_set
        if machine not in preferred
    ]
    partner_pool = list(preferred_machine_sets[partner_family_id]) if partner_family_id is not None else []

    selected: list[str] = []
    selected.append(_pick_unused(rng, list(shared_machines), selected, all_machine_names))
    selected.append(_pick_unused(rng, [local_machine], selected, all_machine_names))
    selected.append(_pick_unused(rng, preferred, selected, all_machine_names))
    if is_bridge and partner_pool:
        selected.append(_pick_unused(rng, partner_pool, selected, all_machine_names))
    else:
        leak_pool = partner_pool + other_preferred
        selected.append(_pick_unused(rng, leak_pool, selected, all_machine_names))
    selected.append(_pick_unused(rng, list(shared_machines), selected, all_machine_names))

    preferred_target = max(1, round(n_ops * (1.0 - tuning.leak_prob)))
    preferred_target = min(n_ops - 1, preferred_target)
    while len(selected) < preferred_target:
        preferred_pool = list(preferred) + [local_machine, local_machine]
        selected.append(_pick_unused(rng, preferred_pool, selected, all_machine_names))
    while len(selected) < n_ops:
        leak_pool = partner_pool + other_preferred + list(shared_machines)
        selected.append(_pick_unused(rng, leak_pool, selected, all_machine_names))

    route = selected[:n_ops]
    rng.shuffle(route)
    return tuple(route)


def _pick_unused(rng: Random, pool: Iterable[str], selected: list[str], all_machine_names: list[str]) -> str:
    candidates = [machine for machine in pool if machine not in selected]
    if not candidates:
        candidates = [machine for machine in all_machine_names if machine not in selected]
    if not candidates:
        raise RuntimeError("could not draw a unique machine route")
    return rng.choice(candidates)


def _draw_duration(
    *,
    rng: Random,
    machine_name: str,
    family_id: int,
    preferred_machine_sets: dict[int, tuple[str, ...]],
    shared_machines: tuple[str, ...],
    is_outlier: bool,
    shared_machine_bonus: int,
) -> int:
    duration = rng.randint(4, 11)
    if machine_name in shared_machines:
        duration += shared_machine_bonus + rng.randint(0, 3)
    if machine_name == preferred_machine_sets[family_id][2]:
        duration += 3 + rng.randint(0, 2)
    if machine_name in preferred_machine_sets[family_id]:
        duration += 1
    if is_outlier:
        duration *= 3
    return duration


def _attach_due_dates(
    *,
    rng: Random,
    raw_jobs: list[tuple[int, tuple[OperationSpec, ...]]],
    hidden_job_metadata: dict[int, HiddenJobMetadata],
    machine_names: tuple[str, ...],
    tuning: GenerationTuning,
) -> tuple[JobSpec, ...]:
    machine_loads = {machine_name: 0 for machine_name in machine_names}
    total_processing_by_job: dict[int, int] = {}
    for job_id, operations in raw_jobs:
        total_processing_by_job[job_id] = sum(op.duration for op in operations)
        for op in operations:
            machine_loads[op.machine_name] += op.duration

    nominal_pressure = max(machine_loads.values())
    non_outlier_job_ids = [
        job_id for job_id, meta in hidden_job_metadata.items() if not meta.is_outlier
    ]
    tight_count = max(1, round(0.30 * len(non_outlier_job_ids)))
    rng.shuffle(non_outlier_job_ids)
    tight_job_ids = set(non_outlier_job_ids[:tight_count])

    jobs: list[JobSpec] = []
    for job_id, operations in raw_jobs:
        total_processing = total_processing_by_job[job_id]
        if job_id in tight_job_ids:
            due_date = max(
                total_processing,
                int(total_processing * tuning.tight_due_factor + 0.42 * nominal_pressure + rng.randint(-8, 10)),
            )
            tardiness_weight = rng.randint(6 + tuning.tight_weight_bonus, 9 + tuning.tight_weight_bonus)
        else:
            due_date = max(
                total_processing,
                int(total_processing * tuning.loose_due_factor + 0.78 * nominal_pressure + rng.randint(-12, 20)),
            )
            tardiness_weight = rng.randint(1, 3)
        jobs.append(
            JobSpec(
                job_id=job_id,
                operations=operations,
                due_date=due_date,
                tardiness_weight=tardiness_weight,
            )
        )
    return tuple(jobs)


def run_preflight_heuristics(jobs: tuple[JobSpec, ...], n_machines: int) -> tuple[HeuristicResult, ...]:
    return tuple(
        [
            _run_baseline(jobs, n_machines),
            _run_bottleneck_first(jobs, n_machines),
            _run_family_first(jobs, n_machines),
            _run_outlier_first(jobs, n_machines),
            _run_due_date_first(jobs, n_machines),
        ]
    )


def compute_heuristic_spread_pct(results: tuple[HeuristicResult, ...]) -> float:
    objectives = [result.objective for result in results]
    best = min(objectives)
    worst = max(objectives)
    return 100.0 * (worst - best) / best


def build_baseline_schedule(jobs: tuple[JobSpec, ...], n_machines: int) -> dict[str, Any]:
    return _run_baseline(jobs, n_machines).schedule


def _run_baseline(jobs: tuple[JobSpec, ...], n_machines: int) -> HeuristicResult:
    return _dispatch_heuristic(
        name="baseline",
        jobs=jobs,
        n_machines=n_machines,
        notes="SPT dispatch with earliest-start tie-breaking.",
        priority_fn=lambda ctx: (
            ctx["earliest_start"],
            ctx["op_duration"],
            ctx["job_due_date"],
            ctx["job_id"],
        ),
    )


def _run_bottleneck_first(jobs: tuple[JobSpec, ...], n_machines: int) -> HeuristicResult:
    machine_loads = _machine_loads(jobs, n_machines)
    top_three = {machine for machine, _ in sorted(machine_loads.items(), key=lambda item: (-item[1], item[0]))[:3]}
    return _dispatch_heuristic(
        name="bottleneck_first",
        jobs=jobs,
        n_machines=n_machines,
        notes=f"Prioritize operations on the top-3 loaded machines: {sorted(top_three)}.",
        priority_fn=lambda ctx: (
            ctx["earliest_start"],
            0 if ctx["machine_name"] in top_three else 1,
            -ctx["remaining_on_top3"],
            ctx["job_due_date"],
            ctx["job_id"],
        ),
        context_enricher=lambda ctx: {
            "remaining_on_top3": sum(
                op.duration
                for op in ctx["remaining_operations"]
                if op.machine_name in top_three
            )
        },
    )


def _run_family_first(jobs: tuple[JobSpec, ...], n_machines: int) -> HeuristicResult:
    clusters = _detect_job_clusters_via_modularity(jobs)
    cluster_rank: dict[int, int] = {}
    for rank, cluster in enumerate(
        sorted(
            clusters,
            key=lambda cluster_jobs: (
                -sum(_job_total_processing(jobs, job_id) for job_id in cluster_jobs),
                min(_job_due_date(jobs, job_id) for job_id in cluster_jobs),
                min(cluster_jobs),
            ),
        )
    ):
        for job_id in cluster:
            cluster_rank[job_id] = rank
    return _dispatch_heuristic(
        name="family_first",
        jobs=jobs,
        n_machines=n_machines,
        notes="Detect job communities from the job-machine bipartite projection and schedule cluster-by-cluster.",
        priority_fn=lambda ctx: (
            ctx["earliest_start"],
            cluster_rank[ctx["job_id"]],
            ctx["op_duration"],
            ctx["job_due_date"],
            ctx["job_id"],
        ),
    )


def _run_outlier_first(jobs: tuple[JobSpec, ...], n_machines: int) -> HeuristicResult:
    long_jobs = {
        job.job_id
        for job in sorted(jobs, key=lambda item: (-item.total_processing_time, item.job_id))[:5]
    }
    return _dispatch_heuristic(
        name="outlier_first",
        jobs=jobs,
        n_machines=n_machines,
        notes=f"Sequence the five longest jobs first: {sorted(long_jobs)}.",
        priority_fn=lambda ctx: (
            ctx["earliest_start"],
            0 if ctx["job_id"] in long_jobs else 1,
            -ctx["remaining_job_processing"],
            ctx["job_due_date"],
            ctx["job_id"],
        ),
        context_enricher=lambda ctx: {
            "remaining_job_processing": sum(op.duration for op in ctx["remaining_operations"])
        },
    )


def _run_due_date_first(jobs: tuple[JobSpec, ...], n_machines: int) -> HeuristicResult:
    return _dispatch_heuristic(
        name="due_date_first",
        jobs=jobs,
        n_machines=n_machines,
        notes="Earliest-due-date priority with high-weight tie-breaking.",
        priority_fn=lambda ctx: (
            ctx["earliest_start"],
            ctx["job_due_date"],
            -ctx["job_tardiness_weight"],
            ctx["op_duration"],
            ctx["job_id"],
        ),
    )


def _dispatch_heuristic(
    *,
    name: str,
    jobs: tuple[JobSpec, ...],
    n_machines: int,
    notes: str,
    priority_fn: Callable[[dict[str, Any]], tuple[Any, ...]],
    context_enricher: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> HeuristicResult:
    machine_available = {f"M{index}": 0 for index in range(1, n_machines + 1)}
    machine_schedule: dict[str, list[list[Any]]] = {f"M{index}": [] for index in range(1, n_machines + 1)}
    job_next_index = {job.job_id: 0 for job in jobs}
    job_available = {job.job_id: 0 for job in jobs}
    jobs_by_id = {job.job_id: job for job in jobs}

    scheduled_ops = 0
    target_ops = sum(len(job.operations) for job in jobs)
    while scheduled_ops < target_ops:
        candidates: list[tuple[tuple[Any, ...], int, int, int, int]] = []
        for job in jobs:
            step_index = job_next_index[job.job_id]
            if step_index >= len(job.operations):
                continue
            op = job.operations[step_index]
            earliest_start = max(job_available[job.job_id], machine_available[op.machine_name])
            ctx: dict[str, Any] = {
                "job_id": job.job_id,
                "step_index": step_index,
                "machine_name": op.machine_name,
                "op_duration": op.duration,
                "earliest_start": earliest_start,
                "job_due_date": job.due_date,
                "job_tardiness_weight": job.tardiness_weight,
                "remaining_operations": job.operations[step_index:],
            }
            if context_enricher is not None:
                ctx.update(context_enricher(ctx))
            priority = priority_fn(ctx)
            candidates.append((priority, earliest_start, job.job_id, step_index, op.duration))

        if not candidates:
            raise RuntimeError(f"{name} heuristic could not select a schedulable operation")

        _, earliest_start, job_id, step_index, _ = min(candidates)
        job = jobs_by_id[job_id]
        op = job.operations[step_index]
        end = earliest_start + op.duration
        machine_schedule[op.machine_name].append([f"J{job_id}", earliest_start, end])
        machine_available[op.machine_name] = end
        job_available[job_id] = end
        job_next_index[job_id] += 1
        scheduled_ops += 1

    schedule = _build_schedule_payload(machine_schedule, jobs)
    verification = verify_schedule(jobs=jobs, n_machines=n_machines, schedule=schedule)
    if not verification.is_feasible or verification.verified_objective is None:
        raise RuntimeError(f"{name} heuristic produced infeasible schedule: {verification.failure_reason}")
    return HeuristicResult(
        name=name,
        schedule=schedule,
        makespan=verification.verified_makespan or 0,
        weighted_tardiness=verification.verified_weighted_tardiness or 0,
        objective=verification.verified_objective,
        notes=notes,
    )


def solve_exact_schedule(
    jobs: tuple[JobSpec, ...],
    n_machines: int,
    *,
    time_limit_s: float = 600.0,
) -> SolveResult:
    cp = _require_ortools()
    model = cp.CpModel()
    horizon = sum(op.duration for job in jobs for op in job.operations)
    op_vars: dict[tuple[int, int], tuple[Any, Any, Any]] = {}
    machine_to_intervals: dict[str, list[Any]] = {f"M{index}": [] for index in range(1, n_machines + 1)}
    completion_vars: dict[int, Any] = {}
    tardiness_vars: dict[int, Any] = {}

    for job in jobs:
        previous_end = None
        for step_index, op in enumerate(job.operations):
            start = model.NewIntVar(0, horizon, f"J{job.job_id}_S{step_index}_start")
            end = model.NewIntVar(0, horizon, f"J{job.job_id}_S{step_index}_end")
            interval = model.NewIntervalVar(start, op.duration, end, f"J{job.job_id}_S{step_index}_interval")
            op_vars[(job.job_id, step_index)] = (start, end, interval)
            machine_to_intervals[op.machine_name].append(interval)
            if previous_end is not None:
                model.Add(start >= previous_end)
            previous_end = end
        if previous_end is None:
            raise RuntimeError(f"job J{job.job_id} has no operations")
        completion_vars[job.job_id] = previous_end
        tardiness = model.NewIntVar(0, horizon, f"J{job.job_id}_tardiness")
        model.Add(tardiness >= previous_end - job.due_date)
        model.Add(tardiness >= 0)
        tardiness_vars[job.job_id] = tardiness

    for intervals in machine_to_intervals.values():
        model.AddNoOverlap(intervals)

    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(makespan, list(completion_vars.values()))
    weighted_tardiness_upper = horizon * sum(job.tardiness_weight for job in jobs)
    weighted_tardiness = model.NewIntVar(0, weighted_tardiness_upper, "weighted_tardiness")
    model.Add(weighted_tardiness == sum(job.tardiness_weight * tardiness_vars[job.job_id] for job in jobs))
    objective = model.NewIntVar(0, weighted_tardiness_upper + MAKESPAN_WEIGHT * horizon, "objective")
    model.Add(objective == MAKESPAN_WEIGHT * makespan + weighted_tardiness)
    model.Minimize(objective)

    solver = cp.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.num_search_workers = 8

    start_time = time.monotonic()
    status = solver.Solve(model)
    wall_seconds = time.monotonic() - start_time
    if status not in (cp.OPTIMAL, cp.FEASIBLE):
        raise RuntimeError(
            "failed to obtain a feasible CP-SAT solution for masked block jobshop instance: "
            f"{solver.StatusName(status)}"
        )

    machine_schedule: dict[str, list[list[Any]]] = {f"M{idx}": [] for idx in range(1, n_machines + 1)}
    for job in jobs:
        for step_index, op in enumerate(job.operations):
            start_var, end_var, _ = op_vars[(job.job_id, step_index)]
            machine_schedule[op.machine_name].append(
                [f"J{job.job_id}", solver.Value(start_var), solver.Value(end_var)]
            )
    schedule = _build_schedule_payload(machine_schedule, jobs)
    schedule["makespan"] = solver.Value(makespan)
    schedule["weighted_tardiness"] = solver.Value(weighted_tardiness)
    schedule["objective"] = solver.Value(objective)

    return SolveResult(
        schedule=schedule,
        makespan=solver.Value(makespan),
        weighted_tardiness=solver.Value(weighted_tardiness),
        objective=solver.Value(objective),
        is_optimal=status == cp.OPTIMAL,
        status_name=solver.StatusName(status),
        wall_seconds=wall_seconds,
    )


def verify_schedule(
    *,
    jobs: tuple[JobSpec, ...],
    n_machines: int,
    schedule: dict[str, Any] | None,
) -> VerificationResult:
    if not isinstance(schedule, dict):
        return VerificationResult(False, None, None, None, "schedule must be an object")

    machines = schedule.get("machines")
    if not isinstance(machines, dict):
        return VerificationResult(False, None, None, None, "schedule must contain a machines object")
    claimed_makespan = _maybe_int(schedule.get("makespan"))
    claimed_weighted_tardiness = _maybe_int(schedule.get("weighted_tardiness"))
    claimed_objective = _maybe_int(schedule.get("objective"))

    expected_machines = {f"M{index}" for index in range(1, n_machines + 1)}
    parsed = _parse_machine_schedule(machines, expected_machines)
    if isinstance(parsed, str):
        return VerificationResult(False, None, None, None, parsed)

    jobs_by_id = {job.job_id: job for job in jobs}
    start_lookup: dict[int, dict[str, int]] = {job.job_id: {} for job in jobs}
    completion_lookup: dict[int, dict[str, int]] = {job.job_id: {} for job in jobs}
    seen_ops: set[tuple[int, str]] = set()
    max_end = 0

    for machine_name, entries in parsed.items():
        reason = _check_machine_conflicts(entries)
        if reason:
            return VerificationResult(False, None, None, None, reason)
        for job_id, start, end in entries:
            job = jobs_by_id.get(job_id)
            if job is None:
                return VerificationResult(False, None, None, None, f"unknown job J{job_id} in {machine_name}")
            duration = _duration_for_machine(job.operations, machine_name)
            if duration is None:
                return VerificationResult(False, None, None, None, f"job J{job_id} does not use machine {machine_name}")
            if end - start != duration:
                return VerificationResult(
                    False,
                    None,
                    None,
                    None,
                    f"duration mismatch for J{job_id} on {machine_name}: expected {duration}, got {end - start}",
                )
            key = (job_id, machine_name)
            if key in seen_ops:
                return VerificationResult(False, None, None, None, f"duplicate operation for J{job_id} on {machine_name}")
            seen_ops.add(key)
            start_lookup[job_id][machine_name] = start
            completion_lookup[job_id][machine_name] = end
            max_end = max(max_end, end)

    weighted_tardiness = 0
    for job in jobs:
        expected_ops = {(job.job_id, op.machine_name) for op in job.operations}
        if len(seen_ops.intersection(expected_ops)) != len(job.operations):
            return VerificationResult(False, None, None, None, f"missing operations for J{job.job_id}")
        reason = _check_route_precedence(
            job.operations,
            start_lookup[job.job_id],
            completion_lookup[job.job_id],
        )
        if reason:
            return VerificationResult(False, None, None, None, f"precedence failed for J{job.job_id}: {reason}")
        last_machine = job.operations[-1].machine_name
        completion = completion_lookup[job.job_id][last_machine]
        weighted_tardiness += job.tardiness_weight * max(0, completion - job.due_date)

    objective = MAKESPAN_WEIGHT * max_end + weighted_tardiness
    if claimed_makespan is not None and claimed_makespan != max_end:
        return VerificationResult(False, None, None, None, f"claimed makespan {claimed_makespan} != verified {max_end}")
    if claimed_weighted_tardiness is not None and claimed_weighted_tardiness != weighted_tardiness:
        return VerificationResult(
            False,
            None,
            None,
            None,
            f"claimed weighted tardiness {claimed_weighted_tardiness} != verified {weighted_tardiness}",
        )
    if claimed_objective is not None and claimed_objective != objective:
        return VerificationResult(False, None, None, None, f"claimed objective {claimed_objective} != verified {objective}")

    return VerificationResult(True, max_end, weighted_tardiness, objective, None)


def _maybe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except Exception:
        return None


def _parse_machine_schedule(
    machines: dict[str, Any],
    expected_machines: set[str],
) -> dict[str, list[tuple[int, int, int]]] | str:
    parsed: dict[str, list[tuple[int, int, int]]] = {}
    for machine_name in expected_machines:
        entries = machines.get(machine_name, [])
        if not isinstance(entries, list):
            return f"machine {machine_name} must map to a list"
        machine_entries: list[tuple[int, int, int]] = []
        for item in entries:
            if not isinstance(item, list) or len(item) != 3:
                return f"machine {machine_name} entries must be [job, start, end]"
            job_label, start, end = item
            try:
                job_id = int(str(job_label).lstrip("Jj"))
                start_int = int(start)
                end_int = int(end)
            except Exception:
                return f"machine {machine_name} has non-integer schedule entry"
            if end_int <= start_int:
                return f"machine {machine_name} has non-positive duration for J{job_id}"
            machine_entries.append((job_id, start_int, end_int))
        parsed[machine_name] = sorted(machine_entries, key=lambda entry: (entry[1], entry[2], entry[0]))

    unknown = set(machines) - expected_machines
    if unknown:
        return f"unknown machines in schedule: {sorted(unknown)}"
    return parsed


def _check_machine_conflicts(entries: list[tuple[int, int, int]]) -> str | None:
    for index in range(1, len(entries)):
        previous = entries[index - 1]
        current = entries[index]
        if current[1] < previous[2]:
            return f"machine overlap between J{previous[0]} and J{current[0]}"
    return None


def _duration_for_machine(route: tuple[OperationSpec, ...], machine_name: str) -> int | None:
    for op in route:
        if op.machine_name == machine_name:
            return op.duration
    return None


def _check_route_precedence(
    route: tuple[OperationSpec, ...],
    start_lookup: dict[str, int],
    completion_lookup: dict[str, int],
) -> str | None:
    previous_end = None
    for op in route:
        if op.machine_name not in start_lookup or op.machine_name not in completion_lookup:
            return f"missing timing for {op.machine_name}"
        current_start = start_lookup[op.machine_name]
        current_end = completion_lookup[op.machine_name]
        if previous_end is not None and current_start < previous_end:
            return f"{op.machine_name} starts at {current_start} before predecessor finished at {previous_end}"
        previous_end = current_end
    return None


def _build_schedule_payload(
    machine_schedule: dict[str, list[list[Any]]],
    jobs: tuple[JobSpec, ...],
) -> dict[str, Any]:
    for machine_name in machine_schedule:
        machine_schedule[machine_name].sort(key=lambda item: (item[1], item[2], item[0]))
    completion = _completion_times_from_schedule(machine_schedule, jobs)
    makespan = max(completion.values(), default=0)
    weighted_tardiness = sum(
        job.tardiness_weight * max(0, completion[job.job_id] - job.due_date)
        for job in jobs
    )
    return {
        "machines": machine_schedule,
        "makespan": makespan,
        "weighted_tardiness": weighted_tardiness,
        "objective": MAKESPAN_WEIGHT * makespan + weighted_tardiness,
    }


def _completion_times_from_schedule(
    machine_schedule: dict[str, list[list[Any]]],
    jobs: tuple[JobSpec, ...],
) -> dict[int, int]:
    completion = {job.job_id: 0 for job in jobs}
    for entries in machine_schedule.values():
        for job_label, _, end in entries:
            job_id = int(str(job_label).lstrip("Jj"))
            completion[job_id] = max(completion[job_id], int(end))
    return completion


def schedule_summary(schedule: dict[str, Any]) -> str:
    lines = []
    for machine_name in sorted(schedule.get("machines", {})):
        entries = ",".join(
            f"{job}[{start}-{end}]"
            for job, start, end in schedule["machines"][machine_name]
        )
        lines.append(f"{machine_name}: {entries}")
    lines.append(f"Makespan: {schedule.get('makespan')}")
    lines.append(f"Weighted tardiness: {schedule.get('weighted_tardiness')}")
    lines.append(f"Objective: {schedule.get('objective')}")
    return "\n".join(lines)


def render_problem(instance: MaskedBlockJobShopInstance) -> str:
    baseline_summary = schedule_summary(instance.baseline_schedule)
    job_lines: list[str] = []
    for job in instance.jobs:
        route = " -> ".join(f"{op.machine_name} ({op.duration})" for op in job.operations)
        job_lines.append(
            f"- Job J{job.job_id}: {route}; due_date={job.due_date}; tardiness_weight={job.tardiness_weight}"
        )
    return f"""You run a single machine shop with {instance.n_jobs} jobs and {instance.n_machines} machines.
Each job is an ordered sequence of operations. Machines are exclusive and operations cannot be preempted.
Every job must respect its listed order.

Objective:
- makespan = the completion time of the last job
- weighted tardiness = sum over jobs of tardiness_weight * max(0, completion_time - due_date)
- total objective = {MAKESPAN_WEIGHT} * makespan + weighted tardiness
- lower is better

Instance data:
{chr(10).join(job_lines)}

Constraints:
- Each machine handles at most one operation at a time.
- Each listed operation must appear exactly once in your schedule.
- Start/end times must be integers.
- Your BEST_GUESS should contain a `machines` object keyed by machine name, plus `makespan`, `weighted_tardiness`, and `objective`.

A deterministic feasible baseline schedule is provided below. If you stop immediately or fail to produce a valid schedule, this baseline is what gets scored.
Baseline makespan: {instance.baseline_makespan}
Baseline weighted tardiness: {instance.baseline_weighted_tardiness}
Baseline objective: {instance.baseline_objective}
Baseline schedule summary:
{baseline_summary}
"""


def _machine_loads(jobs: tuple[JobSpec, ...], n_machines: int) -> dict[str, int]:
    loads = {f"M{index}": 0 for index in range(1, n_machines + 1)}
    for job in jobs:
        for op in job.operations:
            loads[op.machine_name] += op.duration
    return loads


def _job_total_processing(jobs: tuple[JobSpec, ...], job_id: int) -> int:
    for job in jobs:
        if job.job_id == job_id:
            return job.total_processing_time
    raise KeyError(job_id)


def _job_due_date(jobs: tuple[JobSpec, ...], job_id: int) -> int:
    for job in jobs:
        if job.job_id == job_id:
            return job.due_date
    raise KeyError(job_id)


def _heuristic_by_name(results: tuple[HeuristicResult, ...], name: str) -> HeuristicResult:
    for result in results:
        if result.name == name:
            return result
    raise KeyError(name)


def _detect_job_clusters_via_modularity(jobs: tuple[JobSpec, ...]) -> list[set[int]]:
    job_ids = [job.job_id for job in jobs]
    machine_to_jobs: dict[str, list[int]] = {}
    for job in jobs:
        for op in job.operations:
            machine_to_jobs.setdefault(op.machine_name, []).append(job.job_id)

    adjacency: dict[int, dict[int, float]] = {job_id: {} for job_id in job_ids}
    for shared_jobs in machine_to_jobs.values():
        unique_jobs = sorted(set(shared_jobs))
        degree = len(unique_jobs)
        if degree < 2:
            continue
        edge_weight = 1.0 / float(degree - 1)
        for index, left in enumerate(unique_jobs):
            for right in unique_jobs[index + 1 :]:
                adjacency[left][right] = adjacency[left].get(right, 0.0) + edge_weight
                adjacency[right][left] = adjacency[right].get(left, 0.0) + edge_weight

    partition = [{job_id} for job_id in job_ids]
    while len(partition) > 4:
        best_partition = None
        best_score = None
        for left_index in range(len(partition)):
            for right_index in range(left_index + 1, len(partition)):
                merged = partition[left_index] | partition[right_index]
                candidate_partition = [
                    cluster
                    for index, cluster in enumerate(partition)
                    if index not in (left_index, right_index)
                ]
                candidate_partition.append(merged)
                score = _weighted_modularity(candidate_partition, adjacency, job_ids)
                if best_score is None or score > best_score:
                    best_score = score
                    best_partition = candidate_partition
        if best_partition is None:
            break
        partition = best_partition
    return partition


def _weighted_modularity(
    partition: list[set[int]],
    adjacency: dict[int, dict[int, float]],
    job_ids: list[int],
) -> float:
    degrees = {job_id: sum(adjacency[job_id].values()) for job_id in job_ids}
    total_weight = sum(degrees.values()) / 2.0
    if total_weight <= 0.0:
        return 0.0

    score = 0.0
    for cluster in partition:
        for left in cluster:
            for right in cluster:
                a_ij = adjacency[left].get(right, 0.0)
                score += a_ij - (degrees[left] * degrees[right]) / (2.0 * total_weight)
    return score / (2.0 * total_weight)
