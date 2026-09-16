from dataclasses import replace
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

    def route_many(self, requests, *, responder_state=None, **kwargs):
        state = {
            key: dict(value)
            for key, value in (responder_state or self.default_responder_state()).items()
        }
        decisions = []
        for request in requests:
            decision = self.route(
                request["text"],
                intent_override=request.get("intent_override"),
                responder_state=state,
                exclude_responder_ids=request.get("exclude_responder_ids", ()),
            )
            decision = replace(decision, request_id=request["id"])
            decisions.append(decision)
            if decision.responder_id:
                current = state[decision.responder_id]
                current["remaining_slots"] -= 1
                if current["remaining_slots"] <= 0:
                    current["active"] = False
        return decisions


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

    with pytest.raises(ValueError, match="invalid_author_token"):
        service.status(request.request_id, "wrong-token")


def test_skip_reallocates_without_consuming_skipped_responder_capacity():
    service = build_service()
    request = service.open_request("I need help")
    before = service.responder_state()["r_one"]["remaining_slots"]

    updated = service.skip(request.request_id, "r_one")

    assert service.responder_state()["r_one"]["remaining_slots"] == before
    assert updated["assigned_responder"]["id"] == "r_two"


def test_pause_rebalances_an_already_open_request():
    service = build_service()
    request = service.open_request("I need help")
    assert request.assigned_responder_id == "r_one"

    service.set_responder_active("r_one", False)

    author_view = service.status(request.request_id, request.author_token)
    assert author_view["assigned_responder"]["id"] == "r_two"
    assert service.responder_state()["r_one"]["active"] is False


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
        social_context={
            "platform": "NSosyal",
            "post_url": "https://nsosyal.com/home",
            "published_observed": True,
        },
    )

    service.accept(request.request_id, "r_one")
    service.answer(request.request_id, "r_one", "Association does not establish causation.")

    author_view = service.status(request.request_id, request.author_token)
    assert author_view["evidence_context"] == evidence
    assert author_view["social_context"]["published_observed"] is True
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


def test_pending_window_never_overbooks_responder_capacity():
    service = build_service()
    requests = [
        service.open_request("First request"),
        service.open_request("Second request"),
        service.open_request("Third request"),
        service.open_request("Fourth request"),
    ]

    assignments = [
        service.status(request.request_id, request.author_token)["assigned_responder"]
        for request in requests
    ]
    assigned_ids = [item["id"] for item in assignments if item is not None]

    assert assigned_ids.count("r_one") == 2
    assert assigned_ids.count("r_two") == 1
    assert len(assigned_ids) == 3
    assert assignments[3] is None


def test_accept_rebalances_remaining_pending_requests_after_capacity_changes():
    service = build_service()
    first = service.open_request("First request")
    second = service.open_request("Second request")
    third = service.open_request("Third request")
    fourth = service.open_request("Fourth request")

    service.accept(first.request_id, "r_one")

    second_view = service.status(second.request_id, second.author_token)
    third_view = service.status(third.request_id, third.author_token)
    fourth_view = service.status(fourth.request_id, fourth.author_token)

    assert second_view["assigned_responder"]["id"] == "r_one"
    assert third_view["assigned_responder"]["id"] == "r_two"
    assert fourth_view["assigned_responder"] is None

    service.accept(second.request_id, "r_one")
    with pytest.raises(ValueError, match="request_not_assigned"):
        service.accept(fourth.request_id, "r_one")


def test_resume_reconsiders_previously_unmatched_request():
    service = build_service()
    service.set_responder_active("r_one", False)
    service.set_responder_active("r_two", False)
    request = service.open_request("Waiting request")

    assert request.status is HumanRequestStatus.UNMATCHED

    service.set_responder_active("r_two", True)
    updated = service.status(request.request_id, request.author_token)

    assert updated["status"] == HumanRequestStatus.OPEN.value
    assert updated["assigned_responder"]["id"] == "r_two"


def test_open_from_routing_preserves_structured_context_for_future_reallocation():
    runtime = StubRuntime()
    store = MemoryStateStore(
        {"requests": {}, "responder_state": runtime.default_responder_state()}
    )
    service = HumanHelpService(runtime, store=store)
    routing_text = "topic: research\nclaim: X\nevidence_status: INSUFFICIENT"

    request = service.open_from_routing(
        "Visible user wording",
        {"routing_text": routing_text, "responder_id": "r_one"},
    )

    stored = store.read()["requests"][request.request_id]
    assert stored["display_text"] == "Visible user wording"
    assert stored["routing_text"] == routing_text
