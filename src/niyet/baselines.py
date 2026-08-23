from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Callable, Iterable

from .allocator import Assignment
from .scoring import pair_score
from .types import CandidateMatch, Responder


def _capacity_greedy(
    matches: Iterable[CandidateMatch],
    responders: Iterable[Responder],
    *,
    rank_key: Callable[[CandidateMatch], float],
    max_responders_per_intent: int = 1,
) -> list[Assignment]:
    budgets = {
        responder.id: max(0, responder.attention_budget)
        for responder in responders
        if responder.active
    }
    responder_load = defaultdict(int)
    intent_load = defaultdict(int)
    assignments: list[Assignment] = []

    eligible_matches = (match for match in matches if match.eligible)
    for match in sorted(eligible_matches, key=rank_key, reverse=True):
        if match.responder_id not in budgets:
            continue
        if responder_load[match.responder_id] >= budgets[match.responder_id]:
            continue
        if intent_load[match.intent_id] >= max_responders_per_intent:
            continue

        assignments.append(
            Assignment(match.intent_id, match.responder_id, rank_key(match))
        )
        responder_load[match.responder_id] += 1
        intent_load[match.intent_id] += 1

    return assignments


def random_capacity(
    matches: Iterable[CandidateMatch],
    responders: Iterable[Responder],
    *,
    seed: int = 7,
    max_responders_per_intent: int = 1,
) -> list[Assignment]:
    shuffled = [match for match in matches if match.eligible]
    random.Random(seed).shuffle(shuffled)
    order = {id(match): len(shuffled) - index for index, match in enumerate(shuffled)}
    return _capacity_greedy(
        shuffled,
        responders,
        rank_key=lambda match: float(order[id(match)]),
        max_responders_per_intent=max_responders_per_intent,
    )


def topic_capacity(
    matches: Iterable[CandidateMatch],
    responders: Iterable[Responder],
    *,
    max_responders_per_intent: int = 1,
) -> list[Assignment]:
    return _capacity_greedy(
        matches,
        responders,
        rank_key=lambda match: match.topic_relevance,
        max_responders_per_intent=max_responders_per_intent,
    )


def unconstrained_best_match(
    matches: Iterable[CandidateMatch],
) -> list[Assignment]:
    best_by_intent: dict[str, CandidateMatch] = {}
    for match in matches:
        if not match.eligible:
            continue
        previous = best_by_intent.get(match.intent_id)
        if previous is None or pair_score(match) > pair_score(previous):
            best_by_intent[match.intent_id] = match

    return [
        Assignment(match.intent_id, match.responder_id, pair_score(match))
        for match in best_by_intent.values()
    ]
