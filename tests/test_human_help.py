from drsk.human_help import HumanHelpService, HumanRequestStatus
from niyet.runtime import NiyetRuntime


def build_service() -> HumanHelpService:
    return HumanHelpService(NiyetRuntime())


def test_open_request_is_visible_in_assigned_responder_inbox():
    service = build_service()

    request = service.open_request("PID ayarı için nereden başlamalıyım?")

    assert request.status is HumanRequestStatus.OPEN
    assert request.assigned_responder_id is not None
    inbox = service.inbox(request.assigned_responder_id)
    assert [item["request_id"] for item in inbox] == [request.request_id]
    assert "author_token" not in inbox[0]


def test_accept_consumes_server_side_capacity_and_answer_reaches_author():
    service = build_service()
    request = service.open_request("PID ayarı için nereden başlamalıyım?")
    responder_id = request.assigned_responder_id
    assert responder_id is not None
    before = service.responder_state()[responder_id]["remaining_slots"]

    accepted = service.accept(request.request_id, responder_id)
    assert accepted["status"] == HumanRequestStatus.ACCEPTED.value
    assert service.responder_state()[responder_id]["remaining_slots"] == before - 1

    answered = service.answer(
        request.request_id,
        responder_id,
        "Önce P kazancını düşük bir I ve D ile ayarlayıp salınımı gözlemleyin.",
    )
    assert answered["status"] == HumanRequestStatus.ANSWERED.value

    author_view = service.status(request.request_id, request.author_token)
    assert author_view["answer"].startswith("Önce P kazancını")


def test_author_status_requires_unpredictable_token():
    service = build_service()
    request = service.open_request("Python API hatamı nasıl ayıklarım?")

    try:
        service.status(request.request_id, "wrong-token")
    except ValueError as exc:
        assert str(exc) == "invalid_author_token"
    else:
        raise AssertionError("wrong author token unexpectedly accepted")


def test_skip_reallocates_without_consuming_skipped_responder_capacity():
    service = build_service()
    request = service.open_request("Python API ve backend deployment konusunda yardım lazım")
    first_responder = request.assigned_responder_id
    assert first_responder is not None
    before = service.responder_state()[first_responder]["remaining_slots"]

    updated = service.skip(request.request_id, first_responder)

    assert service.responder_state()[first_responder]["remaining_slots"] == before
    assert updated["assigned_responder"] is None or (
        updated["assigned_responder"]["id"] != first_responder
    )


def test_pause_changes_authoritative_availability_for_later_routes():
    service = build_service()
    service.set_responder_active("r_control", False)

    assert service.responder_state()["r_control"]["active"] is False

    request = service.open_request("PID control robot motor salınımını nasıl azaltırım?")
    assert request.assigned_responder_id != "r_control"


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

    responder_id = request.assigned_responder_id
    assert responder_id is not None
    service.accept(request.request_id, responder_id)
    service.answer(request.request_id, responder_id, "Association does not establish causation.")

    author_view = service.status(request.request_id, request.author_token)
    assert author_view["evidence_context"] == evidence
    assert author_view["answer"] == "Association does not establish causation."
