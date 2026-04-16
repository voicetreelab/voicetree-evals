from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class FlowshopJob:
    job_id: int
    prep_minutes: int
    finish_minutes: int


@dataclass(frozen=True)
class FlowshopInstance:
    seed: int
    jobs: tuple[FlowshopJob, ...]
    baseline_order: tuple[int, ...]
    baseline_makespan: int
    gold_order: tuple[int, ...]
    gold_makespan: int

    @property
    def n_jobs(self) -> int:
        return len(self.jobs)

    def jobs_by_id(self) -> dict[int, FlowshopJob]:
        return {job.job_id: job for job in self.jobs}


def build_instance(seed: int, n_jobs: int = 12, duration_low: int = 1, duration_high: int = 20) -> FlowshopInstance:
    rng = Random(seed)
    jobs = tuple(
        FlowshopJob(
            job_id=index,
            prep_minutes=rng.randint(duration_low, duration_high),
            finish_minutes=rng.randint(duration_low, duration_high),
        )
        for index in range(1, n_jobs + 1)
    )
    baseline_order = tuple(range(1, n_jobs + 1))
    baseline_makespan = flowshop_makespan(jobs, baseline_order)
    gold_order = tuple(johnsons_rule(jobs))
    gold_makespan = flowshop_makespan(jobs, gold_order)
    return FlowshopInstance(
        seed=seed,
        jobs=jobs,
        baseline_order=baseline_order,
        baseline_makespan=baseline_makespan,
        gold_order=gold_order,
        gold_makespan=gold_makespan,
    )


def flowshop_makespan(
    jobs: tuple[FlowshopJob, ...] | list[FlowshopJob],
    order: tuple[int, ...] | list[int],
) -> int:
    if not order:
        raise ValueError("order must not be empty")

    jobs_by_id = {job.job_id: job for job in jobs}
    finish_a = 0
    finish_b = 0
    for job_id in order:
        try:
            job = jobs_by_id[job_id]
        except KeyError as exc:
            raise ValueError(f"unknown job id: {job_id}") from exc
        finish_a += job.prep_minutes
        finish_b = max(finish_b, finish_a) + job.finish_minutes
    return finish_b


def johnsons_rule(jobs: tuple[FlowshopJob, ...] | list[FlowshopJob]) -> list[int]:
    left = sorted(
        (job for job in jobs if job.prep_minutes <= job.finish_minutes),
        key=lambda job: (job.prep_minutes, job.finish_minutes, job.job_id),
    )
    right = sorted(
        (job for job in jobs if job.prep_minutes > job.finish_minutes),
        key=lambda job: (-job.finish_minutes, job.prep_minutes, job.job_id),
    )
    return [job.job_id for job in left] + [job.job_id for job in right]
