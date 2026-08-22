from niyet.baselines import random_capacity, topic_capacity, unconstrained_best_match
from niyet.types import CandidateMatch, IntentType, Responder


def test_topic_capacity_respects_budget():
    responders = [Responder("r1", ("python",), (IntentType.ASK,), 1)]
    matches = [
        CandidateMatch("i1", "r1", 0.9, 1.0, 1.0),
        CandidateMatch("i2", "r1", 0.8, 1.0, 1.0),
    ]

    result = topic_capacity(matches, responders)

    assert len(result) == 1
    assert result[0].intent_id == "i1"


def test_random_capacity_is_repeatable():
    responders = [
        Responder("r1", ("python",), (IntentType.ASK,), 1),
        Responder("r2", ("python",), (IntentType.ASK,), 1),
    ]
    matches = [
        CandidateMatch("i1", "r1", 0.9, 1.0, 1.0),
        CandidateMatch("i1", "r2", 0.8, 1.0, 1.0),
        CandidateMatch("i2", "r1", 0.7, 1.0, 1.0),
        CandidateMatch("i2", "r2", 0.6, 1.0, 1.0),
    ]

    assert random_capacity(matches, responders, seed=4) == random_capacity(
        matches, responders, seed=4
    )


def test_unconstrained_best_match_can_overload_responder():
    matches = [
        CandidateMatch("i1", "r1", 0.9, 1.0, 1.0),
        CandidateMatch("i2", "r1", 0.8, 1.0, 1.0),
        CandidateMatch("i2", "r2", 0.7, 1.0, 1.0),
    ]

    result = unconstrained_best_match(matches)

    assert [item.responder_id for item in result] == ["r1", "r1"]
