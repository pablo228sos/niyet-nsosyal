from niyet.allocator import allocate
from niyet.optimizer import global_allocate
from niyet.types import CandidateMatch, IntentType, Responder


def test_ineligible_match_is_never_assigned():
    responders = [Responder("r1", ("robotics",), (IntentType.ASK,), 1)]
    matches = [CandidateMatch("i1", "r1", 1.0, 1.0, 1.0, eligible=False)]

    assert allocate(matches, responders) == []
    assert global_allocate(matches, responders) == []


def test_inactive_responder_has_no_routing_capacity():
    responders = [
        Responder(
            "r1",
            ("robotics",),
            (IntentType.ASK,),
            attention_budget=5,
            active=False,
        )
    ]
    matches = [CandidateMatch("i1", "r1", 1.0, 1.0, 1.0)]

    assert allocate(matches, responders) == []
    assert global_allocate(matches, responders) == []
