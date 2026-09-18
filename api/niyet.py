from __future__ import annotations

import json
import logging
import os
import re
import sys
import traceback
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from drsk.firebase_auth import AuthError, AuthenticatedUser, authenticate_authorization_header  # noqa: E402
from drsk.firebase_backend import (  # noqa: E402
    FirebaseConfigurationError,
    get_firestore_client,
    public_firebase_config,
)
from drsk.niyet_persistence import (  # noqa: E402
    DomainError,
    FirestoreNiyetRepository,
    NiyetService,
)

MAX_REQUEST_BYTES = 32 * 1024
MAX_LOG_MESSAGE_CHARS = 2_000
MAX_LOG_TRACEBACK_CHARS = 16_000
logger = logging.getLogger(__name__)
_service: NiyetService | None = None
_sourcechain: Any | None = None
_resolution_engine: Any | None = None

_LOGGABLE_ACTIONS = frozenset({
    "accept",
    "answer",
    "config",
    "create_request",
    "inbox",
    "me",
    "open",
    "pause",
    "profile",
    "request",
    "resolve",
    "resume",
    "skip",
    "sync_user",
    "update_profile",
})
_LOG_REDACTIONS = (
    (
        re.compile(
            r"-----BEGIN [^-\r\n]*PRIVATE KEY-----.*?-----END [^-\r\n]*PRIVATE KEY-----",
            re.IGNORECASE | re.DOTALL,
        ),
        "[REDACTED_PRIVATE_KEY]",
    ),
    (re.compile(r"\bBearer\s+[^\s,;]+", re.IGNORECASE), "Bearer [REDACTED]"),
    (
        re.compile(
            r'''(["']?(?:authorization|id_token|access_token|refresh_token|token|password|'''
            r'''private_key|client_secret|api_key|text|answer|email)["']?\s*[:=]\s*)'''
            r'''(?:"[^"]*"|'[^']*'|[^\s,;]+)''',
            re.IGNORECASE,
        ),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
        "[REDACTED_JWT]",
    ),
    (
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
        "[REDACTED_EMAIL]",
    ),
)


def _safe_operation(value: Any) -> str:
    operation = value.strip().lower() if isinstance(value, str) else ""
    return operation if operation in _LOGGABLE_ACTIONS else "unknown"


def _sanitize_log_text(value: str, limit: int) -> str:
    sanitized = value
    for pattern, replacement in _LOG_REDACTIONS:
        sanitized = pattern.sub(replacement, sanitized)
    if len(sanitized) > limit:
        return f"{sanitized[:limit]}...[truncated]"
    return sanitized


def _log_unexpected_exception(exc: Exception, operation: str) -> None:
    # logger.exception would append the raw exception message to its traceback.
    # Format and redact the traceback first so credentials cannot reach runtime logs.
    message = _sanitize_log_text(str(exc), MAX_LOG_MESSAGE_CHARS)
    traceback_text = _sanitize_log_text(
        "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        MAX_LOG_TRACEBACK_CHARS,
    )
    logger.error(
        "Unhandled NIYET API exception action=%s exception_class=%s exception_message=%s\n%s",
        _safe_operation(operation),
        type(exc).__name__,
        message,
        traceback_text,
    )


def get_service() -> NiyetService:
    global _service
    if _service is None:
        _service = NiyetService(FirestoreNiyetRepository(get_firestore_client()))
    return _service


def _get_resolution_components() -> tuple[Any, Any]:
    global _sourcechain, _resolution_engine
    if _sourcechain is None:
        from sourcechain.pipeline import SourcechainPipeline

        _sourcechain = SourcechainPipeline()
    if _resolution_engine is None:
        from drsk.resolution import ResolutionEngine

        _resolution_engine = ResolutionEngine()
    return _sourcechain, _resolution_engine


def _evidence_context(bundle: Any, resolution: dict[str, Any]) -> dict[str, Any]:
    value = bundle.to_dict()
    claims = {
        str(item.get("claim_id")): item.get("text")
        for item in value.get("analysis", {}).get("claims", [])
        if isinstance(item, dict) and item.get("claim_id") and item.get("text")
    }
    evidence = []
    for item in value.get("evidence", [])[:3]:
        if not isinstance(item, dict):
            continue
        evidence.append({
            "claim_text": claims.get(str(item.get("claim_id"))),
            "source_title": item.get("title") or item.get("publisher"),
            "source_url": item.get("source_url") or item.get("canonical_url"),
            "publisher": item.get("publisher"),
            "publication_date": item.get("publication_date"),
            "passage": item.get("passage"),
            "relation": item.get("relation"),
            "distortions": item.get("distortions", []),
        })
    return {
        "status": value.get("status"),
        "sufficient": value.get("sufficient"),
        "explanation": value.get("explanation"),
        "resolution": resolution,
        "evidence": evidence,
    }


def _social_context(payload: dict[str, Any]) -> dict[str, Any] | None:
    raw_url = payload.get("post_url")
    if raw_url is None:
        return None
    if not isinstance(raw_url, str) or len(raw_url) > 2048:
        raise DomainError("invalid_post_url")
    parsed = urlparse(raw_url.strip())
    try:
        port = parsed.port
    except ValueError as exc:
        raise DomainError("invalid_post_url") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname not in {"nsosyal.com", "www.nsosyal.com"}
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
    ):
        raise DomainError("invalid_post_url")
    return {"platform": "NSosyal", "post_url": parsed.geturl(), "published_observed": True}


def _json_default(value: Any) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_nonfinite_number(value: str) -> None:
    raise ValueError(f"non_finite_json_number:{value}")


def _parse_json(raw: bytes) -> Any:
    return json.loads(
        raw,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite_number,
    )


def dispatch_get(
    action: str,
    actor: AuthenticatedUser,
    service: NiyetService,
    query: dict[str, list[str]],
) -> dict[str, Any]:
    if action == "me":
        profile = service.repository.get_profile(actor.uid)
        return {
            "user": service.repository.get_user(actor.uid),
            "responder_profile": profile,
        }
    if action == "profile":
        return {"responder_profile": service.get_responder_profile(actor)}
    if action == "inbox":
        return {"assignments": service.list_inbox(actor)}
    if action == "request":
        request_id = (query.get("request_id") or [""])[0]
        return {"request": service.get_author_request(actor, request_id)}
    raise DomainError("invalid_action", 400)


def dispatch_post(
    payload: dict[str, Any],
    actor: AuthenticatedUser,
    service: NiyetService,
) -> dict[str, Any]:
    action = str(payload.get("action", "")).strip().lower()
    if action == "sync_user":
        return {"user": service.sync_user(actor)}
    if action in {"update_profile", "create_request", "open", "resolve"}:
        service.sync_user(actor)
    if action == "update_profile":
        return {"responder_profile": service.update_responder_profile(actor, payload)}
    if action in {"create_request", "open"}:
        request = service.create_request(
            actor,
            text=payload.get("text", ""),
            intent=payload.get("intent", "ask"),
            idempotency_key=payload.get("idempotency_key"),
            untrusted_author_uid=payload.get("author_uid"),
        )
        return {"request": service.get_author_request(actor, request["id"])}
    if action == "resolve":
        text = payload.get("text", "")
        clean_text = text.strip() if isinstance(text, str) else ""
        if not clean_text or len(clean_text) > 1200:
            raise DomainError("invalid_request_text")
        sourcechain, resolution_engine = _get_resolution_components()
        bundle = sourcechain.analyze(clean_text)
        decision = resolution_engine.resolve(bundle, ask_human=True)
        resolution = decision.to_dict()
        evidence_context = _evidence_context(bundle, resolution)
        if decision.escalation is None:
            return {
                "request": None,
                "resolution": resolution,
                "evidence_context": evidence_context,
                "human_recommended": False,
                "human_available": False,
            }
        request = service.create_request(
            actor,
            text=clean_text,
            intent="ask",
            idempotency_key=payload.get("idempotency_key"),
            metadata={
                "evidence_context": evidence_context,
                "resolution": resolution,
                "social_context": _social_context(payload),
            },
            untrusted_author_uid=payload.get("author_uid"),
        )
        return {
            "request": service.get_author_request(actor, request["id"]),
            "resolution": resolution,
            "evidence_context": evidence_context,
            "human_recommended": True,
            "human_available": bool(request.get("current_assignment_id")),
        }
    assignment_id = str(payload.get("assignment_id", "")).strip()
    if action == "accept":
        return {"assignment": service.accept(actor, assignment_id)}
    if action == "skip":
        return {"assignment": service.skip(actor, assignment_id)}
    if action == "answer":
        return {"assignment": service.answer(actor, assignment_id, payload.get("answer", ""))}
    if action == "pause":
        return {"responder_profile": service.pause(actor)}
    if action == "resume":
        return {"responder_profile": service.resume(actor)}
    raise DomainError("invalid_action", 400)


class handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, default=_json_default).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _actor(self) -> AuthenticatedUser:
        return authenticate_authorization_header(self.headers.get("Authorization"))

    def _error(self, exc: Exception, *, operation: str) -> None:
        if isinstance(exc, (AuthError, DomainError)):
            self._json(exc.status, {"error": {"code": exc.code}})
            return
        if isinstance(exc, FirebaseConfigurationError):
            self._json(503, {"error": {"code": str(exc)}})
            return
        _log_unexpected_exception(exc, operation)
        self._json(500, {"error": {"code": "internal_error"}})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        action = (query.get("action") or ["me"])[0]
        try:
            if action == "config":
                self._json(200, {"firebase": public_firebase_config()})
                return
            self._json(200, dispatch_get(action, self._actor(), get_service(), query))
        except Exception as exc:
            self._error(exc, operation=_safe_operation(action))

    def do_POST(self) -> None:
        operation = "unknown"
        try:
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                raise DomainError("unsupported_media_type", 415)
            raw_length = self.headers.get("Content-Length", "0")
            try:
                length = int(raw_length)
            except ValueError as exc:
                raise DomainError("invalid_content_length") from exc
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise DomainError("invalid_request_size", 413 if length > MAX_REQUEST_BYTES else 400)
            try:
                payload = _parse_json(self.rfile.read(length))
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
                raise DomainError("invalid_json") from exc
            if not isinstance(payload, dict):
                raise DomainError("json_object_required")
            operation = _safe_operation(payload.get("action"))
            result = dispatch_post(payload, self._actor(), get_service())
            self._json(200, result)
        except Exception as exc:
            self._error(exc, operation=operation)
