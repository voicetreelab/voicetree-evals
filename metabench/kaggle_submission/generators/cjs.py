from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any

try:
    from ortools.sat.python import cp_model
except ImportError:  # pragma: no cover - exercised in dependency-blocked environments
    cp_model = None


DIFFICULTY_CONFIGS = {
    "medium": {
        "n_jobs": 5,
        "n_machines": 6,
        "min_baseline_gap_pct": 15.0,
    },
    "hard": {
        "n_jobs": 6,
        "n_machines": 7,
        "min_baseline_gap_pct": 15.0,
    },
}


def _require_ortools() -> Any:
    if cp_model is None:
        raise RuntimeError(
            "ortools is not installed. Install the kaggle_submission dependencies before generating CJS instances."
        )
    return cp_model


@dataclass(frozen=True)
class OperationSpec:
    machine_name: str
    duration: int


@dataclass(frozen=True)
class JobSpec:
    job_id: int
    factory_a: tuple[OperationSpec, ...]
    factory_b: tuple[OperationSpec, ...]


@dataclass(frozen=True)
class VerificationResult:
    is_feasible: bool
    verified_makespan: int | None
    failure_reason: str | None


@dataclass(frozen=True)
class CoupledJobShopInstance:
    seed: int
    n_jobs: int
    n_machines: int
    jobs: tuple[JobSpec, ...]
    baseline_schedule: dict[str, Any]
    baseline_makespan: int
    optimal_schedule: dict[str, Any]
    optimal_makespan: int
    problem_statement: str


def generate(seed: int, difficulty: str) -> dict[str, Any]:
    config = DIFFICULTY_CONFIGS.get(difficulty)
    if config is None:
        supported = ", ".join(sorted(DIFFICULTY_CONFIGS))
        raise ValueError(f"unsupported cjs difficulty {difficulty!r}; expected one of: {supported}")

    instance = build_instance(
        seed=seed,
        n_jobs=config["n_jobs"],
        n_machines=config["n_machines"],
        min_baseline_gap_pct=config["min_baseline_gap_pct"],
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
        "jobs": [_job_to_dict(job) for job in instance.jobs],
        "baseline_submission": instance.baseline_schedule,
        "gold_submission": instance.optimal_schedule,
        "baseline_objective": baseline_objective,
        "gold_objective": gold_objective,
        "baseline_gap_pct": baseline_gap_pct,
        "problem_statement": instance.problem_statement,
    }


def build_instance(
    seed: int,
    n_jobs: int,
    n_machines: int,
    duration_low: int = 1,
    duration_high: int = 9,
    min_baseline_gap_pct: float | None = 15.0,
    max_generation_attempts: int = 20,
) -> CoupledJobShopInstance:
    last_gap_pct = None
    for attempt in range(max_generation_attempts):
        attempt_seed = seed if attempt == 0 else seed * 10_000 + attempt
        rng = Random(attempt_seed)
        jobs = _build_jobs(
            rng,
            n_jobs=n_jobs,
            n_machines=n_machines,
            duration_low=duration_low,
            duration_high=duration_high,
        )
        baseline_schedule = build_baseline_schedule(jobs)
        baseline_check = verify_schedule(
            jobs=jobs,
            n_machines=n_machines,
            schedule=baseline_schedule,
        )
        if not baseline_check.is_feasible or baseline_check.verified_makespan is None:
            raise RuntimeError(f"internal error: baseline schedule is infeasible: {baseline_check.failure_reason}")

        optimal_schedule, optimal_makespan = solve_exact_schedule(jobs=jobs, n_machines=n_machines)
        last_gap_pct = 100.0 * (baseline_check.verified_makespan - optimal_makespan) / optimal_makespan
        if min_baseline_gap_pct is not None and last_gap_pct < min_baseline_gap_pct:
            continue

        instance_stub = CoupledJobShopInstance(
            seed=seed,
            n_jobs=n_jobs,
            n_machines=n_machines,
            jobs=jobs,
            baseline_schedule=baseline_schedule,
            baseline_makespan=baseline_check.verified_makespan,
            optimal_schedule=optimal_schedule,
            optimal_makespan=optimal_makespan,
            problem_statement="",
        )
        problem_statement = render_problem(instance_stub)
        return CoupledJobShopInstance(
            seed=seed,
            n_jobs=n_jobs,
            n_machines=n_machines,
            jobs=jobs,
            baseline_schedule=baseline_schedule,
            baseline_makespan=baseline_check.verified_makespan,
            optimal_schedule=optimal_schedule,
            optimal_makespan=optimal_makespan,
            problem_statement=problem_statement,
        )

    raise RuntimeError(
        "failed to generate coupled job-shop instance meeting minimum baseline gap "
        f"{min_baseline_gap_pct} after {max_generation_attempts} attempts; last gap was {last_gap_pct}"
    )


def _build_jobs(
    rng: Random,
    *,
    n_jobs: int,
    n_machines: int,
    duration_low: int,
    duration_high: int,
) -> tuple[JobSpec, ...]:
    factory_a_machines = [f"MA{index}" for index in range(1, n_machines + 1)]
    factory_b_machines = [f"MB{index}" for index in range(1, n_machines + 1)]
    jobs: list[JobSpec] = []
    seen_a: set[tuple[str, ...]] = set()
    seen_b: set[tuple[str, ...]] = set()

    for job_id in range(1, n_jobs + 1):
        route_a = _draw_route(rng, factory_a_machines, seen_a)
        route_b = _draw_route(rng, factory_b_machines, seen_b)
        jobs.append(
            JobSpec(
                job_id=job_id,
                factory_a=tuple(
                    OperationSpec(machine_name=machine_name, duration=rng.randint(duration_low, duration_high))
                    for machine_name in route_a
                ),
                factory_b=tuple(
                    OperationSpec(machine_name=machine_name, duration=rng.randint(duration_low, duration_high))
                    for machine_name in route_b
                ),
            )
        )

    return tuple(jobs)


def _draw_route(rng: Random, machines: list[str], seen: set[tuple[str, ...]]) -> tuple[str, ...]:
    for _ in range(20):
        route = tuple(rng.sample(machines, len(machines)))
        if route not in seen or len(seen) >= max(1, len(machines) - 1):
            seen.add(route)
            return route
    route = tuple(machines)
    seen.add(route)
    return route


def build_baseline_schedule(jobs: tuple[JobSpec, ...]) -> dict[str, Any]:
    machine_schedule_a, completion_a = _serial_schedule_factory(
        jobs=jobs,
        factory="A",
        job_order=[job.job_id for job in jobs],
        release_times={job.job_id: 0 for job in jobs},
    )
    job_order_b = sorted(completion_a, key=lambda job_id: (completion_a[job_id], job_id))
    machine_schedule_b, completion_b = _serial_schedule_factory(
        jobs=jobs,
        factory="B",
        job_order=job_order_b,
        release_times=completion_a,
    )
    makespan = max(completion_b.values(), default=0)
    return {
        "factory_a": machine_schedule_a,
        "factory_b": machine_schedule_b,
        "makespan": makespan,
    }


def _serial_schedule_factory(
    *,
    jobs: tuple[JobSpec, ...],
    factory: str,
    job_order: list[int],
    release_times: dict[int, int],
) -> tuple[dict[str, list[list[Any]]], dict[int, int]]:
    machine_available: dict[str, int] = {}
    machine_schedule: dict[str, list[list[Any]]] = {}
    jobs_by_id = {job.job_id: job for job in jobs}
    job_completion: dict[int, int] = {}

    for job_id in job_order:
        job = jobs_by_id[job_id]
        route = job.factory_a if factory == "A" else job.factory_b
        current_time = release_times.get(job_id, 0)
        for op in route:
            start = max(current_time, machine_available.get(op.machine_name, 0))
            end = start + op.duration
            machine_schedule.setdefault(op.machine_name, []).append([f"J{job_id}", start, end])
            machine_available[op.machine_name] = end
            current_time = end
        job_completion[job_id] = current_time

    for machine_name in sorted(machine_schedule):
        machine_schedule[machine_name].sort(key=lambda item: (item[1], item[2], item[0]))
    return machine_schedule, job_completion


def solve_exact_schedule(jobs: tuple[JobSpec, ...], n_machines: int) -> tuple[dict[str, Any], int]:
    cp = _require_ortools()
    model = cp.CpModel()
    horizon = sum(op.duration for job in jobs for op in job.factory_a + job.factory_b)
    op_vars: dict[tuple[str, int, int], tuple[Any, Any, Any]] = {}
    machine_to_intervals: dict[str, list[Any]] = {}
    last_end_a: dict[int, Any] = {}
    last_end_b: dict[int, Any] = {}

    for job in jobs:
        for factory_name, route in (("A", job.factory_a), ("B", job.factory_b)):
            previous_end = None
            for step_index, op in enumerate(route):
                start = model.NewIntVar(0, horizon, f"{factory_name}_J{job.job_id}_S{step_index}_start")
                end = model.NewIntVar(0, horizon, f"{factory_name}_J{job.job_id}_S{step_index}_end")
                interval = model.NewIntervalVar(
                    start,
                    op.duration,
                    end,
                    f"{factory_name}_J{job.job_id}_S{step_index}_interval",
                )
                op_vars[(factory_name, job.job_id, step_index)] = (start, end, interval)
                machine_to_intervals.setdefault(op.machine_name, []).append(interval)
                if previous_end is not None:
                    model.Add(start >= previous_end)
                previous_end = end
            if previous_end is not None:
                if factory_name == "A":
                    last_end_a[job.job_id] = previous_end
                else:
                    last_end_b[job.job_id] = previous_end

        model.Add(op_vars[("B", job.job_id, 0)][0] >= last_end_a[job.job_id])

    for intervals in machine_to_intervals.values():
        model.AddNoOverlap(intervals)

    makespan = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(makespan, list(last_end_b.values()))
    model.Minimize(makespan)

    solver = cp.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    status = solver.Solve(model)
    if status != cp.OPTIMAL:
        status_name = solver.StatusName(status)
        raise RuntimeError(f"failed to obtain exact optimum for coupled job-shop instance: {status_name}")

    machine_schedule_a: dict[str, list[list[Any]]] = {f"MA{idx}": [] for idx in range(1, n_machines + 1)}
    machine_schedule_b: dict[str, list[list[Any]]] = {f"MB{idx}": [] for idx in range(1, n_machines + 1)}
    for job in jobs:
        for factory_name, route in (("A", job.factory_a), ("B", job.factory_b)):
            for step_index, op in enumerate(route):
                start, end, _ = op_vars[(factory_name, job.job_id, step_index)]
                target = machine_schedule_a if factory_name == "A" else machine_schedule_b
                target[op.machine_name].append([f"J{job.job_id}", solver.Value(start), solver.Value(end)])

    for schedule in (machine_schedule_a, machine_schedule_b):
        for machine_name in schedule:
            schedule[machine_name].sort(key=lambda item: (item[1], item[2], item[0]))

    return {
        "factory_a": machine_schedule_a,
        "factory_b": machine_schedule_b,
        "makespan": solver.Value(makespan),
    }, solver.Value(makespan)


def verify_schedule(
    *,
    jobs: tuple[JobSpec, ...],
    n_machines: int,
    schedule: dict[str, Any] | None,
) -> VerificationResult:
    if not isinstance(schedule, dict):
        return VerificationResult(False, None, "schedule must be an object")

    try:
        factory_a = schedule["factory_a"]
        factory_b = schedule["factory_b"]
        claimed_makespan = int(schedule["makespan"])
    except Exception:
        return VerificationResult(False, None, "schedule must contain factory_a, factory_b, makespan")

    expected_a = {f"MA{index}" for index in range(1, n_machines + 1)}
    expected_b = {f"MB{index}" for index in range(1, n_machines + 1)}
    if not isinstance(factory_a, dict) or not isinstance(factory_b, dict):
        return VerificationResult(False, None, "factory schedules must be objects")

    parsed_a = _parse_factory_schedule(factory_a, expected_a)
    if isinstance(parsed_a, str):
        return VerificationResult(False, None, parsed_a)
    parsed_b = _parse_factory_schedule(factory_b, expected_b)
    if isinstance(parsed_b, str):
        return VerificationResult(False, None, parsed_b)

    jobs_by_id = {job.job_id: job for job in jobs}
    seen_ops_a: set[tuple[int, str]] = set()
    seen_ops_b: set[tuple[int, str]] = set()
    start_a: dict[int, dict[str, int]] = {job.job_id: {} for job in jobs}
    completion_a: dict[int, dict[str, int]] = {job.job_id: {} for job in jobs}
    completion_b: dict[int, dict[str, int]] = {job.job_id: {} for job in jobs}
    start_b: dict[int, dict[str, int]] = {job.job_id: {} for job in jobs}
    max_end = 0

    for machine_name, entries in parsed_a.items():
        reason = _check_machine_conflicts(entries)
        if reason:
            return VerificationResult(False, None, reason)
        for job_id, start, end in entries:
            job = jobs_by_id.get(job_id)
            if job is None:
                return VerificationResult(False, None, f"unknown job J{job_id} in {machine_name}")
            duration = _duration_for_machine(job.factory_a, machine_name)
            if duration is None:
                return VerificationResult(False, None, f"job J{job_id} does not use machine {machine_name} in factory A")
            if end - start != duration:
                return VerificationResult(
                    False,
                    None,
                    f"duration mismatch for J{job_id} on {machine_name}: expected {duration}, got {end - start}",
                )
            op_key = (job_id, machine_name)
            if op_key in seen_ops_a:
                return VerificationResult(False, None, f"duplicate operation for J{job_id} on {machine_name}")
            seen_ops_a.add(op_key)
            start_a[job_id][machine_name] = start
            completion_a[job_id][machine_name] = end
            max_end = max(max_end, end)

    for machine_name, entries in parsed_b.items():
        reason = _check_machine_conflicts(entries)
        if reason:
            return VerificationResult(False, None, reason)
        for job_id, start, end in entries:
            job = jobs_by_id.get(job_id)
            if job is None:
                return VerificationResult(False, None, f"unknown job J{job_id} in {machine_name}")
            duration = _duration_for_machine(job.factory_b, machine_name)
            if duration is None:
                return VerificationResult(False, None, f"job J{job_id} does not use machine {machine_name} in factory B")
            if end - start != duration:
                return VerificationResult(
                    False,
                    None,
                    f"duration mismatch for J{job_id} on {machine_name}: expected {duration}, got {end - start}",
                )
            op_key = (job_id, machine_name)
            if op_key in seen_ops_b:
                return VerificationResult(False, None, f"duplicate operation for J{job_id} on {machine_name}")
            seen_ops_b.add(op_key)
            completion_b[job_id][machine_name] = end
            start_b[job_id][machine_name] = start
            max_end = max(max_end, end)

    for job in jobs:
        if len(seen_ops_a.intersection({(job.job_id, op.machine_name) for op in job.factory_a})) != len(job.factory_a):
            return VerificationResult(False, None, f"missing factory A operations for J{job.job_id}")
        if len(seen_ops_b.intersection({(job.job_id, op.machine_name) for op in job.factory_b})) != len(job.factory_b):
            return VerificationResult(False, None, f"missing factory B operations for J{job.job_id}")

        reason = _check_route_precedence(
            job.factory_a,
            start_a[job.job_id],
            completion_a[job.job_id],
        )
        if reason:
            return VerificationResult(False, None, f"factory A precedence failed for J{job.job_id}: {reason}")
        reason = _check_route_precedence(
            job.factory_b,
            start_b[job.job_id],
            completion_b[job.job_id],
        )
        if reason:
            return VerificationResult(False, None, f"factory B precedence failed for J{job.job_id}: {reason}")

        last_a_machine = job.factory_a[-1].machine_name
        first_b_machine = job.factory_b[0].machine_name
        if start_b[job.job_id][first_b_machine] < completion_a[job.job_id][last_a_machine]:
            return VerificationResult(False, None, f"coupling violation for J{job.job_id}")

    if claimed_makespan != max_end:
        return VerificationResult(False, None, f"claimed makespan {claimed_makespan} does not match verified {max_end}")

    return VerificationResult(True, max_end, None)


def _parse_factory_schedule(
    factory_schedule: dict[str, Any],
    expected_machines: set[str],
) -> dict[str, list[tuple[int, int, int]]] | str:
    parsed: dict[str, list[tuple[int, int, int]]] = {}
    for machine_name in expected_machines:
        entries = factory_schedule.get(machine_name, [])
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
        parsed[machine_name] = sorted(machine_entries, key=lambda item: (item[1], item[2], item[0]))
    unknown = set(factory_schedule) - expected_machines
    if unknown:
        return f"unknown machines in schedule: {sorted(unknown)}"
    return parsed


def _check_machine_conflicts(entries: list[tuple[int, int, int]]) -> str | None:
    for index in range(1, len(entries)):
        prev = entries[index - 1]
        current = entries[index]
        if current[1] < prev[2]:
            return f"machine overlap between J{prev[0]} and J{current[0]}"
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
        machine_name = op.machine_name
        if machine_name not in start_lookup or machine_name not in completion_lookup:
            return f"missing timing for {machine_name}"
        current_start = start_lookup[machine_name]
        current_end = completion_lookup[machine_name]
        if previous_end is not None and current_start < previous_end:
            return f"{machine_name} starts at {current_start} before predecessor finished at {previous_end}"
        previous_end = current_end
    return None


def schedule_summary(schedule: dict[str, Any]) -> str:
    parts: list[str] = []
    for factory_key, title in (("factory_a", "Factory A"), ("factory_b", "Factory B")):
        lines = []
        for machine_name in sorted(schedule.get(factory_key, {})):
            entries = ",".join(
                f"{job}[{start}-{end}]"
                for job, start, end in schedule[factory_key][machine_name]
            )
            lines.append(f"{machine_name}: {entries}")
        parts.append(f"{title}: " + "; ".join(lines))
    parts.append(f"Makespan: {schedule.get('makespan')}")
    return "\n".join(parts)


def render_problem(instance: CoupledJobShopInstance) -> str:
    baseline_summary = schedule_summary(instance.baseline_schedule)
    job_lines: list[str] = []
    for job in instance.jobs:
        a_route = " -> ".join(f"{op.machine_name} ({op.duration})" for op in job.factory_a)
        b_route = " -> ".join(f"{op.machine_name} ({op.duration})" for op in job.factory_b)
        job_lines.append(f"- Job {job.job_id}: Factory A {a_route}; Factory B {b_route}")
    return f"""You run a two-factory manufacturing pipeline. Factory A makes components, then Factory B finishes the same jobs.
Each factory is its own job shop with one-job-per-machine exclusivity and no preemption.
Every job must finish all of its Factory A operations before that same job may start any Factory B operation.
Your objective is to minimize the coupled makespan: the time when the final Factory B operation finishes.

Instance size: {instance.n_jobs} jobs, {instance.n_machines} machines in each factory.
Jobs and ordered operations:
{chr(10).join(job_lines)}

Constraints:
- A machine handles at most one job at a time.
- Each job must respect its listed operation order inside each factory.
- Factory B job Jx cannot start until Factory A job Jx has fully completed.
- When you emit a schedule, every required operation must appear exactly once.

A deterministic feasible baseline schedule is provided below. If you stop immediately or fail to produce a valid schedule, this baseline is what gets scored.
Baseline makespan: {instance.baseline_makespan}
Baseline schedule summary:
{baseline_summary}
"""


def _job_to_dict(job: JobSpec) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "factory_a": [_operation_to_dict(op) for op in job.factory_a],
        "factory_b": [_operation_to_dict(op) for op in job.factory_b],
    }


def _operation_to_dict(operation: OperationSpec) -> dict[str, Any]:
    return {
        "machine_name": operation.machine_name,
        "duration": operation.duration,
    }
