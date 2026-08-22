from __future__ import annotations

from collections.abc import Iterable

import numpy as np
from scipy.optimize import linear_sum_assignment

from .allocator import Assignment
from .scoring import pair_score
from .types import CandidateMatch, Responder


def global_allocate(
    matches: Iterable[CandidateMatch],
    responders: Iterable[Responder],
    *,
    min_score: float = 0.0,
) -> list[Assignment]:
    """Find the highest-utility assignment under responder attention budgets."""
    match_list = tuple(matches)
    responder_list = tuple(responders)

    intent_ids = tuple(dict.fromkeys(match.intent_id for match in match_list))
    if not intent_ids:
        return []

    slots = [
        (responder.id, slot_index)
        for responder in responder_list
        for slot_index in range(max(0, responder.attention_budget))
    ]

    pair_by_ids = {
        (match.intent_id, match.responder_id): match
        for match in match_list
    }

    real_slot_count = len(slots)
    dummy_count = len(intent_ids)
    utility = np.full(
        (len(intent_ids), real_slot_count + dummy_count),
        -1_000_000.0,
        dtype=float,
    )

    for row, intent_id in enumerate(intent_ids):
        for column, (responder_id, _) in enumerate(slots):
            match = pair_by_ids.get((intent_id, responder_id))
            if match is not None:
                utility[row, column] = pair_score(match)

        utility[row, real_slot_count:] = 0.0

    rows, columns = linear_sum_assignment(utility, maximize=True)

    assignments = []
    for row, column in zip(rows, columns, strict=True):
        if column >= real_slot_count:
            continue

        intent_id = intent_ids[row]
        responder_id = slots[column][0]
        match = pair_by_ids[(intent_id, responder_id)]
        score = pair_score(match)
        if score < min_score:
            continue

        assignments.append(Assignment(intent_id, responder_id, score))

    return assignments
