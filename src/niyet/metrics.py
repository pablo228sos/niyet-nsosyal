from __future__ import annotations

from collections.abc import Iterable

from .allocator import Assignment
from .benchmark import LabeledMatch
from .types import Intent, Responder


def intent_coverage(assignments: Iterable[Assignment], intents: Iterable[Intent]) -> float:
    intent_ids = {intent.id for intent in intents}
    if not intent_ids:
        return 0.0
    covered = {assignment.intent_id for assignment in assignments}
    return len(covered & intent_ids) / len(intent_ids)


def mean_gold_relevance(
    assignments: Iterable[Assignment], labeled_matches: Iterable[LabeledMatch]
) -> float:
    gold = {
        (item.match.intent_id, item.match.responder_id): item.gold_relevance
        for item in labeled_matches
    }
    values = [
        gold[(assignment.intent_id, assignment.responder_id)]
        for assignment in assignments
        if (assignment.intent_id, assignment.responder_id) in gold
    ]
    if not values:
        return 0.0
    return sum(values) / len(values)


def responder_loads(
    assignments: Iterable[Assignment], responders: Iterable[Responder]
) -> dict[str, int]:
    loads = {responder.id: 0 for responder in responders}
    for assignment in assignments:
        if assignment.responder_id in loads:
            loads[assignment.responder_id] += 1
    return loads


def overload_count(
    assignments: Iterable[Assignment], responders: Iterable[Responder]
) -> int:
    responder_list = tuple(responders)
    budgets = {responder.id: responder.attention_budget for responder in responder_list}
    loads = responder_loads(assignments, responder_list)
    return sum(max(0, loads[responder_id] - budget) for responder_id, budget in budgets.items())


def gini(values: Iterable[int | float]) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered or sum(ordered) == 0:
        return 0.0

    n = len(ordered)
    weighted_sum = sum((index + 1) * value for index, value in enumerate(ordered))
    return (2 * weighted_sum) / (n * sum(ordered)) - (n + 1) / n


def responder_load_gini(
    assignments: Iterable[Assignment], responders: Iterable[Responder]
) -> float:
    loads = responder_loads(assignments, responders)
    return gini(loads.values())
