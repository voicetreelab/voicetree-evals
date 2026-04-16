from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Any

from ortools.sat.python import cp_model

MACHINE_NAMES = ("Saw", "Mill", "Drill", "Heat", "Paint", "Inspect")
DEFAULT_N_JOBS = 5
DEFAULT_N_MACHINES = 6
GOLD_SOLVE_LIMIT_S = 30.0


@dataclass(frozen=True)
class Operation:
    machine_idx: int
    machine_name: str
    duration_minutes: int


@dataclass(frozen=True)
class Job:
    job_id: int
    operations: tuple[Operation, ...]


@dataclass(frozen=True)
class ScheduledOperation:
    machine_name: str
    job_id: int
    op_index: int
    start: int
    end: int


@dataclass(frozen=True)
class ScheduleResult:
    makespan: int
    machine_sequences: dict[str, tuple[int, ...]]
    machine_timelines: dict[str, tuple[ScheduledOperation, ...]]


@dataclass(frozen=True)
class ExactSolveResult:
    makespan: int
    schedule: ScheduleResult
    wall_seconds: float


@dataclass(frozen=True)
class JobshopInstance:
    requested_seed: int
    source_seed: int
    jobs: tuple[Job, ...]
    baseline_priorities: dict[str, tuple[int, ...]]
    baseline_makespan: int
    gold_makespan: int
    gold_schedule: ScheduleResult
    baseline_gap_pct: float
    gold_wall_seconds: float

    @property
    def n_jobs(self) -> int:
        return len(self.jobs)

    @property
    def machine_names(self) -> tuple[str, ...]:
        return MACHINE_NAMES

    def jobs_by_id(self) -> dict[int, Job]:
        return {job.job_id: job for job in self.jobs}


def build_instance(
    requested_seed: int,
    *,
    target_baseline_gap_pct: float = 10.0,
    min_baseline_gap_pct: float = 5.0,
    max_tries: int = 200,
) -> JobshopInstance:
    best_instance: JobshopInstance | None = None

    for offset in range(max_tries):
        source_seed = requested_seed * 1000 + offset
        jobs = generate_candidate_jobs(source_seed)
        gold = solve_exact(jobs, time_limit_s=GOLD_SOLVE_LIMIT_S)
        if gold is None:
            continue

        baseline_priorities = baseline_priority_queues(len(jobs))
        baseline_schedule = schedule_from_priorities(jobs, baseline_priorities)
        baseline_gap_pct = 100.0 * (baseline_schedule.makespan - gold.makespan) / gold.makespan

        instance = JobshopInstance(
            requested_seed=requested_seed,
            source_seed=source_seed,
            jobs=jobs,
            baseline_priorities=baseline_priorities,
            baseline_makespan=baseline_schedule.makespan,
            gold_makespan=gold.makespan,
            gold_schedule=gold.schedule,
            baseline_gap_pct=baseline_gap_pct,
            gold_wall_seconds=gold.wall_seconds,
        )
        if best_instance is None or instance.baseline_gap_pct > best_instance.baseline_gap_pct:
            best_instance = instance
        if baseline_gap_pct >= target_baseline_gap_pct:
            return instance

    if best_instance is None:
        raise RuntimeError("failed to generate any exact-solvable 5x6 job-shop instance")
    if best_instance.baseline_gap_pct < min_baseline_gap_pct:
        raise RuntimeError(
            f"failed to find a materially suboptimal baseline: best gap={best_instance.baseline_gap_pct:.2f}%"
        )
    return best_instance


def generate_candidate_jobs(
    seed: int,
    *,
    n_jobs: int = DEFAULT_N_JOBS,
    n_machines: int = DEFAULT_N_MACHINES,
) -> tuple[Job, ...]:
    rng = Random(seed)
    bottlenecks = set(rng.sample(range(n_machines), k=2))
    bottleneck_bonus = {machine_idx: rng.randint(3, 6) for machine_idx in bottlenecks}
    jobs: list[Job] = []

    for job_id in range(1, n_jobs + 1):
        route = list(range(n_machines))
        rng.shuffle(route)
        operations: list[Operation] = []
        for machine_idx in route:
            duration = rng.randint(1, 8) + bottleneck_bonus.get(machine_idx, 0)
            operations.append(
                Operation(
                    machine_idx=machine_idx,
                    machine_name=MACHINE_NAMES[machine_idx],
                    duration_minutes=duration,
                )
            )
        jobs.append(Job(job_id=job_id, operations=tuple(operations)))
    return tuple(jobs)


def baseline_priority_queues(n_jobs: int) -> dict[str, tuple[int, ...]]:
    base = tuple(range(1, n_jobs + 1))
    return {machine_name: base for machine_name in MACHINE_NAMES}


def schedule_from_priorities(
    jobs: tuple[Job, ...] | list[Job],
    priorities: dict[str, tuple[int, ...]] | dict[str, list[int]],
) -> ScheduleResult:
    jobs_by_id = {job.job_id: job for job in jobs}
    n_jobs = len(jobs_by_id)
    expected_ids = tuple(range(1, n_jobs + 1))
    rank: dict[str, dict[int, int]] = {}

    for machine_name in MACHINE_NAMES:
        queue = tuple(int(job_id) for job_id in priorities[machine_name])
        if tuple(sorted(queue)) != expected_ids:
            raise ValueError(f"invalid priority queue for {machine_name}: {queue}")
        rank[machine_name] = {job_id: index for index, job_id in enumerate(queue)}

    next_op_index = {job_id: 0 for job_id in jobs_by_id}
    job_ready_time = {job_id: 0 for job_id in jobs_by_id}
    machine_busy_until = {machine_name: 0 for machine_name in MACHINE_NAMES}
    machine_timelines: dict[str, list[ScheduledOperation]] = {machine_name: [] for machine_name in MACHINE_NAMES}
    machine_sequences: dict[str, list[int]] = {machine_name: [] for machine_name in MACHINE_NAMES}
    current_time = 0
    scheduled_count = 0
    total_ops = sum(len(job.operations) for job in jobs)

    while scheduled_count < total_ops:
        progress = False
        for machine_name in MACHINE_NAMES:
            if machine_busy_until[machine_name] > current_time:
                continue

            candidates: list[int] = []
            for job_id, job in jobs_by_id.items():
                op_index = next_op_index[job_id]
                if op_index >= len(job.operations):
                    continue
                op = job.operations[op_index]
                if op.machine_name != machine_name:
                    continue
                if job_ready_time[job_id] > current_time:
                    continue
                candidates.append(job_id)

            if not candidates:
                continue

            chosen_job_id = min(
                candidates,
                key=lambda job_id: (rank[machine_name][job_id], job_ready_time[job_id], job_id),
            )
            chosen_job = jobs_by_id[chosen_job_id]
            chosen_op_index = next_op_index[chosen_job_id]
            chosen_op = chosen_job.operations[chosen_op_index]
            start = current_time
            end = start + chosen_op.duration_minutes

            machine_busy_until[machine_name] = end
            job_ready_time[chosen_job_id] = end
            next_op_index[chosen_job_id] += 1
            scheduled_count += 1
            progress = True

            machine_timelines[machine_name].append(
                ScheduledOperation(
                    machine_name=machine_name,
                    job_id=chosen_job_id,
                    op_index=chosen_op_index,
                    start=start,
                    end=end,
                )
            )
            machine_sequences[machine_name].append(chosen_job_id)

        if scheduled_count >= total_ops:
            break
        if progress:
            continue

        future_times = [busy_until for busy_until in machine_busy_until.values() if busy_until > current_time]
        if not future_times:
            raise RuntimeError("schedule generation stalled before all operations were placed")
        current_time = min(future_times)

    makespan = max((timeline[-1].end for timeline in machine_timelines.values() if timeline), default=0)
    return ScheduleResult(
        makespan=makespan,
        machine_sequences={name: tuple(seq) for name, seq in machine_sequences.items()},
        machine_timelines={name: tuple(timeline) for name, timeline in machine_timelines.items()},
    )


def solve_exact(
    jobs: tuple[Job, ...] | list[Job],
    *,
    time_limit_s: float = GOLD_SOLVE_LIMIT_S,
) -> ExactSolveResult | None:
    import time

    model = cp_model.CpModel()
    horizon = sum(op.duration_minutes for job in jobs for op in job.operations)
    task_data: dict[tuple[int, int], dict[str, Any]] = {}
    machine_to_intervals: dict[int, list[cp_model.IntervalVar]] = {machine_idx: [] for machine_idx in range(len(MACHINE_NAMES))}

    for job in jobs:
        for op_index, op in enumerate(job.operations):
            suffix = f"j{job.job_id}_o{op_index}"
            start_var = model.NewIntVar(0, horizon, f"start_{suffix}")
            end_var = model.NewIntVar(0, horizon, f"end_{suffix}")
            interval_var = model.NewIntervalVar(start_var, op.duration_minutes, end_var, f"interval_{suffix}")
            task_data[(job.job_id, op_index)] = {
                "start": start_var,
                "end": end_var,
                "interval": interval_var,
                "machine_idx": op.machine_idx,
                "machine_name": op.machine_name,
                "duration": op.duration_minutes,
            }
            machine_to_intervals[op.machine_idx].append(interval_var)

    for job in jobs:
        for op_index in range(len(job.operations) - 1):
            model.Add(task_data[(job.job_id, op_index)]["end"] <= task_data[(job.job_id, op_index + 1)]["start"])

    for machine_idx, intervals in machine_to_intervals.items():
        del machine_idx
        model.AddNoOverlap(intervals)

    makespan_var = model.NewIntVar(0, horizon, "makespan")
    model.AddMaxEquality(
        makespan_var,
        [task_data[(job.job_id, len(job.operations) - 1)]["end"] for job in jobs],
    )
    model.Minimize(makespan_var)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_s)
    solver.parameters.num_search_workers = 8
    start_time = time.monotonic()
    status = solver.Solve(model)
    wall_seconds = time.monotonic() - start_time
    if status != cp_model.OPTIMAL:
        return None

    machine_timelines: dict[str, list[ScheduledOperation]] = {machine_name: [] for machine_name in MACHINE_NAMES}
    for job in jobs:
        for op_index, op in enumerate(job.operations):
            start = solver.Value(task_data[(job.job_id, op_index)]["start"])
            end = solver.Value(task_data[(job.job_id, op_index)]["end"])
            machine_timelines[op.machine_name].append(
                ScheduledOperation(
                    machine_name=op.machine_name,
                    job_id=job.job_id,
                    op_index=op_index,
                    start=start,
                    end=end,
                )
            )

    machine_sequences: dict[str, tuple[int, ...]] = {}
    normalized_timelines: dict[str, tuple[ScheduledOperation, ...]] = {}
    for machine_name, ops in machine_timelines.items():
        ordered_ops = tuple(sorted(ops, key=lambda item: (item.start, item.end, item.job_id, item.op_index)))
        normalized_timelines[machine_name] = ordered_ops
        machine_sequences[machine_name] = tuple(op.job_id for op in ordered_ops)

    schedule = ScheduleResult(
        makespan=solver.Value(makespan_var),
        machine_sequences=machine_sequences,
        machine_timelines=normalized_timelines,
    )
    return ExactSolveResult(
        makespan=schedule.makespan,
        schedule=schedule,
        wall_seconds=wall_seconds,
    )
