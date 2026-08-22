from niyet.allocator import Assignment
from niyet.benchmark import LabeledMatch
from niyet.metrics import (
    gini,
    intent_coverage,
    mean_gold_relevance,
    overload_count,
    responder_load_gini,
)
from niyet.types import CandidateMatch, Intent, IntentType, Responder


def test_intent_coverage():
    intents = [
        Intent("i1", "u1", IntentType.ASK, "python", "help"),
        Intent("i2", "u2", IntentType.ASK, "robotics", "help"),
    ]
    assignments = [Assignment("i1", "r1", 0.9)]

    assert intent_coverage(assignments, intents) == 0.5


def test_mean_gold_relevance():
    assignments = [
        Assignment("i1", "r1", 0.9),
        Assignment("i2", "r2", 0.8),
    ]
    labels = [
        LabeledMatch(CandidateMatch("i1", "r1", 0.9, 1.0, 0.9), 3),
        LabeledMatch(CandidateMatch("i2", "r2", 0.8, 1.0, 0.8), 1),
    ]

    assert mean_gold_relevance(assignments, labels) == 2.0


def test_overload_and_load_gini():
    responders = [
        Responder("r1", ("python",), (IntentType.ASK,), 1),
        Responder("r2", ("python",), (IntentType.ASK,), 1),
    ]
    assignments = [
        Assignment("i1", "r1", 0.9),
        Assignment("i2", "r1", 0.8),
    ]

    assert overload_count(assignments, responders) == 1
    assert responder_load_gini(assignments, responders) == 0.5


def test_gini_is_zero_for_equal_or_empty_loads():
    assert gini([2, 2, 2]) == 0.0
    assert gini([]) == 0.0
