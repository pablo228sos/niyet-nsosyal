from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .scoring import pair_score
from .types import CandidateMatch, Responder


@dataclass(frozen=True)
class Assignment:
    intent_id: str
    responder_id: str
    score: float


def allocate(
    matches: Iterable[CandidateMatch],
    responders: Iterable[Responder],
    *,
    max_responders_per_intent: int = 1,
) -> list[Assignment]:
    """Greedy capacity-aware baseline used by the first prototype."""
    budgets = {responder.id: responder.attention_budget for responder in responders}
    responder_load = defaultdict(int)
    intent_load = defaultdict(int)

    ranked = sorted(matches, key=pair_score, reverse=True)
    assignments: list[Assignment] = []

    for match in ranked:
        if match.responder_id not in budgets:
            continue
        if responder_load[match.responder_id] >= budgets[match.responder_id]:
            continue
        if intent_load[match.intent_id] >= max_responders_per_intent:
            continue

        assignments.append(
            Assignment(
                intent_id=match.intent_id,
                responder_id=match.responder_id,
                score=pair_score(match),
            )
        )
        responder_load[match.responder_id] += 1
        intent_load[match.intent_id] += 1

    return assignments
