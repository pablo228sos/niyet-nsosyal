from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from niyet.runtime import NiyetRuntime, RouteDecision  # noqa: E402
from niyet.types import IntentType  # noqa: E402


runtime = NiyetRuntime(os.path.join(ROOT, "data"))


def serialize_decision(result: RouteDecision, intent_source: str) -> dict:
    return {
        "request_id": result.request_id,
        "response_needed": result.response_needed,
        "intent": result.intent.upper() if result.intent else None,
        "intent_source": intent_source,
        "match": (
            {
                "id": result.responder_id,
                "name": result.responder_name,
                "reason": list(result.reason),
            }
            if result.responder_id
            else None
        ),
        "technical": {
            "development_utility": (
                round(result.development_utility, 4)
                if result.development_utility is not None
                else None
            ),
            "retrieval_similarity": (
                round(result.retrieval_similarity, 4)
                if result.retrieval_similarity is not None
                else None
            ),
            "note": "Development diagnostics. Values are not calibrated probabilities.",
        },
    }


class handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        self._json(
            200,
            {
                "status": "ok",
                "service": "DRSK / NIYET routing prototype",
                "model_scope": "controlled Turkish development data",
                "retrieval": "character TF-IDF deployment baseline",
                "allocation": "capacity-constrained global assignment",
                "state_model": "browser-session responder capacity",
                "default_responder_state": runtime.default_responder_state(),
            },
        )

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"error": "invalid_json"})
            return

        responder_state = payload.get("responder_state")
        action = str(payload.get("action", "")).strip().lower()

        if action:
            responder_id = str(payload.get("responder_id", "")).strip()
            if action not in {"accept", "pause", "resume"}:
                self._json(400, {"error": "invalid_action"})
                return
            if not responder_id:
                self._json(400, {"error": "responder_id_required"})
                return
            try:
                state = runtime.update_responder_state(
                    responder_state,
                    responder_id,
                    action=action,
                )
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
                return
            self._json(
                200,
                {
                    "status": "ok",
                    "action": action,
                    "responder_id": responder_id,
                    "responder_state": state,
                },
            )
            return

        if isinstance(payload.get("requests"), list):
            raw_requests = payload["requests"]
            if not raw_requests or len(raw_requests) > 20:
                self._json(400, {"error": "batch_size_out_of_range"})
                return

            requests = []
            intent_sources: dict[str, str] = {}
            try:
                for index, item in enumerate(raw_requests):
                    if not isinstance(item, dict):
                        raise ValueError("invalid_batch_request")
                    text = str(item.get("text", "")).strip()
                    if not text or len(text) > 1200:
                        raise ValueError("invalid_batch_text")
                    request_id = str(item.get("id") or f"batch-{index + 1}")
                    override_raw = item.get("intent_override")
                    override = None
                    if override_raw:
                        override = IntentType(str(override_raw).strip().lower())
                    requests.append(
                        {
                            "id": request_id,
                            "text": text,
                            "intent_override": override,
                            "exclude_responder_ids": item.get(
                                "exclude_responder_ids", []
                            ),
                        }
                    )
                    intent_sources[request_id] = (
                        "user_confirmed" if override else "model"
                    )
            except ValueError as exc:
                self._json(400, {"error": str(exc)})
                return

            try:
                decisions = runtime.route_many(
                    requests,
                    responder_state=responder_state,
                )
            except Exception as exc:
                self._json(
                    500,
                    {"error": "batch_routing_failed", "detail": type(exc).__name__},
                )
                return

            self._json(
                200,
                {
                    "status": "ok",
                    "batch_size": len(requests),
                    "allocation_scope": "bounded matching window",
                    "decisions": [
                        serialize_decision(
                            result,
                            intent_sources.get(result.request_id or "", "model"),
                        )
                        for result in decisions
                    ],
                    "responder_state": runtime.normalize_responder_state(
                        responder_state
                    ),
                    "model_scope": "Turkish controlled development model",
                },
            )
            return

        text = str(payload.get("text", "")).strip()
        override_raw = payload.get("intent_override")
        excluded = tuple(
            str(value) for value in payload.get("exclude_responder_ids", [])
        )

        if not text:
            self._json(400, {"error": "text_required"})
            return
        if len(text) > 1200:
            self._json(400, {"error": "text_too_long"})
            return

        intent_override = None
        if override_raw:
            try:
                intent_override = IntentType(str(override_raw).strip().lower())
            except ValueError:
                self._json(400, {"error": "invalid_intent_override"})
                return

        try:
            result = runtime.route(
                text,
                intent_override=intent_override,
                responder_state=responder_state,
                exclude_responder_ids=excluded,
            )
        except Exception as exc:
            self._json(
                500,
                {"error": "routing_failed", "detail": type(exc).__name__},
            )
            return

        response = serialize_decision(
            result,
            "user_confirmed" if intent_override else "model",
        )
        response.update(
            {
                "status": "ok",
                "responder_state": runtime.normalize_responder_state(
                    responder_state
                ),
                "model_scope": "Turkish controlled development model",
            }
        )
        self._json(200, response)
