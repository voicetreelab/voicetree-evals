from __future__ import annotations

from dataclasses import dataclass
from typing import Any


INFEASIBLE_GAP_PCT = 100.0


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


def verify(instance: dict[str, Any], submission: dict[str, Any]) -> tuple[float, bool, dict[str, Any]]:
    """BEST_GUESS schema: {"factory_a": {"MA1": [["J1", 0, 3], ...]}, "factory_b": {"MB1": [["J1", 3, 5], ...]}, "makespan": 42}."""
    parsed_instance = _parse_instance(instance)
    if isinstance(parsed_instance, str):
        return INFEASIBLE_GAP_PCT, False, {"failure_reason": parsed_instance}

    jobs, n_machines, gold_objective, baseline_objective = parsed_instance
    result = _verify_schedule(
        jobs=jobs,
        n_machines=n_machines,
        schedule=submission,
    )
    details = {
        "metric_name": "makespan",
        "gold_objective": gold_objective,
        "baseline_objective": baseline_objective,
        "verified_makespan": result.verified_makespan,
        "verified_objective": result.verified_makespan,
        "failure_reason": result.failure_reason,
    }
    if not result.is_feasible or result.verified_makespan is None:
        details["gap_pct"] = INFEASIBLE_GAP_PCT
        return INFEASIBLE_GAP_PCT, False, details

    gap_pct = 100.0 * (result.verified_makespan - gold_objective) / gold_objective
    details["gap_pct"] = gap_pct
    return gap_pct, True, details


def _parse_instance(
    instance: dict[str, Any] | Any,
) -> tuple[tuple[JobSpec, ...], int, int, int | None] | str:
    if not isinstance(instance, dict):
        return "instance must be an object"

    raw_n_machines = instance.get("n_machines")
    raw_jobs = instance.get("jobs")
    raw_gold_objective = instance.get("gold_objective", instance.get("gold_makespan"))
    raw_baseline_objective = instance.get("baseline_objective", instance.get("baseline_makespan"))

    try:
        n_machines = int(raw_n_machines)
    except Exception:
        return "instance.n_machines must be an integer"
    if n_machines <= 0:
        return "instance.n_machines must be positive"

    try:
        gold_objective = int(raw_gold_objective)
    except Exception:
        return "instance.gold_objective must be an integer"
    if gold_objective <= 0:
        return "instance.gold_objective must be positive"

    baseline_objective = None
    if raw_baseline_objective is not None:
        try:
            baseline_objective = int(raw_baseline_objective)
        except Exception:
            return "instance.baseline_objective must be an integer when present"

    if not isinstance(raw_jobs, list):
        return "instance.jobs must be a list"

    jobs: list[JobSpec] = []
    for raw_job in raw_jobs:
        parsed_job = _parse_job(raw_job)
        if isinstance(parsed_job, str):
            return parsed_job
        jobs.append(parsed_job)
    if not jobs:
        return "instance.jobs must not be empty"

    return tuple(jobs), n_machines, gold_objective, baseline_objective


def _parse_job(raw_job: Any) -> JobSpec | str:
    if not isinstance(raw_job, dict):
        return "each job must be an object"

    try:
        job_id = int(raw_job["job_id"])
    except Exception:
        return "job.job_id must be an integer"

    parsed_a = _parse_route(raw_job.get("factory_a"), factory_key="factory_a", job_id=job_id)
    if isinstance(parsed_a, str):
        return parsed_a
    parsed_b = _parse_route(raw_job.get("factory_b"), factory_key="factory_b", job_id=job_id)
    if isinstance(parsed_b, str):
        return parsed_b

    return JobSpec(job_id=job_id, factory_a=parsed_a, factory_b=parsed_b)


def _parse_route(raw_route: Any, *, factory_key: str, job_id: int) -> tuple[OperationSpec, ...] | str:
    if not isinstance(raw_route, list):
        return f"job {job_id} {factory_key} must be a list"
    operations: list[OperationSpec] = []
    for raw_op in raw_route:
        if not isinstance(raw_op, dict):
            return f"job {job_id} {factory_key} entries must be objects"
        machine_name = raw_op.get("machine_name")
        duration = raw_op.get("duration")
        if not isinstance(machine_name, str) or not machine_name:
            return f"job {job_id} {factory_key} machine_name must be a non-empty string"
        try:
            duration_int = int(duration)
        except Exception:
            return f"job {job_id} {factory_key} duration must be an integer"
        if duration_int <= 0:
            return f"job {job_id} {factory_key} duration must be positive"
        operations.append(OperationSpec(machine_name=machine_name, duration=duration_int))
    if not operations:
        return f"job {job_id} {factory_key} must not be empty"
    return tuple(operations)


def _verify_schedule(
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
    start_b: dict[int, dict[str, int]] = {job.job_id: {} for job in jobs}
    completion_b: dict[int, dict[str, int]] = {job.job_id: {} for job in jobs}
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
            key = (job_id, machine_name)
            if key in seen_ops_a:
                return VerificationResult(False, None, f"duplicate operation for J{job_id} on {machine_name}")
            seen_ops_a.add(key)
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
            key = (job_id, machine_name)
            if key in seen_ops_b:
                return VerificationResult(False, None, f"duplicate operation for J{job_id} on {machine_name}")
            seen_ops_b.add(key)
            start_b[job_id][machine_name] = start
            completion_b[job_id][machine_name] = end
            max_end = max(max_end, end)

    for job in jobs:
        expected_a = {(job.job_id, op.machine_name) for op in job.factory_a}
        expected_b = {(job.job_id, op.machine_name) for op in job.factory_b}
        if len(seen_ops_a.intersection(expected_a)) != len(job.factory_a):
            return VerificationResult(False, None, f"missing factory A operations for J{job.job_id}")
        if len(seen_ops_b.intersection(expected_b)) != len(job.factory_b):
            return VerificationResult(False, None, f"missing factory B operations for J{job.job_id}")

        reason = _check_route_precedence(job.factory_a, start_a[job.job_id], completion_a[job.job_id])
        if reason:
            return VerificationResult(False, None, f"factory A precedence failed for J{job.job_id}: {reason}")
        reason = _check_route_precedence(job.factory_b, start_b[job.job_id], completion_b[job.job_id])
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
        machine_name = op.machine_name
        if machine_name not in start_lookup or machine_name not in completion_lookup:
            return f"missing timing for {machine_name}"
        current_start = start_lookup[machine_name]
        current_end = completion_lookup[machine_name]
        if previous_end is not None and current_start < previous_end:
            return f"{machine_name} starts at {current_start} before predecessor finished at {previous_end}"
        previous_end = current_end
    return None
