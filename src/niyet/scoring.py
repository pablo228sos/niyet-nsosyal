from __future__ import annotations

from .types import CandidateMatch


def pair_score(match: CandidateMatch) -> float:
    """Score one candidate edge before capacity constraints are applied."""
    values = (
        match.topic_relevance,
        match.willingness,
        match.response_probability,
    )
    if any(value < 0 or value > 1 for value in values):
        raise ValueError("match scores must be between 0 and 1")

    return (
        0.45 * match.topic_relevance
        + 0.25 * match.willingness
        + 0.30 * match.response_probability
    )
