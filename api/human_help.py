from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from drsk.human_help import HumanHelpService  # noqa: E402
from drsk.orchestrator import DrskOrchestrator  # noqa: E402
from drsk.state_store import state_store_from_environment  # noqa: E402
from niyet.final_runtime import FinalDemoRuntime  # noqa: E402


runtime = FinalDemoRuntime(os.path.join(ROOT, "data"))
initial_state = {
    "requests": {},
    "responder_state": runtime.default_responder_state(),
}
LEGACY_DISABLED = (
    os.getenv("VERCEL_ENV", "").strip().lower() == "production"
    or any(
        os.getenv(name, "").strip()
        for name in (
            "FIREBASE_PROJECT_ID",
            "FIREBASE_CLIENT_EMAIL",
            "FIREBASE_PRIVATE_KEY",
            "FIRESTORE_EMULATOR_HOST",
        )
    )
)
if LEGACY_DISABLED:
    state_store = None
    service = None
    orchestrator = None
else:
    state_store = state_store_from_environment(initial_state)
    service = HumanHelpService(runtime, store=state_store)
    orchestrator = DrskOrchestrator(niyet_runtime=runtime)

MAX_REQUEST_BYTES = 32 * 1024
MAX_TEXT_LENGTH = 1200
MAX_ANSWER_LENGTH = 4000

_CONFLICT_ERRORS = {
    "request_not_assigned",
    "request_not_open",
    "request_not_accepted",
    "responder_capacity_exhausted",
}
_NOT_FOUND_ERRORS = {"request_not_found", "unknown_responder"}
_FORBIDDEN_ERRORS = {"invalid_author_token"}
_HUMAN_RESOLUTION_PATHS = {"HUMAN", "BOTH", "DEFERRED"}


def _parse_json(raw: bytes) -> dict:
    value = json.loads(raw or b"{}")
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def _clean_string(payload: dict, key: str, *, required: bool = True) -> str:
    raw = payload.get(key)
    if raw is None and not required:
        return ""
    if not isinstance(raw, str):
        raise ValueError(f"{key}_required")
    value = raw.strip()
    if required and not value:
        raise ValueError(f"{key}_required")
    return value


def _value_error_status(code: str) -> int:
    if code in _CONFLICT_ERRORS:
        return 409
    if code in _NOT_FOUND_ERRORS:
        return 404
    if code in _FORBIDDEN_ERRORS:
        return 403
    return 400


def _published_social_context(payload: dict) -> dict | None:
    """Accept only a visible NSosyal publication reference from the adapter.

    The extension never receives account cookies or publishes on the user's
    behalf.  This marker records that the exact inspected text was observed on
    the NSosyal page before NIYET routing was requested.
    """

    raw_url = payload.get("post_url")
    if raw_url is None:
        return None
    if not isinstance(raw_url, str) or len(raw_url) > 2048:
        raise ValueError("invalid_post_url")
    parsed = urlparse(raw_url.strip())
    if parsed.scheme != "https" or parsed.hostname not in {
        "nsosyal.com",
        "www.nsosyal.com",
    }:
        raise ValueError("invalid_post_url")
    return {
        "platform": "NSosyal",
        "post_url": parsed.geturl(),
        "published_observed": True,
    }


def _runtime_error_response(exc: RuntimeError) -> tuple[int, str]:
    code = str(exc)
    if code.startswith("state_store_"):
        return 503, "state_temporarily_unavailable"
    return 500, "human_help_failed"


def _evidence_context(response: dict) -> dict | None:
    bundle = response.get("evidence_bundle")
    resolution = response.get("resolution")
    if not isinstance(bundle, dict):
        return None

    analysis = bundle.get("analysis")
    claims_by_id: dict[str, str] = {}
    if isinstance(analysis, dict):
        for claim in analysis.get("claims", []):
            if not isinstance(claim, dict):
                continue
            claim_id = claim.get("claim_id")
            claim_text = claim.get("text")
            if claim_id and isinstance(claim_text, str) and claim_text.strip():
                claims_by_id[str(claim_id)] = claim_text.strip()

    evidence_items = []
    for item in bundle.get("evidence", [])[:3]:
        if not isinstance(item, dict):
            continue
        claim_id = item.get("claim_id")
        evidence_items.append(
            {
                "claim_text": claims_by_id.get(str(claim_id)) if claim_id else None,
                "source_title": item.get("title") or item.get("publisher"),
                "source_url": item.get("source_url") or item.get("canonical_url"),
                "publisher": item.get("publisher"),
                "publication_date": item.get("publication_date"),
                "passage": item.get("passage"),
                "relation": item.get("relation"),
                "distortions": item.get("distortions", []),
            }
        )

    return {
        "status": bundle.get("status"),
        "sufficient": bundle.get("sufficient"),
        "explanation": bundle.get("explanation"),
        "resolution": resolution,
        "evidence": evidence_items,
    }


def _resolution_metadata(response: dict) -> dict:
    """Expose the recommendation without creating a human request.

    The browser integration uses this contract to keep evidence inspection and
    human escalation as two explicit user actions.  Routing remains advisory
    until the user confirms; no author token or internal routing text is
    returned in the preview.
    """
    resolution = response.get("resolution")
    path = resolution.get("path") if isinstance(resolution, dict) else None
    routing = response.get("human_routing")
    recommended = path in _HUMAN_RESOLUTION_PATHS
    available = bool(
        recommended
        and isinstance(routing, dict)
        and routing.get("responder_id")
    )
    preview = None
    if available:
        preview = {
            "id": routing.get("responder_id"),
            "name": routing.get("responder_name"),
            "reason": routing.get("reason", []),
        }
    return {
        "human_recommended": recommended,
        "human_available": available,
        "routing_preview": preview,
    }


class handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if LEGACY_DISABLED:
            self._json(410, {"error": "legacy_demo_endpoint_disabled"})
            return
        try:
            state = service.responder_state()
        except RuntimeError as exc:
            status, code = _runtime_error_response(exc)
            self._json(status, {"error": code})
            return
        except Exception:
            self._json(500, {"error": "human_help_failed"})
            return

        durable = service.state_durable
        self._json(
            200,
            {
                "status": "ok",
                "service": "DRSK human-help demo service",
                "state_backend": service.state_backend,
                "state_durable": durable,
                "state_model": (
                    "shared durable state"
                    if durable
                    else "process-local development fallback"
                ),
                "durability": (
                    "survives function instance replacement"
                    if durable
                    else "non-durable; configure shared state before live multi-device use"
                ),
                "responders": [
                    {
                        "id": item.responder.id,
                        "name": item.display_name,
                        "remaining_slots": state[item.responder.id]["remaining_slots"],
                        "active": state[item.responder.id]["active"],
                    }
                    for item in runtime.responders
                ],
            },
        )

    def do_POST(self) -> None:
        if LEGACY_DISABLED:
            self._json(410, {"error": "legacy_demo_endpoint_disabled"})
            return
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip()
        if content_type != "application/json":
            self._json(415, {"error": "unsupported_media_type"})
            return

        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            self._json(411, {"error": "content_length_required"})
            return
        try:
            length = int(raw_length)
        except ValueError:
            self._json(400, {"error": "invalid_content_length"})
            return
        if length < 0 or length > MAX_REQUEST_BYTES:
            self._json(
                413 if length > MAX_REQUEST_BYTES else 400,
                {"error": "invalid_content_length"},
            )
            return

        try:
            payload = _parse_json(self.rfile.read(length))
            action = _clean_string(payload, "action").lower()
            result = self._dispatch(action, payload)
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid_json"})
            return
        except ValueError as exc:
            code = str(exc)
            self._json(_value_error_status(code), {"error": code})
            return
        except RuntimeError as exc:
            status, code = _runtime_error_response(exc)
            self._json(status, {"error": code})
            return
        except Exception:
            self._json(500, {"error": "human_help_failed"})
            return

        self._json(200, {"status": "ok", **result})

    def _dispatch(self, action: str, payload: dict) -> dict:
        if action == "open":
            text = _clean_string(payload, "text")
            if len(text) > MAX_TEXT_LENGTH:
                raise ValueError("text_too_long")
            request = service.open_request(text)
            return {"request": request.public_dict(include_author_token=True)}

        if action in {"inspect", "resolve"}:
            text = _clean_string(payload, "text")
            if len(text) > MAX_TEXT_LENGTH:
                raise ValueError("text_too_long")
            social_context = (
                _published_social_context(payload)
                if action == "resolve"
                else None
            )
            response = orchestrator.analyze(
                text,
                ask_human=True,
                responder_state=service.responder_state(),
            )
            context = _evidence_context(response)
            metadata = _resolution_metadata(response)
            if action == "inspect":
                return {
                    "resolution": response.get("resolution"),
                    "evidence_context": context,
                    "request": None,
                    **metadata,
                }
            routing = response.get("human_routing")
            if not isinstance(routing, dict) or not routing.get("responder_id"):
                return {
                    "resolution": response.get("resolution"),
                    "evidence_context": context,
                    "request": None,
                    **metadata,
                }
            request = service.open_from_routing(
                text,
                routing,
                evidence_context=context,
                social_context=social_context,
            )
            return {
                "resolution": response.get("resolution"),
                "request": request.public_dict(include_author_token=True),
                **metadata,
            }

        if action == "inbox":
            responder_id = _clean_string(payload, "responder_id")
            return {"requests": service.inbox(responder_id)}

        if action == "status":
            request_id = _clean_string(payload, "request_id")
            author_token = _clean_string(payload, "author_token")
            return {"request": service.status(request_id, author_token)}

        if action in {"accept", "skip"}:
            request_id = _clean_string(payload, "request_id")
            responder_id = _clean_string(payload, "responder_id")
            request = (
                service.accept(request_id, responder_id)
                if action == "accept"
                else service.skip(request_id, responder_id)
            )
            return {
                "request": request,
                "responder_state": service.responder_state(),
            }

        if action == "answer":
            request_id = _clean_string(payload, "request_id")
            responder_id = _clean_string(payload, "responder_id")
            answer = _clean_string(payload, "answer")
            if len(answer) > MAX_ANSWER_LENGTH:
                raise ValueError("answer_too_long")
            request = service.answer(request_id, responder_id, answer)
            return {"request": request}

        if action in {"pause", "resume"}:
            responder_id = _clean_string(payload, "responder_id")
            state = service.set_responder_active(responder_id, action == "resume")
            return {"responder_id": responder_id, "responder_state": state}

        if action == "reset":
            service.reset()
            return {"reset": True}

        raise ValueError("invalid_action")
