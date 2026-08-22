from niyet.allocator import allocate
from niyet.types import CandidateMatch, IntentType, Responder


def test_respects_attention_budget():
    responders = [
        Responder(
            id="r1",
            topics=("robotics",),
            willing_intents=(IntentType.ASK,),
            attention_budget=1,
        )
    ]
    matches = [
        CandidateMatch("i1", "r1", 0.95, 1.0, 0.9),
        CandidateMatch("i2", "r1", 0.90, 1.0, 0.9),
    ]

    result = allocate(matches, responders)

    assert len(result) == 1
    assert result[0].intent_id == "i1"


def test_one_responder_per_intent_by_default():
    responders = [
        Responder("r1", ("robotics",), (IntentType.ASK,), 1),
        Responder("r2", ("robotics",), (IntentType.ASK,), 1),
    ]
    matches = [
        CandidateMatch("i1", "r1", 0.95, 1.0, 0.9),
        CandidateMatch("i1", "r2", 0.90, 1.0, 0.9),
    ]

    result = allocate(matches, responders)

    assert len(result) == 1
    assert result[0].responder_id == "r1"
