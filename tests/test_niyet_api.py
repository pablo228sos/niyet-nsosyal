from __future__ import annotations

import pytest

from api.niyet import _parse_json, _social_context, dispatch_get, dispatch_post
from drsk.firebase_auth import AuthenticatedUser
from drsk.niyet_persistence import DomainError, MemoryNiyetRepository, NiyetService


def actor(uid: str) -> AuthenticatedUser:
    return AuthenticatedUser(uid, f"{uid}@example.test", uid, None, ("password",), {"uid": uid})


def test_api_ignores_payload_author_uid() -> None:
    repository = MemoryNiyetRepository()
    service = NiyetService(repository)
    result = dispatch_post(
        {"action": "create_request", "text": "Need Python help", "intent": "ask", "author_uid": "victim"},
        actor("verified"),
        service,
    )
    assert result["request"]["author_uid"] == "verified"


def test_request_status_is_private_to_author() -> None:
    repository = MemoryNiyetRepository()
    service = NiyetService(repository)
    created = dispatch_post(
        {"action": "create_request", "text": "Need Python help", "intent": "ask"},
        actor("author"),
        service,
    )["request"]
    with pytest.raises(DomainError, match="permission_denied"):
        dispatch_get("request", actor("intruder"), service, {"request_id": [created["id"]]})


def test_api_persists_answer_only_for_verified_assignee() -> None:
    repository = MemoryNiyetRepository()
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    service.sync_user(actor("responder"))
    service.update_responder_profile(actor("responder"), {
        "topics": ["python"], "languages": ["en"], "willing": True,
        "active": True, "capacity_total": 1,
    })
    created = dispatch_post(
        {"action": "create_request", "text": "Python help", "intent": "ask", "idempotency_key": "api-operation-0001"},
        actor("author"), service,
    )["request"]
    assignment_id = created["current_assignment_id"]
    dispatch_post({"action": "accept", "assignment_id": assignment_id}, actor("responder"), service)

    with pytest.raises(DomainError, match="permission_denied"):
        dispatch_post({"action": "answer", "assignment_id": assignment_id, "answer": "No"}, actor("intruder"), service)
    dispatch_post({"action": "answer", "assignment_id": assignment_id, "answer": "Use transactions."}, actor("responder"), service)
    saved = dispatch_get("request", actor("author"), service, {"request_id": [created["id"]]})["request"]
    assert saved["status"] == "ANSWERED"
    assert saved["answer"] == "Use transactions."


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"value":NaN}'])
def test_api_rejects_ambiguous_or_nonfinite_json(raw: bytes) -> None:
    with pytest.raises(ValueError):
        _parse_json(raw)


@pytest.mark.parametrize(
    "url",
    [
        "http://nsosyal.com/post/1",
        "https://user@nsosyal.com/post/1",
        "https://nsosyal.com:444/post/1",
        "https://evil.example/post/1",
    ],
)
def test_social_context_accepts_only_canonical_nsosyal_https_urls(url: str) -> None:
    with pytest.raises(DomainError, match="invalid_post_url"):
        _social_context({"post_url": url})


def test_read_paths_do_not_rewrite_user_identity_on_poll() -> None:
    repository = MemoryNiyetRepository()
    service = NiyetService(repository)
    service.sync_user(actor("reader"))

    def unexpected_sync(_: AuthenticatedUser) -> dict:
        raise AssertionError("GET polling must not perform a user write")

    service.sync_user = unexpected_sync  # type: ignore[method-assign]
    result = dispatch_get("me", actor("reader"), service, {})
    assert result["user"]["uid"] == "reader"
