from __future__ import annotations

from dataclasses import dataclass
from typing import Any


INFEASIBLE_GAP_PCT = 100.0
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


@dataclass(frozen=True)
class VerificationResult:
    is_feasible: bool
    verified_makespan: int | None
    verified_weighted_tardiness: int | None
    verified_objective: int | None
    failure_reason: str | None


def verify(instance: dict[str, Any], submission: dict[str, Any] | None) -> tuple[float, bool, dict[str, Any]]:
    """BEST_GUESS schema: {"machines": {"M1": [["J1", 0, 3], ...], ...}, "makespan": 42, "weighted_tardiness": 18, "objective": 858}."""
    parsed_instance = _parse_instance(instance)
    if isinstance(parsed_instance, str):
        return INFEASIBLE_GAP_PCT, False, {"failure_reason": parsed_instance}

    jobs, n_machines, gold_objective, baseline_objective = parsed_instance
    result = _verify_schedule(jobs=jobs, n_machines=n_machines, schedule=submission)
    details: dict[str, Any] = {
        "metric_name": "objective",
        "gold_objective": gold_objective,
        "baseline_objective": baseline_objective,
        "verified_makespan": result.verified_makespan,
        "verified_weighted_tardiness": result.verified_weighted_tardiness,
        "verified_objective": result.verified_objective,
        "failure_reason": result.failure_reason,
    }
    if not result.is_feasible or result.verified_objective is None:
        details["gap_pct"] = INFEASIBLE_GAP_PCT
        return INFEASIBLE_GAP_PCT, False, details

    gap_pct = 100.0 * (result.verified_objective - gold_objective) / max(1, gold_objective)
    details["gap_pct"] = gap_pct
    return gap_pct, True, details


def _parse_instance(
    instance: dict[str, Any] | Any,
) -> tuple[tuple[JobSpec, ...], int, int, int | None] | str:
    if not isinstance(instance, dict):
        return "instance must be an object"

    raw_n_machines = instance.get("n_machines")
    raw_jobs = instance.get("jobs")
    raw_gold_objective = instance.get("gold_objective")
    raw_baseline_objective = instance.get("baseline_objective")

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

    if not isinstance(raw_jobs, list) or not raw_jobs:
        return "instance.jobs must be a non-empty list"

    jobs: list[JobSpec] = []
    for raw_job in raw_jobs:
        parsed_job = _parse_job(raw_job)
        if isinstance(parsed_job, str):
            return parsed_job
        jobs.append(parsed_job)

    return tuple(jobs), n_machines, gold_objective, baseline_objective


def _parse_job(raw_job: Any) -> JobSpec | str:
    if not isinstance(raw_job, dict):
        return "each job must be an object"
    try:
        job_id = int(raw_job["job_id"])
        due_date = int(raw_job["due_date"])
        tardiness_weight = int(raw_job["tardiness_weight"])
    except Exception:
        return "job must have integer job_id, due_date, and tardiness_weight"

    raw_ops = raw_job.get("operations")
    if not isinstance(raw_ops, list) or not raw_ops:
        return f"job {job_id} operations must be a non-empty list"

    operations: list[OperationSpec] = []
    for raw_op in raw_ops:
        if not isinstance(raw_op, dict):
            return f"job {job_id} operation entries must be objects"
        machine_name = raw_op.get("machine_name")
        duration = raw_op.get("duration")
        if not isinstance(machine_name, str) or not machine_name:
            return f"job {job_id} operation machine_name must be a non-empty string"
        try:
            duration_int = int(duration)
        except Exception:
            return f"job {job_id} operation duration must be an integer"
        if duration_int <= 0:
            return f"job {job_id} operation duration must be positive"
        operations.append(OperationSpec(machine_name=machine_name, duration=duration_int))

    return JobSpec(
        job_id=job_id,
        operations=tuple(operations),
        due_date=due_date,
        tardiness_weight=tardiness_weight,
    )


def _verify_schedule(
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
