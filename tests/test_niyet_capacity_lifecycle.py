from __future__ import annotations

from drsk.firebase_auth import AuthenticatedUser
from drsk.niyet_persistence import MemoryNiyetRepository, NiyetService


def actor(uid: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        uid=uid,
        email=f"{uid}@example.test",
        display_name=uid.title(),
        photo_url=None,
        provider_ids=("password",),
        claims={"uid": uid},
    )


def configure_responder(service: NiyetService, uid: str, *, capacity: int = 1) -> None:
    service.sync_user(actor(uid))
    service.update_responder_profile(
        actor(uid),
        {
            "topics": ["python", "backend"],
            "languages": ["en"],
            "willing": True,
            "active": True,
            "capacity_total": capacity,
        },
    )


def test_answer_releases_capacity_and_allocates_waiting_request() -> None:
    repository = MemoryNiyetRepository()
    service = NiyetService(repository)
    service.sync_user(actor("author-a"))
    service.sync_user(actor("author-b"))
    configure_responder(service, "responder", capacity=1)

    first = service.create_request(
        actor("author-a"),
        text="Need Python backend help",
        intent="ask",
    )
    first_assignment_id = first["current_assignment_id"]
    assert first_assignment_id

    service.accept(actor("responder"), first_assignment_id)
    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 0

    second = service.create_request(
        actor("author-b"),
        text="Need Python backend review",
        intent="ask",
    )
    assert second["current_assignment_id"] is None

    service.answer(actor("responder"), first_assignment_id, "Use a transaction.")

    profile = service.get_responder_profile(actor("responder"))
    assert profile["capacity_remaining"] == 1

    refreshed_second = repository.get_request(second["id"])
    assert refreshed_second is not None
    assert refreshed_second["current_assignment_id"] is not None
    replacement = repository.get_assignment(refreshed_second["current_assignment_id"])
    assert replacement is not None
    assert replacement["responder_uid"] == "responder"
    assert replacement["status"] == "PENDING"

    # Retrying the same answer is idempotent: it must not release the slot twice.
    service.answer(actor("responder"), first_assignment_id, "Use a transaction.")
    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 1
