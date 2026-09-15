from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

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

    evidence_items = []
    for item in bundle.get("evidence", [])[:3]:
        if not isinstance(item, dict):
            continue
        evidence_items.append(
            {
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

        if action == "resolve":
            text = _clean_string(payload, "text")
            if len(text) > MAX_TEXT_LENGTH:
                raise ValueError("text_too_long")
            response = orchestrator.analyze(
                text,
                ask_human=True,
                responder_state=service.responder_state(),
            )
            context = _evidence_context(response)
            routing = response.get("human_routing")
            if not isinstance(routing, dict) or not routing.get("responder_id"):
                return {
                    "resolution": response.get("resolution"),
                    "evidence_context": context,
                    "request": None,
                }
            request = service.open_from_routing(
                text,
                routing,
                evidence_context=context,
            )
            return {
                "resolution": response.get("resolution"),
                "request": request.public_dict(include_author_token=True),
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
