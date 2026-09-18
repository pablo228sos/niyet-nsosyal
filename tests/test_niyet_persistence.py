from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest

from drsk.firebase_auth import AuthenticatedUser
from drsk.niyet_persistence import DomainError, MemoryNiyetRepository, NiyetService


def actor(uid: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        uid=uid,
        email=f"{uid}@example.test",
        display_name=uid.title(),
        photo_url=None,
        provider_ids=("password",),
        claims={"uid": uid},
    )


@pytest.fixture
def repository() -> MemoryNiyetRepository:
    return MemoryNiyetRepository()


def configure_responder(service: NiyetService, uid: str, *, capacity: int = 2) -> None:
    service.sync_user(actor(uid))
    service.update_responder_profile(
        actor(uid),
        {
            "topics": ["python", "fastapi", "backend"],
            "languages": ["en"],
            "willing": True,
            "active": True,
            "capacity_total": capacity,
        },
    )


def test_request_assignment_accept_and_persistence_across_services(
    repository: MemoryNiyetRepository,
) -> None:
    first = NiyetService(repository)
    second = NiyetService(repository)
    first.sync_user(actor("author"))
    configure_responder(first, "responder", capacity=2)

    created = first.create_request(
        actor("author"),
        text="Can someone help with a Python FastAPI backend?",
        intent="ask",
    )
    inbox = second.list_inbox(actor("responder"))
    assert inbox[0]["request_id"] == created["request_id"]

    accepted = second.accept(actor("responder"), inbox[0]["assignment_id"])
    duplicate = first.accept(actor("responder"), inbox[0]["assignment_id"])
    assert accepted["status"] == "ACCEPTED"
    assert duplicate["status"] == "ACCEPTED"
    assert second.get_responder_profile(actor("responder"))["capacity_remaining"] == 1


def test_concurrent_accept_cannot_oversubscribe_capacity(
    repository: MemoryNiyetRepository,
) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("author-a"))
    service.sync_user(actor("author-b"))
    configure_responder(service, "responder", capacity=1)

    first = service.create_request(actor("author-a"), text="Python backend review", intent="ask")
    # Simulate a stale second pending assignment to prove the accept transaction is the final guard.
    second_assignment = repository.force_pending_assignment(
        author_uid="author-b",
        responder_uid="responder",
        text="FastAPI architecture help",
    )
    assignment_ids = [first["current_assignment_id"], second_assignment]

    def accept_one(assignment_id: str) -> str:
        try:
            return service.accept(actor("responder"), assignment_id)["status"]
        except DomainError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(accept_one, assignment_ids))

    assert outcomes.count("ACCEPTED") == 1
    assert outcomes.count("capacity_exhausted") == 1
    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 0


def test_skip_pause_resume_and_actor_authorization(repository: MemoryNiyetRepository) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    configure_responder(service, "first", capacity=2)
    configure_responder(service, "second", capacity=2)

    created = service.create_request(actor("author"), text="Python FastAPI question", intent="ask")
    assignment = repository.get_assignment(created["current_assignment_id"])
    skipped_uid = assignment["responder_uid"]
    skipped = service.skip(actor(skipped_uid), assignment["id"])
    assert skipped["status"] == "SKIPPED"

    request = repository.get_request(created["request_id"])
    if request["current_assignment_id"]:
        replacement = repository.get_assignment(request["current_assignment_id"])
        assert replacement["responder_uid"] != skipped_uid
        assert any(event["type"] == "REALLOCATED" for event in repository.events.values())

    with pytest.raises(DomainError, match="permission_denied"):
        service.accept(actor("intruder"), assignment["id"])

    service.pause(actor("first"))
    assert service.get_responder_profile(actor("first"))["paused"] is True
    service.resume(actor("first"))
    assert service.get_responder_profile(actor("first"))["paused"] is False


def test_capacity_cannot_be_negative(repository: MemoryNiyetRepository) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    configure_responder(service, "responder", capacity=1)
    created = service.create_request(actor("author"), text="Python backend help", intent="ask")
    assignment_id = created["current_assignment_id"]
    service.accept(actor("responder"), assignment_id)
    service.accept(actor("responder"), assignment_id)
    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 0


def test_authenticated_user_cannot_create_as_payload_uid(repository: MemoryNiyetRepository) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("real-user"))
    created = service.create_request(
        actor("real-user"),
        text="Need a Python reviewer",
        intent="ask",
        untrusted_author_uid="other-user",
    )
    assert repository.get_request(created["request_id"])["author_uid"] == "real-user"


def test_create_is_idempotent_for_verified_actor_and_operation_key(
    repository: MemoryNiyetRepository,
) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    key = "request-operation-0001"
    first = service.create_request(actor("author"), text="Need Python help", intent="ask", idempotency_key=key)
    second = service.create_request(actor("author"), text="Need Python help", intent="ask", idempotency_key=key)

    assert first["id"] == second["id"]
    assert len(repository.requests) == 1
    assert len(repository.posts) == 1


def test_answer_is_owned_atomic_persistent_and_idempotent(
    repository: MemoryNiyetRepository,
) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    configure_responder(service, "responder")
    request = service.create_request(actor("author"), text="Python backend help", intent="ask")
    assignment_id = request["current_assignment_id"]
    service.accept(actor("responder"), assignment_id)

    with pytest.raises(DomainError, match="permission_denied"):
        service.answer(actor("intruder"), assignment_id, "Unsafe answer")

    first = service.answer(actor("responder"), assignment_id, "Use a transaction.")
    duplicate = service.answer(actor("responder"), assignment_id, "Use a transaction.")
    assert first["status"] == duplicate["status"] == "ANSWERED"
    saved = service.get_author_request(actor("author"), request["id"])
    assert saved["status"] == "ANSWERED"
    assert saved["answer"] == "Use a transaction."
    assert repository.posts[saved["post_id"]]["resolution"]["assignment_id"] == assignment_id

    with pytest.raises(DomainError, match="answer_already_submitted"):
        service.answer(actor("responder"), assignment_id, "Replace the answer")


def test_pause_releases_pending_assignment_and_reallocates(
    repository: MemoryNiyetRepository,
) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    configure_responder(service, "first")
    configure_responder(service, "second")
    request = service.create_request(actor("author"), text="Python backend help", intent="ask")
    old_assignment = repository.get_assignment(request["current_assignment_id"])

    service.pause(actor(old_assignment["responder_uid"]))

    assert repository.get_assignment(old_assignment["id"])["status"] == "CANCELLED"
    refreshed = repository.get_request(request["id"])
    replacement = repository.get_assignment(refreshed["current_assignment_id"])
    assert replacement["responder_uid"] != old_assignment["responder_uid"]
    assert repository.get_profile(old_assignment["responder_uid"])["pending_assignments"] == 0


def test_profile_cannot_override_derived_capacity_and_ineligible_profile_releases_pending(
    repository: MemoryNiyetRepository,
) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    configure_responder(service, "responder", capacity=2)
    request = service.create_request(actor("author"), text="Python backend help", intent="ask")
    assignment_id = request["current_assignment_id"]

    profile = service.update_responder_profile(actor("responder"), {
        "topics": ["python"], "languages": ["en"], "willing": False,
        "active": True, "capacity_total": 2,
        "capacity_remaining": 99, "pending_assignments": 99,
    })

    assert profile["capacity_remaining"] == 2
    assert profile["pending_assignments"] == 0
    assert repository.get_assignment(assignment_id)["status"] == "CANCELLED"


def test_expired_assignment_is_released_before_accept(
    repository: MemoryNiyetRepository,
) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    configure_responder(service, "responder")
    request = service.create_request(actor("author"), text="Python backend help", intent="ask")
    assignment_id = request["current_assignment_id"]
    repository.assignments[assignment_id]["expires_at"] = repository.assignments[assignment_id]["created_at"] - timedelta(seconds=1)

    with pytest.raises(DomainError, match="stale_assignment"):
        service.accept(actor("responder"), assignment_id)
    assert repository.get_assignment(assignment_id)["status"] == "EXPIRED"
    assert repository.get_profile("responder")["pending_assignments"] == 0
    refreshed = repository.get_request(request["id"])
    assert refreshed["current_assignment_id"] is None
    assert "responder" in refreshed["excluded_responder_ids"]


def test_profile_rejects_non_string_topics_and_nonfinite_quality(
    repository: MemoryNiyetRepository,
) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("responder"))
    base = {
        "topics": ["python"], "languages": ["en"], "willing": True,
        "active": True, "capacity_total": 1,
    }
    with pytest.raises(DomainError, match="invalid_topics"):
        service.update_responder_profile(actor("responder"), {**base, "topics": [{"admin": True}]})
    with pytest.raises(DomainError, match="invalid_quality_threshold"):
        service.update_responder_profile(actor("responder"), {**base, "quality_threshold": float("nan")})


def test_idempotency_key_cannot_be_reused_for_different_request_payload(
    repository: MemoryNiyetRepository,
) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    key = "request-operation-0002"
    service.create_request(actor("author"), text="First request", intent="ask", idempotency_key=key)

    with pytest.raises(DomainError, match="idempotency_conflict"):
        service.create_request(actor("author"), text="Different request", intent="ask", idempotency_key=key)


def test_author_refresh_expires_stale_assignment_and_reallocates(
    repository: MemoryNiyetRepository,
) -> None:
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    configure_responder(service, "first")
    configure_responder(service, "second")
    request = service.create_request(actor("author"), text="Python backend help", intent="ask")
    old_assignment = repository.get_assignment(request["current_assignment_id"])
    repository.assignments[old_assignment["id"]]["expires_at"] = (
        repository.assignments[old_assignment["id"]]["created_at"] - timedelta(seconds=1)
    )

    refreshed = service.get_author_request(actor("author"), request["id"])

    assert repository.get_assignment(old_assignment["id"])["status"] == "EXPIRED"
    assert refreshed["current_assignment_id"] != old_assignment["id"]
    if refreshed["current_assignment_id"]:
        replacement = repository.get_assignment(refreshed["current_assignment_id"])
        assert replacement["responder_uid"] != old_assignment["responder_uid"]
