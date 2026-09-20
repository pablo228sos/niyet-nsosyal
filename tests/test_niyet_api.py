from __future__ import annotations

import logging
from io import BytesIO

import pytest

import api.niyet as niyet_api
from api.niyet import _parse_json, _safe_operation, _social_context, dispatch_get, dispatch_post, handler
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


def test_unexpected_handler_exception_is_logged_and_remains_generic(caplog: pytest.LogCaptureFixture) -> None:
    response: dict = {}
    api_handler = object.__new__(handler)
    api_handler._json = lambda status, payload: response.update(status=status, payload=payload)  # type: ignore[method-assign]

    with caplog.at_level(logging.ERROR, logger="api.niyet"):
        try:
            raise RuntimeError("Firestore transaction failed")
        except RuntimeError as exc:
            api_handler._error(exc, operation="create_request")

    assert response == {"status": 500, "payload": {"error": {"code": "internal_error"}}}
    assert "action=create_request" in caplog.text
    assert "exception_class=RuntimeError" in caplog.text
    assert "exception_message=Firestore transaction failed" in caplog.text
    assert "Traceback (most recent call last)" in caplog.text


def test_unexpected_exception_log_redacts_secrets_and_never_logs_request_body(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response: dict = {}
    api_handler = object.__new__(handler)
    api_handler._json = lambda status, payload: response.update(status=status, payload=payload)  # type: ignore[method-assign]
    request_body = b'{"action":"create_request","text":"PRIVATE REQUEST BODY"}'
    api_handler.headers = {
        "Authorization": "Bearer request-header-secret",
        "Content-Length": str(len(request_body)),
        "Content-Type": "application/json",
    }
    api_handler.rfile = BytesIO(request_body)
    api_handler._actor = lambda: actor("verified")  # type: ignore[method-assign]
    exception_message = (
        "Firestore failed Authorization: Bearer header-secret "
        "password=password-secret id_token=token-secret email=user@example.test"
    )

    def fail_dispatch(*_: object) -> dict:
        raise RuntimeError(exception_message)

    monkeypatch.setattr(niyet_api, "dispatch_post", fail_dispatch)
    monkeypatch.setattr(niyet_api, "get_service", lambda: object())
    with caplog.at_level(logging.ERROR, logger="api.niyet"):
        api_handler.do_POST()

    assert response["status"] == 500
    assert "request-header-secret" not in caplog.text
    assert "header-secret" not in caplog.text
    assert "password-secret" not in caplog.text
    assert "token-secret" not in caplog.text
    assert "user@example.test" not in caplog.text
    assert request_body.decode() not in caplog.text
    assert "PRIVATE REQUEST BODY" not in caplog.text
    assert "[REDACTED]" in caplog.text


def test_log_operation_is_allowlisted() -> None:
    assert _safe_operation("create_request") == "create_request"
    assert _safe_operation("create_request\nAuthorization: Bearer injected-secret") == "unknown"
