"""BEST_GUESS JSON schema:
{
  "p_query_given_evidence": <float strictly between 0 and 1>,
  "ordering_used": ["X1", "X2", "..."],  # every eliminable variable exactly once
  "peak_factor_size_self_report": <positive int>
}
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
import math
from random import Random
from typing import Any, Iterable, Sequence

RANDOM_ORDER_SAMPLES = 1000
DEFAULT_VARIABLE_SIZES = (22, 26, 28)
DIFFICULTY_TO_VARIABLES = {
    "medium": 22,
    "hard": 26,
}
FAILURE_GAP_PCT = 100.0
MIN_POSITIVE = 1e-12


@dataclass(frozen=True)
class VariableSpec:
    name: str
    parents: tuple[str, ...]
    cpt_true_probs: tuple[float, ...]


@dataclass(frozen=True)
class Factor:
    scope: tuple[str, ...]
    values: tuple[float, ...]


@dataclass(frozen=True)
class OrderingSummary:
    name: str
    ordering: tuple[str, ...]
    peak_factor_size: int


@dataclass(frozen=True)
class GuessVerification:
    is_valid: bool
    failure_reason: str | None
    p_query_given_evidence: float | None
    ordering_used: tuple[str, ...] | None
    peak_factor_size_self_report: int | None
    true_peak_factor_size: int | None
    gap_nats: float | None


@dataclass(frozen=True)
class GeneratedCandidate:
    total_variables: int
    variables: tuple[VariableSpec, ...]
    query_variable: str
    evidence: dict[str, int]
    hidden_clusters: dict[str, tuple[str, ...]]
    bridge_variables: tuple[str, ...]
    decoy_variable: str


@dataclass(frozen=True)
class BayesianVEInstance:
    seed: int
    difficulty: str
    requested_total_variables: int
    total_variables: int
    variables: tuple[VariableSpec, ...]
    query_variable: str
    evidence: dict[str, int]
    eliminable_variables: tuple[str, ...]
    exact_posterior: float
    baseline_ordering: tuple[str, ...]
    baseline_peak_factor_size: int
    gold_ordering: tuple[str, ...]
    gold_peak_factor_size: int
    gold_source: str
    heuristic_results: tuple[OrderingSummary, ...]
    random_search_best: OrderingSummary
    min_fill_peak_factor_size: int
    problem_statement: str
    hidden_clusters: dict[str, tuple[str, ...]]
    bridge_variables: tuple[str, ...]
    decoy_variable: str
    attempt_index: int
    size_escalated: bool
    scale_note: str | None


def build_instance_payload(seed: int, difficulty: str) -> dict[str, Any]:
    requested_total_variables = _difficulty_to_requested_total_variables(difficulty)
    instance = build_instance(
        seed=seed,
        difficulty=difficulty,
        requested_total_variables=requested_total_variables,
    )
    return _instance_to_payload(instance)


def verify(instance: dict[str, Any], submission: dict[str, Any]) -> tuple[float, bool, dict[str, Any]]:
    try:
        ve_instance = _instance_from_payload(instance)
    except ValueError as exc:
        return FAILURE_GAP_PCT, False, {"failure_reason": f"invalid instance: {exc}"}

    verification = verify_best_guess(ve_instance, submission)
    if not verification.is_valid:
        return FAILURE_GAP_PCT, False, {"failure_reason": verification.failure_reason}

    submitted_probability = float(verification.p_query_given_evidence)
    gap_pct = _posterior_gap_pct(ve_instance.exact_posterior, submitted_probability)
    return (
        gap_pct,
        True,
        {
            "submitted_probability": submitted_probability,
            "exact_posterior": ve_instance.exact_posterior,
            "absolute_probability_error": abs(submitted_probability - ve_instance.exact_posterior),
            "gap_pct": gap_pct,
            "gap_nats": verification.gap_nats,
            "ordering_used": list(verification.ordering_used or ()),
            "submitted_peak_factor_size": verification.peak_factor_size_self_report,
            "true_peak_factor_size": verification.true_peak_factor_size,
            "gold_ordering": list(ve_instance.gold_ordering),
            "gold_peak_factor_size": ve_instance.gold_peak_factor_size,
            "gold_source": ve_instance.gold_source,
            "peak_factor_size_matches": (
                verification.peak_factor_size_self_report == verification.true_peak_factor_size
            ),
        },
    )


def build_instance(
    *,
    seed: int,
    difficulty: str,
    requested_total_variables: int = 22,
    max_generation_attempts: int = 16,
    random_order_samples: int = RANDOM_ORDER_SAMPLES,
) -> BayesianVEInstance:
    size_queue = [requested_total_variables]
    size_queue.extend(
        size for size in DEFAULT_VARIABLE_SIZES if size > requested_total_variables and size not in size_queue
    )

    best_candidate: BayesianVEInstance | None = None
    best_score: tuple[int, int, float] | None = None
    last_reason = "no candidate generated"
    scale_note: str | None = None

    for size_index, total_variables in enumerate(size_queue):
        best_for_size: BayesianVEInstance | None = None
        best_for_size_score: tuple[int, int, float] | None = None
        any_hard_enough = False

        for attempt_index in range(max_generation_attempts):
            candidate_seed = seed + size_index * 100_000 + attempt_index * 10_007
            candidate = _generate_candidate(seed=candidate_seed, total_variables=total_variables)
            instance = _finalize_candidate(
                seed=seed,
                difficulty=difficulty,
                requested_total_variables=requested_total_variables,
                candidate=candidate,
                attempt_index=attempt_index,
                random_order_samples=random_order_samples,
                scale_note=scale_note,
            )
            score = _candidate_score(instance)
            if best_candidate is None or score > best_score:
                best_candidate = instance
                best_score = score
            if best_for_size is None or score > best_for_size_score:
                best_for_size = instance
                best_for_size_score = score
            if total_variables == 22 and instance.min_fill_peak_factor_size <= 4:
                last_reason = (
                    f"attempt {attempt_index} at 22 vars still looked easy "
                    f"(min-fill peak factor size {instance.min_fill_peak_factor_size})"
                )
                continue
            any_hard_enough = True

        if total_variables == 22 and not any_hard_enough:
            scale_note = "All 22-variable attempts had min-fill peak factor size <= 4, so the spike escalated."
            last_reason = scale_note
            continue
        if best_for_size is not None:
            return best_for_size

    if best_candidate is not None:
        return best_candidate
    raise RuntimeError(f"failed to generate a Bayesian VE instance: {last_reason}")


def verify_best_guess(instance: BayesianVEInstance, best_guess: dict[str, Any]) -> GuessVerification:
    if not isinstance(best_guess, dict):
        return GuessVerification(False, "BEST_GUESS must be a JSON object", None, None, None, None, None)

    try:
        probability = float(best_guess["p_query_given_evidence"])
    except Exception:
        return GuessVerification(False, "p_query_given_evidence must be numeric", None, None, None, None, None)
    if not 0.0 < probability < 1.0:
        return GuessVerification(
            False,
            "p_query_given_evidence must lie strictly between 0 and 1",
            None,
            None,
            None,
            None,
            None,
        )

    ordering_used = best_guess.get("ordering_used")
    normalized_order = normalize_elimination_order(instance, ordering_used)
    if normalized_order is None:
        return GuessVerification(
            False,
            "ordering_used must list every eliminable variable exactly once and exclude query/evidence variables",
            None,
            None,
            None,
            None,
            None,
        )

    try:
        self_reported_peak = int(best_guess["peak_factor_size_self_report"])
    except Exception:
        return GuessVerification(
            False,
            "peak_factor_size_self_report must be an integer",
            None,
            None,
            None,
            None,
            None,
        )
    if self_reported_peak < 1:
        return GuessVerification(
            False,
            "peak_factor_size_self_report must be positive",
            None,
            None,
            None,
            None,
            None,
        )

    _, true_peak = evaluate_exact_probability(instance, normalized_order)
    gap_nats = abs(math.log(instance.exact_posterior) - math.log(probability))
    return GuessVerification(
        is_valid=True,
        failure_reason=None,
        p_query_given_evidence=probability,
        ordering_used=normalized_order,
        peak_factor_size_self_report=self_reported_peak,
        true_peak_factor_size=true_peak,
        gap_nats=gap_nats,
    )


def normalize_elimination_order(
    instance: BayesianVEInstance,
    ordering: Sequence[Any] | None,
) -> tuple[str, ...] | None:
    if not isinstance(ordering, Sequence) or isinstance(ordering, (str, bytes)):
        return None
    names = tuple(str(value).strip() for value in ordering)
    if not all(names):
        return None
    if len(names) != len(instance.eliminable_variables):
        return None
    if set(names) != set(instance.eliminable_variables):
        return None
    if len(set(names)) != len(names):
        return None
    return names


def render_problem(instance: BayesianVEInstance) -> str:
    evidence_terms = ", ".join(f"{name}={value}" for name, value in instance.evidence.items())
    lines = [
        "You are doing exact inference in a Bayesian network with binary variables in {0, 1}.",
        f"Task: report P({instance.query_variable}=1 | {evidence_terms}).",
        "All CPT rows below give P(variable=1 | parents); P(variable=0 | parents) = 1 minus that value.",
        "When you report ordering_used, list every eliminable variable exactly once and do not include the query variable or any evidence variable.",
        "Interpret peak_factor_size as the largest intermediate factor scope size, counted as the number of variables in that factor before summing out the eliminated variable.",
        "",
        f"Variables: {', '.join(variable.name for variable in instance.variables)}",
        f"Query variable: {instance.query_variable}",
        f"Evidence: {evidence_terms}",
        f"Eliminable variables ({len(instance.eliminable_variables)}): {', '.join(instance.eliminable_variables)}",
        "",
        "Bayesian network (topological order):",
    ]
    for variable in instance.variables:
        parent_text = ", ".join(variable.parents) if variable.parents else "none"
        lines.append(f"- {variable.name}: parents = [{parent_text}]")
        if not variable.parents:
            lines.append(f"  P({variable.name}=1) = {_fmt_prob(variable.cpt_true_probs[0])}")
            continue
        for assignment_index, probability in enumerate(variable.cpt_true_probs):
            assignment = _bits_from_index(assignment_index, len(variable.parents))
            parent_terms = ", ".join(
                f"{parent}={value}" for parent, value in zip(variable.parents, assignment, strict=True)
            )
            lines.append(f"  if {parent_terms} -> P({variable.name}=1) = {_fmt_prob(probability)}")
    return "\n".join(lines)


def evaluate_exact_probability(
    instance: BayesianVEInstance,
    ordering: Sequence[str],
) -> tuple[float, int]:
    normalized_order = normalize_elimination_order(instance, ordering)
    if normalized_order is None:
        raise ValueError("invalid elimination ordering")

    factors = list(_build_conditioned_factors(instance.variables, instance.evidence))
    peak_factor_size = max((len(factor.scope) for factor in factors if factor.scope), default=1)

    for variable_name in normalized_order:
        involved = [factor for factor in factors if variable_name in factor.scope]
        untouched = [factor for factor in factors if variable_name not in factor.scope]
        if not involved:
            factors = untouched
            continue
        product_factor = _multiply_all(involved)
        peak_factor_size = max(peak_factor_size, len(product_factor.scope))
        reduced = _sum_out(product_factor, variable_name)
        if reduced.scope or not math.isclose(reduced.values[0], 1.0, rel_tol=0.0, abs_tol=1e-12):
            untouched.append(reduced)
        factors = untouched

    final_factor = _multiply_all(factors)
    if instance.query_variable not in final_factor.scope:
        raise RuntimeError("query variable disappeared during elimination")
    probability_zero = _factor_probability_for_assignment(final_factor, {instance.query_variable: 0})
    probability_one = _factor_probability_for_assignment(final_factor, {instance.query_variable: 1})
    normalizer = probability_zero + probability_one
    if normalizer <= 0.0:
        raise RuntimeError("invalid posterior normalizer")
    return probability_one / normalizer, peak_factor_size


def evaluate_ordering_peak_from_scopes(
    initial_scopes: Sequence[frozenset[str]],
    ordering: Sequence[str],
) -> int:
    scopes = [set(scope) for scope in initial_scopes if scope]
    peak_factor_size = max((len(scope) for scope in scopes), default=1)
    for variable_name in ordering:
        touched = [scope for scope in scopes if variable_name in scope]
        untouched = [scope for scope in scopes if variable_name not in scope]
        if not touched:
            scopes = untouched
            continue
        merged_scope = set().union(*touched)
        peak_factor_size = max(peak_factor_size, len(merged_scope))
        next_scope = merged_scope - {variable_name}
        if next_scope:
            untouched.append(next_scope)
        scopes = untouched
    return peak_factor_size


def _finalize_candidate(
    *,
    seed: int,
    difficulty: str,
    requested_total_variables: int,
    candidate: GeneratedCandidate,
    attempt_index: int,
    random_order_samples: int,
    scale_note: str | None,
) -> BayesianVEInstance:
    eliminable_variables = tuple(
        variable.name
        for variable in candidate.variables
        if variable.name != candidate.query_variable and variable.name not in candidate.evidence
    )
    initial_scopes = tuple(
        frozenset(factor.scope)
        for factor in _build_conditioned_factors(candidate.variables, candidate.evidence)
        if factor.scope
    )

    heuristic_orders = (
        OrderingSummary(
            name="baseline",
            ordering=tuple(sorted(eliminable_variables)),
            peak_factor_size=evaluate_ordering_peak_from_scopes(initial_scopes, tuple(sorted(eliminable_variables))),
        ),
        OrderingSummary(
            name="min_neighbors",
            ordering=_build_greedy_order(initial_scopes, eliminable_variables, rule="min_neighbors"),
            peak_factor_size=0,
        ),
        OrderingSummary(
            name="min_weight",
            ordering=_build_greedy_order(initial_scopes, eliminable_variables, rule="min_weight"),
            peak_factor_size=0,
        ),
        OrderingSummary(
            name="min_fill",
            ordering=_build_greedy_order(initial_scopes, eliminable_variables, rule="min_fill"),
            peak_factor_size=0,
        ),
    )
    realized_heuristics: list[OrderingSummary] = []
    for summary in heuristic_orders:
        peak = summary.peak_factor_size or evaluate_ordering_peak_from_scopes(initial_scopes, summary.ordering)
        realized_heuristics.append(
            OrderingSummary(
                name=summary.name,
                ordering=summary.ordering,
                peak_factor_size=peak,
            )
        )

    rng = Random(seed + candidate.total_variables * 997 + attempt_index * 13)
    random_best_ordering = tuple(eliminable_variables)
    random_best_peak = evaluate_ordering_peak_from_scopes(initial_scopes, random_best_ordering)
    for _ in range(random_order_samples):
        proposal = list(eliminable_variables)
        rng.shuffle(proposal)
        peak = evaluate_ordering_peak_from_scopes(initial_scopes, proposal)
        if peak < random_best_peak:
            random_best_ordering = tuple(proposal)
            random_best_peak = peak
    random_search_best = OrderingSummary(
        name="random_best_of_1000",
        ordering=random_best_ordering,
        peak_factor_size=random_best_peak,
    )

    gold_candidates = list(realized_heuristics[1:]) + [random_search_best]
    gold = min(gold_candidates, key=lambda summary: (summary.peak_factor_size, summary.name, summary.ordering))
    stub = BayesianVEInstance(
        seed=seed,
        difficulty=difficulty,
        requested_total_variables=requested_total_variables,
        total_variables=candidate.total_variables,
        variables=candidate.variables,
        query_variable=candidate.query_variable,
        evidence=candidate.evidence,
        eliminable_variables=eliminable_variables,
        exact_posterior=0.0,
        baseline_ordering=realized_heuristics[0].ordering,
        baseline_peak_factor_size=realized_heuristics[0].peak_factor_size,
        gold_ordering=gold.ordering,
        gold_peak_factor_size=gold.peak_factor_size,
        gold_source=gold.name,
        heuristic_results=tuple(realized_heuristics[1:]),
        random_search_best=random_search_best,
        min_fill_peak_factor_size=next(
            summary.peak_factor_size for summary in realized_heuristics if summary.name == "min_fill"
        ),
        problem_statement="",
        hidden_clusters=candidate.hidden_clusters,
        bridge_variables=candidate.bridge_variables,
        decoy_variable=candidate.decoy_variable,
        attempt_index=attempt_index,
        size_escalated=candidate.total_variables != requested_total_variables,
        scale_note=scale_note,
    )
    exact_posterior, _ = evaluate_exact_probability(stub, gold.ordering)
    instance_without_render = BayesianVEInstance(
        seed=seed,
        difficulty=difficulty,
        requested_total_variables=requested_total_variables,
        total_variables=candidate.total_variables,
        variables=candidate.variables,
        query_variable=candidate.query_variable,
        evidence=candidate.evidence,
        eliminable_variables=eliminable_variables,
        exact_posterior=exact_posterior,
        baseline_ordering=realized_heuristics[0].ordering,
        baseline_peak_factor_size=realized_heuristics[0].peak_factor_size,
        gold_ordering=gold.ordering,
        gold_peak_factor_size=gold.peak_factor_size,
        gold_source=gold.name,
        heuristic_results=tuple(realized_heuristics[1:]),
        random_search_best=random_search_best,
        min_fill_peak_factor_size=next(
            summary.peak_factor_size for summary in realized_heuristics if summary.name == "min_fill"
        ),
        problem_statement="",
        hidden_clusters=candidate.hidden_clusters,
        bridge_variables=candidate.bridge_variables,
        decoy_variable=candidate.decoy_variable,
        attempt_index=attempt_index,
        size_escalated=candidate.total_variables != requested_total_variables,
        scale_note=scale_note,
    )
    return BayesianVEInstance(
        seed=seed,
        difficulty=difficulty,
        requested_total_variables=requested_total_variables,
        total_variables=candidate.total_variables,
        variables=candidate.variables,
        query_variable=candidate.query_variable,
        evidence=candidate.evidence,
        eliminable_variables=eliminable_variables,
        exact_posterior=exact_posterior,
        baseline_ordering=realized_heuristics[0].ordering,
        baseline_peak_factor_size=realized_heuristics[0].peak_factor_size,
        gold_ordering=gold.ordering,
        gold_peak_factor_size=gold.peak_factor_size,
        gold_source=gold.name,
        heuristic_results=tuple(realized_heuristics[1:]),
        random_search_best=random_search_best,
        min_fill_peak_factor_size=next(
            summary.peak_factor_size for summary in realized_heuristics if summary.name == "min_fill"
        ),
        problem_statement=render_problem(instance_without_render),
        hidden_clusters=candidate.hidden_clusters,
        bridge_variables=candidate.bridge_variables,
        decoy_variable=candidate.decoy_variable,
        attempt_index=attempt_index,
        size_escalated=candidate.total_variables != requested_total_variables,
        scale_note=scale_note,
    )


def _candidate_score(instance: BayesianVEInstance) -> tuple[int, int, float]:
    heuristic_peaks = [summary.peak_factor_size for summary in instance.heuristic_results]
    spread = max(heuristic_peaks) - min(heuristic_peaks)
    baseline_advantage = instance.baseline_peak_factor_size - instance.gold_peak_factor_size
    posterior_balance = -abs(instance.exact_posterior - 0.5)
    return (baseline_advantage, spread, posterior_balance)


def _generate_candidate(*, seed: int, total_variables: int) -> GeneratedCandidate:
    rng = Random(seed)
    cluster_sizes = _cluster_sizes(total_variables - 3)
    hidden_clusters = {
        "A": tuple(f"A{index}" for index in range(1, cluster_sizes[0] + 1)),
        "B": tuple(f"B{index}" for index in range(1, cluster_sizes[1] + 1)),
        "C": tuple(f"C{index}" for index in range(1, cluster_sizes[2] + 1)),
    }
    bridge_variables = ("BR01", "BR12")
    decoy_variable = "D0"

    early_clusters = {name: values[: max(3, len(values) // 2)] for name, values in hidden_clusters.items()}
    late_clusters = {name: values[len(early_clusters[name]) :] for name, values in hidden_clusters.items()}

    topological_order = (
        list(hidden_clusters["A"][: len(early_clusters["A"])])
        + list(hidden_clusters["B"][: len(early_clusters["B"])])
        + list(hidden_clusters["C"][: len(early_clusters["C"])])
        + [decoy_variable, *bridge_variables]
        + list(late_clusters["A"])
        + list(late_clusters["B"])
        + list(late_clusters["C"])
    )

    parent_map: dict[str, tuple[str, ...]] = {}
    position = {name: index for index, name in enumerate(topological_order)}

    for cluster_name in ("A", "B", "C"):
        early_nodes = early_clusters[cluster_name]
        for index, variable_name in enumerate(early_nodes):
            parents: list[str] = []
            if index >= 1:
                parents.append(early_nodes[index - 1])
            if index >= 2:
                parents.append(early_nodes[index - 2])
            if cluster_name == "B" and index == 0:
                parents.append(hidden_clusters["A"][min(1, len(hidden_clusters["A"]) - 1)])
            if cluster_name == "C" and index == 0:
                parents.append(hidden_clusters["B"][min(1, len(hidden_clusters["B"]) - 1)])
            parent_map[variable_name] = tuple(dict.fromkeys(parents))

    parent_map[decoy_variable] = (
        early_clusters["A"][-1],
        early_clusters["B"][-1],
        early_clusters["C"][-1],
    )
    parent_map["BR01"] = (
        early_clusters["A"][-2],
        early_clusters["B"][-2],
    )
    parent_map["BR12"] = (
        early_clusters["B"][-1],
        early_clusters["C"][-2],
    )

    for cluster_name in ("A", "B", "C"):
        late_nodes = late_clusters[cluster_name]
        all_cluster_nodes = hidden_clusters[cluster_name]
        for index, variable_name in enumerate(late_nodes):
            earlier_same_cluster = [name for name in all_cluster_nodes if position[name] < position[variable_name]]
            parents = list(earlier_same_cluster[-2:]) if len(earlier_same_cluster) >= 2 else list(earlier_same_cluster)
            if cluster_name == "A":
                if index in {0, len(late_nodes) - 1}:
                    parents.append(decoy_variable)
            elif cluster_name == "B":
                if index == 0:
                    parents.append("BR01")
                if index == 1:
                    parents.append(decoy_variable)
                if index == len(late_nodes) - 1:
                    parents.extend([decoy_variable, "BR12"])
            else:
                if index == 0:
                    parents.append("BR12")
                if index in {0, len(late_nodes) - 1}:
                    parents.append(decoy_variable)
            if cluster_name == "B" and index < len(hidden_clusters["A"]):
                parents.append(hidden_clusters["A"][min(len(hidden_clusters["A"]) - 1, index + 1)])
            if cluster_name == "C" and index < len(hidden_clusters["B"]):
                parents.append(hidden_clusters["B"][min(len(hidden_clusters["B"]) - 1, index + 1)])
            parent_map[variable_name] = tuple(dict.fromkeys(parents[-3:]))

    variables = tuple(
        VariableSpec(
            name=variable_name,
            parents=parent_map.get(variable_name, ()),
            cpt_true_probs=_generate_cpt(
                rng=rng,
                variable_name=variable_name,
                parents=parent_map.get(variable_name, ()),
            ),
        )
        for variable_name in topological_order
    )

    query_variable = late_clusters["B"][-1]
    evidence_candidates = [
        late_clusters["A"][-1],
        hidden_clusters["B"][0],
        late_clusters["B"][0],
        late_clusters["C"][-1],
        hidden_clusters["C"][1],
    ]
    evidence = {
        variable_name: rng.randint(0, 1)
        for variable_name in evidence_candidates
        if variable_name != query_variable
    }
    return GeneratedCandidate(
        total_variables=total_variables,
        variables=variables,
        query_variable=query_variable,
        evidence=evidence,
        hidden_clusters=hidden_clusters,
        bridge_variables=bridge_variables,
        decoy_variable=decoy_variable,
    )


def _cluster_sizes(core_variable_count: int) -> tuple[int, int, int]:
    base = core_variable_count // 3
    remainder = core_variable_count - 3 * base
    return (base, base + remainder, base)


def _generate_cpt(*, rng: Random, variable_name: str, parents: Sequence[str]) -> tuple[float, ...]:
    if not parents:
        return (_rounded_probability(0.35 + 0.30 * rng.random()),)

    base = rng.uniform(-0.9, 0.9)
    weights = []
    for parent_name in parents:
        magnitude = rng.uniform(0.55, 1.35)
        sign = -1.0 if rng.random() < 0.45 else 1.0
        if parent_name in {"D0", "BR01", "BR12"} or variable_name in {"D0", "BR01", "BR12"}:
            magnitude += 0.15
        weights.append(sign * magnitude)

    probabilities = []
    for assignment_index in range(1 << len(parents)):
        assignment = _bits_from_index(assignment_index, len(parents))
        logit = base
        for bit, weight in zip(assignment, weights, strict=True):
            logit += weight * (1.0 if bit else -1.0)
        probability = 1.0 / (1.0 + math.exp(-logit))
        probabilities.append(_rounded_probability(probability))
    return tuple(probabilities)


def _rounded_probability(probability: float) -> float:
    clipped = min(0.95, max(0.05, probability))
    return round(clipped, 3)


def _build_conditioned_factors(
    variables: Sequence[VariableSpec],
    evidence: dict[str, int],
) -> tuple[Factor, ...]:
    factors: list[Factor] = []
    for variable in variables:
        reduced_scope = [parent for parent in variable.parents if parent not in evidence]
        include_variable = variable.name not in evidence
        if include_variable:
            reduced_scope.append(variable.name)
        values: list[float] = []
        for assignment_index in range(1 << len(reduced_scope)):
            reduced_assignment = _bits_from_index(assignment_index, len(reduced_scope))
            assignment_map = dict(zip(reduced_scope, reduced_assignment, strict=True))
            parent_assignment = tuple(
                evidence[parent_name] if parent_name in evidence else assignment_map[parent_name]
                for parent_name in variable.parents
            )
            variable_value = evidence[variable.name] if variable.name in evidence else assignment_map[variable.name]
            p_true = variable.cpt_true_probs[_index_from_bits(parent_assignment)]
            values.append(p_true if variable_value == 1 else 1.0 - p_true)
        factors.append(Factor(scope=tuple(reduced_scope), values=tuple(values)))
    return tuple(factors)


def _build_greedy_order(
    initial_scopes: Sequence[frozenset[str]],
    eliminable_variables: Sequence[str],
    *,
    rule: str,
) -> tuple[str, ...]:
    remaining = list(eliminable_variables)
    scopes = [set(scope) for scope in initial_scopes if scope]
    order: list[str] = []

    while remaining:
        adjacency = _adjacency_from_scopes(scopes)
        incident_scopes = {name: [scope for scope in scopes if name in scope] for name in remaining}

        def score(name: str) -> tuple[Any, ...]:
            neighbors = adjacency.get(name, set())
            mass = sum(1 << len(scope) for scope in incident_scopes[name]) or 1
            if rule == "min_neighbors":
                return (len(neighbors), mass, name)
            if rule == "min_weight":
                return (mass, len(neighbors), name)
            if rule == "min_fill":
                fill_edges = 0
                neighbor_list = sorted(neighbors)
                for left, right in combinations(neighbor_list, 2):
                    if right not in adjacency.get(left, set()):
                        fill_edges += 1
                return (fill_edges, len(neighbors), mass, name)
            raise ValueError(f"unknown rule: {rule}")

        choice = min(remaining, key=score)
        order.append(choice)
        remaining.remove(choice)

        touched = [scope for scope in scopes if choice in scope]
        untouched = [scope for scope in scopes if choice not in scope]
        merged = set().union(*touched) if touched else {choice}
        next_scope = merged - {choice}
        if next_scope:
            untouched.append(next_scope)
        scopes = untouched

    return tuple(order)


def _adjacency_from_scopes(scopes: Iterable[set[str]]) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {}
    for scope in scopes:
        for variable_name in scope:
            adjacency.setdefault(variable_name, set())
        for left, right in combinations(scope, 2):
            adjacency[left].add(right)
            adjacency[right].add(left)
    return adjacency


def _multiply_all(factors: Sequence[Factor]) -> Factor:
    if not factors:
        return Factor(scope=(), values=(1.0,))
    result = factors[0]
    for factor in factors[1:]:
        result = _multiply(result, factor)
    return result


def _multiply(left: Factor, right: Factor) -> Factor:
    scope = tuple(dict.fromkeys((*left.scope, *right.scope)))
    values: list[float] = []
    for assignment_index in range(1 << len(scope)):
        assignment = _bits_from_index(assignment_index, len(scope))
        assignment_map = dict(zip(scope, assignment, strict=True))
        values.append(
            _factor_probability_for_assignment(left, assignment_map)
            * _factor_probability_for_assignment(right, assignment_map)
        )
    return Factor(scope=scope, values=tuple(values))


def _sum_out(factor: Factor, variable_name: str) -> Factor:
    if variable_name not in factor.scope:
        return factor
    reduced_scope = tuple(name for name in factor.scope if name != variable_name)
    values: list[float] = []
    for assignment_index in range(1 << len(reduced_scope)):
        assignment = _bits_from_index(assignment_index, len(reduced_scope))
        assignment_map = dict(zip(reduced_scope, assignment, strict=True))
        total = 0.0
        for value in (0, 1):
            total += _factor_probability_for_assignment(
                factor,
                {**assignment_map, variable_name: value},
            )
        values.append(total)
    return Factor(scope=reduced_scope, values=tuple(values))


def _factor_probability_for_assignment(factor: Factor, assignment_map: dict[str, int]) -> float:
    if not factor.scope:
        return factor.values[0]
    bits = tuple(int(assignment_map[name]) for name in factor.scope)
    return factor.values[_index_from_bits(bits)]


def _bits_from_index(index: int, width: int) -> tuple[int, ...]:
    return tuple((index >> shift) & 1 for shift in reversed(range(width)))


def _index_from_bits(bits: Sequence[int]) -> int:
    index = 0
    for bit in bits:
        index = (index << 1) | int(bit)
    return index


def _fmt_prob(probability: float) -> str:
    return f"{probability:.3f}"


def _difficulty_to_requested_total_variables(difficulty: str) -> int:
    normalized = difficulty.strip().lower()
    if normalized not in DIFFICULTY_TO_VARIABLES:
        raise ValueError(f"unsupported difficulty: {difficulty}")
    return DIFFICULTY_TO_VARIABLES[normalized]


def _instance_to_payload(instance: BayesianVEInstance) -> dict[str, Any]:
    return {
        "seed": instance.seed,
        "difficulty": instance.difficulty,
        "requested_total_variables": instance.requested_total_variables,
        "total_variables": instance.total_variables,
        "variables": [
            {
                "name": variable.name,
                "parents": list(variable.parents),
                "cpt_true_probs": list(variable.cpt_true_probs),
            }
            for variable in instance.variables
        ],
        "query_variable": instance.query_variable,
        "evidence": dict(instance.evidence),
        "eliminable_variables": list(instance.eliminable_variables),
        "exact_posterior": instance.exact_posterior,
        "baseline_ordering": list(instance.baseline_ordering),
        "baseline_peak_factor_size": instance.baseline_peak_factor_size,
        "gold_ordering": list(instance.gold_ordering),
        "gold_peak_factor_size": instance.gold_peak_factor_size,
        "gold_source": instance.gold_source,
        "heuristic_results": [
            {
                "name": summary.name,
                "ordering": list(summary.ordering),
                "peak_factor_size": summary.peak_factor_size,
            }
            for summary in instance.heuristic_results
        ],
        "random_search_best": {
            "name": instance.random_search_best.name,
            "ordering": list(instance.random_search_best.ordering),
            "peak_factor_size": instance.random_search_best.peak_factor_size,
        },
        "min_fill_peak_factor_size": instance.min_fill_peak_factor_size,
        "problem_statement": instance.problem_statement,
        "hidden_clusters": {
            cluster_name: list(variable_names)
            for cluster_name, variable_names in instance.hidden_clusters.items()
        },
        "bridge_variables": list(instance.bridge_variables),
        "decoy_variable": instance.decoy_variable,
        "attempt_index": instance.attempt_index,
        "size_escalated": instance.size_escalated,
        "scale_note": instance.scale_note,
    }


def _instance_from_payload(payload: dict[str, Any]) -> BayesianVEInstance:
    if not isinstance(payload, dict):
        raise ValueError("instance must be a dict")

    variables_payload = payload.get("variables")
    if not isinstance(variables_payload, list) or not variables_payload:
        raise ValueError("variables must be a non-empty list")
    variables = tuple(_variable_from_payload(item) for item in variables_payload)

    query_variable = _required_str(payload.get("query_variable"), "query_variable")
    evidence = _int_mapping(payload.get("evidence"), "evidence")
    eliminable_variables = payload.get("eliminable_variables")
    if eliminable_variables is None:
        eliminable_variables_tuple = tuple(
            variable.name for variable in variables if variable.name != query_variable and variable.name not in evidence
        )
    else:
        eliminable_variables_tuple = _string_tuple(eliminable_variables, "eliminable_variables")

    requested_total_variables = _optional_int(payload.get("requested_total_variables"), 22, "requested_total_variables")
    total_variables = _optional_int(payload.get("total_variables"), len(variables), "total_variables")
    seed = _optional_int(payload.get("seed"), 0, "seed")
    difficulty = str(payload.get("difficulty", "medium"))

    initial_scopes = tuple(
        frozenset(factor.scope)
        for factor in _build_conditioned_factors(variables, evidence)
        if factor.scope
    )

    baseline_ordering = tuple(sorted(eliminable_variables_tuple))
    if "baseline_ordering" in payload:
        baseline_ordering = _string_tuple(payload["baseline_ordering"], "baseline_ordering")
    baseline_peak = payload.get("baseline_peak_factor_size")
    if baseline_peak is None:
        baseline_peak_factor_size = evaluate_ordering_peak_from_scopes(initial_scopes, baseline_ordering)
    else:
        baseline_peak_factor_size = _optional_int(baseline_peak, 0, "baseline_peak_factor_size")

    heuristic_payload = payload.get("heuristic_results")
    if heuristic_payload is None:
        heuristic_results = (
            OrderingSummary(
                name="min_neighbors",
                ordering=_build_greedy_order(initial_scopes, eliminable_variables_tuple, rule="min_neighbors"),
                peak_factor_size=0,
            ),
            OrderingSummary(
                name="min_weight",
                ordering=_build_greedy_order(initial_scopes, eliminable_variables_tuple, rule="min_weight"),
                peak_factor_size=0,
            ),
            OrderingSummary(
                name="min_fill",
                ordering=_build_greedy_order(initial_scopes, eliminable_variables_tuple, rule="min_fill"),
                peak_factor_size=0,
            ),
        )
        heuristic_results = tuple(
            OrderingSummary(
                name=summary.name,
                ordering=summary.ordering,
                peak_factor_size=evaluate_ordering_peak_from_scopes(initial_scopes, summary.ordering),
            )
            for summary in heuristic_results
        )
    else:
        if not isinstance(heuristic_payload, list):
            raise ValueError("heuristic_results must be a list")
        heuristic_results = tuple(_ordering_summary_from_payload(item) for item in heuristic_payload)

    random_search_best_payload = payload.get("random_search_best")
    if random_search_best_payload is None:
        random_search_best = OrderingSummary(
            name="random_best_of_1000",
            ordering=baseline_ordering,
            peak_factor_size=baseline_peak_factor_size,
        )
    else:
        random_search_best = _ordering_summary_from_payload(random_search_best_payload)

    gold_ordering = payload.get("gold_ordering")
    if gold_ordering is None:
        gold_candidates = list(heuristic_results) + [random_search_best]
        gold = min(gold_candidates, key=lambda summary: (summary.peak_factor_size, summary.name, summary.ordering))
        gold_ordering_tuple = gold.ordering
        gold_peak_factor_size = gold.peak_factor_size
        gold_source = gold.name
    else:
        gold_ordering_tuple = _string_tuple(gold_ordering, "gold_ordering")
        gold_peak = payload.get("gold_peak_factor_size")
        if gold_peak is None:
            gold_peak_factor_size = evaluate_ordering_peak_from_scopes(initial_scopes, gold_ordering_tuple)
        else:
            gold_peak_factor_size = _optional_int(gold_peak, 0, "gold_peak_factor_size")
        gold_source = str(payload.get("gold_source", "provided"))

    exact_posterior_value = payload.get("exact_posterior")
    instance_stub = BayesianVEInstance(
        seed=seed,
        difficulty=difficulty,
        requested_total_variables=requested_total_variables,
        total_variables=total_variables,
        variables=variables,
        query_variable=query_variable,
        evidence=evidence,
        eliminable_variables=eliminable_variables_tuple,
        exact_posterior=0.0,
        baseline_ordering=baseline_ordering,
        baseline_peak_factor_size=baseline_peak_factor_size,
        gold_ordering=gold_ordering_tuple,
        gold_peak_factor_size=gold_peak_factor_size,
        gold_source=gold_source,
        heuristic_results=heuristic_results,
        random_search_best=random_search_best,
        min_fill_peak_factor_size=_optional_int(
            payload.get("min_fill_peak_factor_size"),
            _min_fill_peak(heuristic_results),
            "min_fill_peak_factor_size",
        ),
        problem_statement=str(payload.get("problem_statement", "")),
        hidden_clusters=_cluster_mapping(payload.get("hidden_clusters")),
        bridge_variables=_optional_string_tuple(payload.get("bridge_variables")),
        decoy_variable=str(payload.get("decoy_variable", "D0")),
        attempt_index=_optional_int(payload.get("attempt_index"), 0, "attempt_index"),
        size_escalated=bool(payload.get("size_escalated", total_variables != requested_total_variables)),
        scale_note=None if payload.get("scale_note") is None else str(payload.get("scale_note")),
    )

    if exact_posterior_value is None:
        exact_posterior, _ = evaluate_exact_probability(instance_stub, gold_ordering_tuple)
    else:
        exact_posterior = float(exact_posterior_value)

    problem_statement = instance_stub.problem_statement or render_problem(
        BayesianVEInstance(
            seed=instance_stub.seed,
            difficulty=instance_stub.difficulty,
            requested_total_variables=instance_stub.requested_total_variables,
            total_variables=instance_stub.total_variables,
            variables=instance_stub.variables,
            query_variable=instance_stub.query_variable,
            evidence=instance_stub.evidence,
            eliminable_variables=instance_stub.eliminable_variables,
            exact_posterior=exact_posterior,
            baseline_ordering=instance_stub.baseline_ordering,
            baseline_peak_factor_size=instance_stub.baseline_peak_factor_size,
            gold_ordering=instance_stub.gold_ordering,
            gold_peak_factor_size=instance_stub.gold_peak_factor_size,
            gold_source=instance_stub.gold_source,
            heuristic_results=instance_stub.heuristic_results,
            random_search_best=instance_stub.random_search_best,
            min_fill_peak_factor_size=instance_stub.min_fill_peak_factor_size,
            problem_statement="",
            hidden_clusters=instance_stub.hidden_clusters,
            bridge_variables=instance_stub.bridge_variables,
            decoy_variable=instance_stub.decoy_variable,
            attempt_index=instance_stub.attempt_index,
            size_escalated=instance_stub.size_escalated,
            scale_note=instance_stub.scale_note,
        )
    )

    return BayesianVEInstance(
        seed=instance_stub.seed,
        difficulty=instance_stub.difficulty,
        requested_total_variables=instance_stub.requested_total_variables,
        total_variables=instance_stub.total_variables,
        variables=instance_stub.variables,
        query_variable=instance_stub.query_variable,
        evidence=instance_stub.evidence,
        eliminable_variables=instance_stub.eliminable_variables,
        exact_posterior=exact_posterior,
        baseline_ordering=instance_stub.baseline_ordering,
        baseline_peak_factor_size=instance_stub.baseline_peak_factor_size,
        gold_ordering=instance_stub.gold_ordering,
        gold_peak_factor_size=instance_stub.gold_peak_factor_size,
        gold_source=instance_stub.gold_source,
        heuristic_results=instance_stub.heuristic_results,
        random_search_best=instance_stub.random_search_best,
        min_fill_peak_factor_size=instance_stub.min_fill_peak_factor_size,
        problem_statement=problem_statement,
        hidden_clusters=instance_stub.hidden_clusters,
        bridge_variables=instance_stub.bridge_variables,
        decoy_variable=instance_stub.decoy_variable,
        attempt_index=instance_stub.attempt_index,
        size_escalated=instance_stub.size_escalated,
        scale_note=instance_stub.scale_note,
    )


def _variable_from_payload(payload: dict[str, Any]) -> VariableSpec:
    if not isinstance(payload, dict):
        raise ValueError("each variable must be a dict")
    name = _required_str(payload.get("name"), "variable.name")
    parents = _string_tuple(payload.get("parents", []), f"{name}.parents")
    cpt_true_probs_raw = payload.get("cpt_true_probs")
    if not isinstance(cpt_true_probs_raw, list) or not cpt_true_probs_raw:
        raise ValueError(f"{name}.cpt_true_probs must be a non-empty list")
    cpt_true_probs = tuple(float(value) for value in cpt_true_probs_raw)
    return VariableSpec(name=name, parents=parents, cpt_true_probs=cpt_true_probs)


def _ordering_summary_from_payload(payload: dict[str, Any]) -> OrderingSummary:
    if not isinstance(payload, dict):
        raise ValueError("ordering summary must be a dict")
    return OrderingSummary(
        name=_required_str(payload.get("name"), "ordering_summary.name"),
        ordering=_string_tuple(payload.get("ordering"), "ordering_summary.ordering"),
        peak_factor_size=_optional_int(payload.get("peak_factor_size"), 0, "ordering_summary.peak_factor_size"),
    )


def _required_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    result = tuple(str(item).strip() for item in value)
    if not all(result):
        raise ValueError(f"{field_name} must not contain empty values")
    return result


def _optional_string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError("expected a list of strings")
    return tuple(str(item).strip() for item in value if str(item).strip())


def _int_mapping(value: Any, field_name: str) -> dict[str, int]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dict")
    parsed: dict[str, int] = {}
    for key, raw in value.items():
        parsed[str(key)] = int(raw)
    return parsed


def _cluster_mapping(value: Any) -> dict[str, tuple[str, ...]]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("hidden_clusters must be a dict")
    parsed: dict[str, tuple[str, ...]] = {}
    for key, raw in value.items():
        if not isinstance(raw, list):
            raise ValueError("hidden_clusters values must be lists")
        parsed[str(key)] = tuple(str(item) for item in raw)
    return parsed


def _optional_int(value: Any, default: int, field_name: str) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be an integer") from exc


def _min_fill_peak(heuristic_results: Sequence[OrderingSummary]) -> int:
    for summary in heuristic_results:
        if summary.name == "min_fill":
            return summary.peak_factor_size
    return 0


def _posterior_gap_pct(exact_posterior: float, submitted_probability: float) -> float:
    denominator = max(abs(exact_posterior), MIN_POSITIVE)
    return 100.0 * abs(submitted_probability - exact_posterior) / denominator


__all__ = ["build_instance_payload", "verify"]
