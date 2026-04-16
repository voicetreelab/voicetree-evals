from __future__ import annotations

from jobshop_spike.jobshop_instance import FlowshopInstance


def render_problem(instance: FlowshopInstance) -> str:
    order_lines = "\n".join(
        f"Order #{job.job_id} needs {job.prep_minutes} minutes in Department A and {job.finish_minutes} minutes in Department B."
        for job in instance.jobs
    )
    baseline_order = ", ".join(f"#{job_id}" for job_id in instance.baseline_order)
    return f"""You run a small manufacturing shop with {instance.n_jobs} orders to complete today.
Every order must go through Department A first and then Department B.
Each department can handle only one order at a time, and once you pick an order sequence that same sequence is used for both departments.
Your goal is to minimize the total completion time, meaning the minutes from starting the first order in Department A until the last order finishes in Department B.

Here are the orders for today:
{order_lines}

A clerk already drafted the arrival-order sequence {baseline_order}.
If you follow that baseline sequence, the shop finishes in {instance.baseline_makespan} minutes.
Try to find a sequence that finishes faster.

Job numbers run from 1 to {instance.n_jobs}.
When you emit BEST_GUESS, give a full order sequence using every job exactly once, for example:
BEST_GUESS: 2, 5, 1, 7, ...
"""
