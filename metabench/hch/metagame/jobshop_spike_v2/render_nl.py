from __future__ import annotations

import json

from jobshop_spike_v2.jobshop_instance import JobshopInstance, MACHINE_NAMES


def render_problem(instance: JobshopInstance) -> str:
    job_lines = []
    for job in instance.jobs:
        steps = ", then ".join(
            f"{op.machine_name} for {op.duration_minutes} minutes"
            for op in job.operations
        )
        job_lines.append(f"Product #{job.job_id} must visit {steps}.")

    baseline_rule = ", ".join(str(job_id) for job_id in range(1, instance.n_jobs + 1))
    baseline_json = json.dumps(
        {machine_name: list(instance.baseline_priorities[machine_name]) for machine_name in MACHINE_NAMES},
        sort_keys=True,
    )

    return f"""You run a custom fabrication shop with five products and six shared stations: Saw, Mill, Drill, Heat, Paint, and Inspect.
Each product has its own route through those stations, each station can work on only one product at a time, and a product cannot start its next step until its previous step is finished.
Your goal is to minimize total completion time: the minutes from the first station start until the last product leaves its final station.

Here is today's work:
{chr(10).join(job_lines)}

The floor lead's fallback policy is simple: whenever a station becomes free, it gives priority to the lowest-numbered waiting product.
Equivalently, every station uses the local priority order {baseline_rule}.
That baseline policy finishes in {instance.baseline_makespan} minutes, so that is always a valid safety-floor answer if you cannot improve it.

When you emit BEST_GUESS, give a JSON object with exactly these keys:
Saw, Mill, Drill, Heat, Paint, Inspect.
Each value must be a full permutation of product numbers 1 through 5.
Interpretation: each station follows its own local priority list and, whenever multiple products are waiting there, it takes the waiting product that appears earliest in that station's list.

Example format:
BEST_GUESS: {baseline_json}
"""
