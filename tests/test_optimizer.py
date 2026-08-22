from niyet.allocator import allocate
from niyet.optimizer import global_allocate
from niyet.types import CandidateMatch, IntentType, Responder


def test_global_allocator_avoids_greedy_trap():
    responders = [
        Responder("r1", ("x",), (IntentType.ASK,), 1),
        Responder("r2", ("x",), (IntentType.ASK,), 1),
    ]
    matches = [
        CandidateMatch("i1", "r1", 0.99, 0.99, 0.99),
        CandidateMatch("i1", "r2", 0.98, 0.98, 0.98),
        CandidateMatch("i2", "r1", 0.97, 0.97, 0.97),
        CandidateMatch("i2", "r2", 0.10, 0.10, 0.10),
    ]

    greedy = allocate(matches, responders)
    global_result = global_allocate(matches, responders)

    greedy_total = sum(item.score for item in greedy)
    global_total = sum(item.score for item in global_result)

    assert global_total > greedy_total
    assert {(item.intent_id, item.responder_id) for item in global_result} == {
        ("i1", "r2"),
        ("i2", "r1"),
    }


def test_global_allocator_respects_attention_budget():
    responders = [Responder("r1", ("x",), (IntentType.ASK,), 1)]
    matches = [
        CandidateMatch("i1", "r1", 0.9, 0.9, 0.9),
        CandidateMatch("i2", "r1", 0.8, 0.8, 0.8),
    ]

    result = global_allocate(matches, responders)

    assert len(result) == 1


def test_global_allocator_can_leave_low_quality_match_unassigned():
    responders = [Responder("r1", ("x",), (IntentType.ASK,), 1)]
    matches = [CandidateMatch("i1", "r1", 0.2, 0.2, 0.2)]

    result = global_allocate(matches, responders, min_score=0.5)

    assert result == []
