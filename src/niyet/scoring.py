from __future__ import annotations

from .types import CandidateMatch


def pair_score(match: CandidateMatch) -> float:
    """Return the current development utility for one eligible edge.

    Willingness is enforced before ranking. For candidates that reach this
    function, willingness is therefore a hard compatibility constraint rather
    than a useful ranking signal. The current utility averages topical
    relevance and remaining availability. These are transparent development
    signals, not learned production weights or calibrated probabilities.
    """
    values = (
        match.topic_relevance,
        match.availability,
    )
    if any(value < 0 or value > 1 for value in values):
        raise ValueError("match scores must be between 0 and 1")
    if not 0 <= match.willingness <= 1:
        raise ValueError("willingness must be between 0 and 1")

    return sum(values) / len(values)
