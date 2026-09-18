from __future__ import annotations

import os

import pytest

from drsk.firebase_auth import AuthenticatedUser
from drsk.niyet_persistence import FirestoreNiyetRepository, NiyetService


pytestmark = pytest.mark.skipif(
    not os.getenv("FIRESTORE_EMULATOR_HOST"),
    reason="start Firebase Emulator Suite and set FIRESTORE_EMULATOR_HOST",
)


def actor(uid: str) -> AuthenticatedUser:
    return AuthenticatedUser(uid, f"{uid}@example.test", uid, None, ("password",), {"uid": uid})


@pytest.fixture
def firestore_client():
    pytest.importorskip("firebase_admin")
    from google.auth.credentials import AnonymousCredentials
    from google.cloud import firestore

    client = firestore.Client(project="drsk-web-test", credentials=AnonymousCredentials())
    collections = ("events", "assignments", "niyet_requests", "posts", "responder_profiles", "users")
    for collection in collections:
        for snapshot in client.collection(collection).stream():
            snapshot.reference.delete()
    yield client
    for collection in collections:
        for snapshot in client.collection(collection).stream():
            snapshot.reference.delete()


def test_firestore_crud_assignment_and_idempotent_accept(firestore_client) -> None:
    service = NiyetService(FirestoreNiyetRepository(firestore_client))
    service.sync_user(actor("author"))
    service.sync_user(actor("responder"))
    service.update_responder_profile(
        actor("responder"),
        {"topics": ["python", "backend"], "languages": ["en"], "willing": True, "active": True, "capacity_total": 2},
    )
    request = service.create_request(actor("author"), text="Python backend help", intent="ask")
    assignment_id = request["current_assignment_id"]
    assert assignment_id
    service.accept(actor("responder"), assignment_id)
    service.accept(actor("responder"), assignment_id)
    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 1
    service.answer(actor("responder"), assignment_id, "Persisted answer")
    service.answer(actor("responder"), assignment_id, "Persisted answer")
    saved = service.get_author_request(actor("author"), request["id"])
    assert saved["status"] == "ANSWERED"
    assert saved["answer"] == "Persisted answer"
    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 2


def test_firestore_pause_releases_and_reallocates_pending_assignment(firestore_client) -> None:
    service = NiyetService(FirestoreNiyetRepository(firestore_client))
    service.sync_user(actor("author"))
    for uid in ("first", "second"):
        service.sync_user(actor(uid))
        service.update_responder_profile(
            actor(uid),
            {"topics": ["python"], "languages": ["en"], "willing": True, "active": True, "capacity_total": 2},
        )
    request = service.create_request(actor("author"), text="Python help", intent="ask")
    old = service.repository.get_assignment(request["current_assignment_id"])
    service.pause(actor(old["responder_uid"]))
    refreshed = service.repository.get_request(request["id"])
    replacement = service.repository.get_assignment(refreshed["current_assignment_id"])
    assert service.repository.get_assignment(old["id"])["status"] == "CANCELLED"
    assert replacement["responder_uid"] != old["responder_uid"]
