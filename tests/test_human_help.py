from types import SimpleNamespace

import pytest

from drsk.human_help import HumanHelpService, HumanRequestStatus
from drsk.state_store import MemoryStateStore
from niyet.runtime import RouteDecision


class StubRuntime:
    def __init__(self) -> None:
        self.responder_by_id = {
            "r_one": SimpleNamespace(),
            "r_two": SimpleNamespace(),
        }

    def default_responder_state(self):
        return {
            "r_one": {"remaining_slots": 2, "active": True},
            "r_two": {"remaining_slots": 1, "active": True},
        }

    def update_responder_state(self, state, responder_id, *, action):
        next_state = {key: dict(value) for key, value in state.items()}
        if responder_id not in next_state:
            raise ValueError("unknown_responder")
        current = next_state[responder_id]
        if action == "accept":
            current["remaining_slots"] = max(0, current["remaining_slots"] - 1)
            current["active"] = current["active"] and current["remaining_slots"] > 0
        elif action == "pause":
            current["active"] = False
        elif action == "resume":
            current["active"] = current["remaining_slots"] > 0
        else:
            raise ValueError("invalid_state_action")
        return next_state

    def route(
        self,
        text,
        *,
        intent_override=None,
        responder_state=None,
        exclude_responder_ids=(),
        **kwargs,
    ):
        state = responder_state or self.default_responder_state()
        for responder_id, name in (("r_one", "Responder One"), ("r_two", "Responder Two")):
            if responder_id in exclude_responder_ids:
                continue
            if state[responder_id]["active"] and state[responder_id]["remaining_slots"] > 0:
                return RouteDecision(
                    response_needed=True,
                    intent="ask",
                    responder_id=responder_id,
                    responder_name=name,
                    reason=("topic_match", "available_now"),
                    development_utility=0.8,
                    retrieval_similarity=0.7,
                    request_id="stub-route",
                )
        return RouteDecision(
            response_needed=True,
            intent="ask",
            responder_id=None,
            responder_name=None,
            reason=("no_eligible_responder",),
            development_utility=None,
            retrieval_similarity=None,
            request_id="stub-route",
        )


def build_service() -> HumanHelpService:
    return HumanHelpService(StubRuntime())


def test_open_request_is_visible_in_assigned_responder_inbox():
    service = build_service()
    request = service.open_request("I need help with this question")

    assert request.status is HumanRequestStatus.OPEN
    assert request.assigned_responder_id == "r_one"
    inbox = service.inbox("r_one")
    assert [item["request_id"] for item in inbox] == [request.request_id]
    assert "author_token" not in inbox[0]


def test_accept_consumes_server_side_capacity_and_answer_reaches_author():
    service = build_service()
    request = service.open_request("I need help with this question")
    before = service.responder_state()["r_one"]["remaining_slots"]

    accepted = service.accept(request.request_id, "r_one")
    assert accepted["status"] == HumanRequestStatus.ACCEPTED.value
    assert service.responder_state()["r_one"]["remaining_slots"] == before - 1

    answered = service.answer(request.request_id, "r_one", "Here is a grounded answer.")
    assert answered["status"] == HumanRequestStatus.ANSWERED.value

    author_view = service.status(request.request_id, request.author_token)
    assert author_view["answer"] == "Here is a grounded answer."


def test_author_status_requires_unpredictable_token():
    service = build_service()
    request = service.open_request("I need help")

    try:
        service.status(request.request_id, "wrong-token")
    except ValueError as exc:
        assert str(exc) == "invalid_author_token"
    else:
        raise AssertionError("wrong author token unexpectedly accepted")


def test_skip_reallocates_without_consuming_skipped_responder_capacity():
    service = build_service()
    request = service.open_request("I need help")
    before = service.responder_state()["r_one"]["remaining_slots"]

    updated = service.skip(request.request_id, "r_one")

    assert service.responder_state()["r_one"]["remaining_slots"] == before
    assert updated["assigned_responder"]["id"] == "r_two"


def test_pause_changes_authoritative_availability_for_later_routes():
    service = build_service()
    service.set_responder_active("r_one", False)

    assert service.responder_state()["r_one"]["active"] is False
    request = service.open_request("I need help")
    assert request.assigned_responder_id == "r_two"


def test_evidence_context_survives_human_resolution_lifecycle():
    service = build_service()
    evidence = {
        "status": "CONFLICTING",
        "evidence": [
            {
                "source_title": "Example study",
                "passage": "X was associated with Y.",
                "relation": "CONFLICTING",
                "distortions": ["CAUSALITY_SHIFT"],
            }
        ],
    }
    request = service.open_request(
        "The study proves X causes Y.",
        routing_text="research statistics causality evidence review",
        evidence_context=evidence,
    )

    service.accept(request.request_id, "r_one")
    service.answer(request.request_id, "r_one", "Association does not establish causation.")

    author_view = service.status(request.request_id, request.author_token)
    assert author_view["evidence_context"] == evidence
    assert author_view["answer"] == "Association does not establish causation."


def test_two_service_instances_observe_one_shared_store():
    runtime = StubRuntime()
    store = MemoryStateStore(
        {"requests": {}, "responder_state": runtime.default_responder_state()}
    )
    author_service = HumanHelpService(runtime, store=store)
    responder_service = HumanHelpService(runtime, store=store)

    request = author_service.open_request("I need help across two instances")
    inbox = responder_service.inbox("r_one")

    assert [item["request_id"] for item in inbox] == [request.request_id]
    responder_service.accept(request.request_id, "r_one")
    responder_service.answer(request.request_id, "r_one", "Shared state works.")
    assert author_service.status(request.request_id, request.author_token)["answer"] == "Shared state works."


def test_accept_rejects_stale_open_request_after_capacity_is_exhausted():
    service = build_service()
    first = service.open_request("First request")
    second = service.open_request("Second request")
    stale = service.open_request("Third request")

    assert first.assigned_responder_id == second.assigned_responder_id == stale.assigned_responder_id == "r_one"
    service.accept(first.request_id, "r_one")
    service.accept(second.request_id, "r_one")

    with pytest.raises(ValueError, match="responder_capacity_exhausted"):
        service.accept(stale.request_id, "r_one")
