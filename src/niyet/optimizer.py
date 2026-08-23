from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from scipy.optimize import linear_sum_assignment

from .allocator import Assignment
from .scoring import pair_score
from .types import CandidateMatch, Responder


_INVALID_UTILITY = -1_000_000.0


def global_allocate(
    matches: Iterable[CandidateMatch],
    responders: Iterable[Responder],
    *,
    min_score: float = 0.0,
) -> list[Assignment]:
    """Find the highest-utility valid assignment under attention budgets."""
    if not 0.0 <= min_score <= 1.0:
        raise ValueError("min_score must be between 0 and 1")

    responder_list = tuple(responder for responder in responders if responder.active)
    active_responder_ids = {responder.id for responder in responder_list}

    scored_matches: list[tuple[CandidateMatch, float]] = []
    for match in matches:
        if not match.eligible or match.responder_id not in active_responder_ids:
            continue
        score = pair_score(match)
        if score >= min_score:
            scored_matches.append((match, score))

    intent_ids = tuple(dict.fromkeys(match.intent_id for match, _ in scored_matches))
    if not intent_ids:
        return []

    slots = [
        (responder.id, slot_index)
        for responder in responder_list
        for slot_index in range(max(0, responder.attention_budget))
    ]

    if not slots:
        return []

    pair_by_ids: dict[tuple[str, str], tuple[CandidateMatch, float]] = {}
    for match, score in scored_matches:
        key = (match.intent_id, match.responder_id)
        previous = pair_by_ids.get(key)
        if previous is None or score > previous[1]:
            pair_by_ids[key] = (match, score)

    real_slot_count = len(slots)
    dummy_count = len(intent_ids)
    utility = np.full(
        (len(intent_ids), real_slot_count + dummy_count),
        _INVALID_UTILITY,
        dtype=float,
    )

    for row, intent_id in enumerate(intent_ids):
        for column, (responder_id, _) in enumerate(slots):
            item = pair_by_ids.get((intent_id, responder_id))
            if item is not None:
                utility[row, column] = item[1]

        # One zero-utility dummy option per intent lets the solver leave an
        # intent unmatched instead of forcing an invalid or weak assignment.
        utility[row, real_slot_count:] = 0.0

    rows, columns = linear_sum_assignment(utility, maximize=True)

    assignments: list[Assignment] = []
    for row, column in zip(rows, columns, strict=True):
        if column >= real_slot_count:
            continue

        intent_id = intent_ids[row]
        responder_id = slots[column][0]
        item = pair_by_ids.get((intent_id, responder_id))
        if item is None:
            continue

        assignments.append(Assignment(intent_id, responder_id, item[1]))

    return assignments
