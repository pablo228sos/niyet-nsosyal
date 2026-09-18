from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from ipaddress import ip_address
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from niyet.runtime import NiyetRuntime, RouteDecision  # noqa: E402
from niyet.types import IntentType  # noqa: E402


runtime = NiyetRuntime(os.path.join(ROOT, "data"))
MAX_REQUEST_BYTES = 32 * 1024
MAX_TEXT_LENGTH = 1200
MAX_REQUEST_ID_LENGTH = 80
_DRSK = None
_SAFE_EVIDENCE_METADATA = frozenset({"provider", "lexical_score"})


def _drsk_orchestrator():
    # Build once: constructing NiyetRuntime fits two classifiers and must not
    # become request-amplified CPU work. The lazy boundary also keeps legacy
    # NIYET import behavior stable.
    global _DRSK
    from drsk.orchestrator import DrskOrchestrator

    if _DRSK is None:
        _DRSK = DrskOrchestrator(niyet_runtime=runtime)
    return _DRSK


def _valid_responder_state(value: object) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict):
        return False

    known_responders = runtime.responder_by_id
    if len(value) > len(known_responders):
        return False
    for responder_id, state in value.items():
        responder = (
            known_responders.get(responder_id)
            if isinstance(responder_id, str)
            else None
        )
        if responder is None or not isinstance(state, dict):
            return False
        if not set(state).issubset({"remaining_slots", "active"}):
            return False
        slots = state.get("remaining_slots", responder.remaining_slots)
        active = state.get("active", responder.responder.active)
        if isinstance(slots, bool) or not isinstance(slots, int):
            return False
        if not 0 <= slots <= responder.daily_budget or not isinstance(active, bool):
            return False
    return True


def _valid_string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _valid_responder_id_list(value: object) -> bool:
    return (
        _valid_string_list(value)
        and len(value) <= len(runtime.responder_by_id)
        and len(value) == len(set(value))
        and all(item in runtime.responder_by_id for item in value)
    )


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite_number(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def _parse_json(value: bytes) -> object:
    return json.loads(
        value,
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite_number,
    )


def _safe_evidence_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        return False

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname == "localhost" or hostname.endswith(
        (".localhost", ".local", ".internal")
    ):
        return False
    try:
        return ip_address(hostname).is_global
    except ValueError:
        return True


def _safe_evidence_bundle(value: object) -> dict:
    if not isinstance(value, dict):
        raise ValueError("invalid evidence bundle")
    evidence = value.get("evidence", [])
    if not isinstance(evidence, list):
        raise ValueError("invalid evidence list")

    sanitized = dict(value)
    sanitized_evidence = []
    for raw_item in evidence:
        if not isinstance(raw_item, dict):
            raise ValueError("invalid evidence item")
        if not all(
            _safe_evidence_url(raw_item.get(field))
            for field in ("source_url", "canonical_url")
        ):
            raise ValueError("unsafe evidence URL")
        item = dict(raw_item)
        metadata = item.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("invalid evidence metadata")
        item["metadata"] = {
            key: metadata[key]
            for key in _SAFE_EVIDENCE_METADATA
            if key in metadata and isinstance(metadata[key], (str, int, float, bool))
        }
        sanitized_evidence.append(item)
    sanitized["evidence"] = sanitized_evidence
    return sanitized


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
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
        )
        self.send_header(
            "Permissions-Policy", "camera=(), microphone=(), geolocation=()"
        )
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
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
        content_type = (
            self.headers.get("Content-Type", "")
            .split(";", 1)[0]
            .strip()
            .lower()
        )
        if content_type != "application/json" and not content_type.endswith("+json"):
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

        if length < 0:
            self._json(400, {"error": "invalid_content_length"})
            return
        if length > MAX_REQUEST_BYTES:
            self._json(413, {"error": "request_body_too_large"})
            return

        try:
            payload = _parse_json(self.rfile.read(length) or b"{}")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
            self._json(400, {"error": "invalid_json"})
            return
        if not isinstance(payload, dict):
            self._json(400, {"error": "json_object_required"})
            return

        responder_state = payload.get("responder_state")
        if not _valid_responder_state(responder_state):
            self._json(400, {"error": "invalid_responder_state"})
            return

        raw_action = payload.get("action", "")
        if not isinstance(raw_action, str):
            self._json(400, {"error": "invalid_action"})
            return
        action = raw_action.strip().lower()

        if action in {"analyze", "resolve"}:
            raw_text = payload.get("text")
            if not isinstance(raw_text, str) or not raw_text.strip():
                self._json(400, {"error": "text_required"})
                return
            text = raw_text.strip()
            if len(text) > MAX_TEXT_LENGTH:
                self._json(400, {"error": "text_too_long"})
                return

            ask_human = payload.get("ask_human", action == "resolve")
            include_niyet = payload.get("include_niyet", False)
            if not isinstance(ask_human, bool) or not isinstance(include_niyet, bool):
                self._json(400, {"error": "invalid_boolean_option"})
                return

            try:
                response = _drsk_orchestrator().analyze(
                    text,
                    ask_human=ask_human,
                    responder_state=responder_state,
                )
            except Exception:
                self._json(
                    500,
                    {"error": "drsk_analysis_failed"},
                )
                return
            if not isinstance(response, dict):
                self._json(500, {"error": "invalid_drsk_response"})
                return

            try:
                bundle = _safe_evidence_bundle(response.get("evidence_bundle"))
            except ValueError:
                self._json(500, {"error": "invalid_drsk_response"})
                return
            bundle_analysis = bundle.get("analysis", {}) if isinstance(bundle, dict) else {}
            result = {
                "status": "ok",
                "post_analysis": response.get("post_analysis") or bundle_analysis,
                "claims": response.get("claims") or bundle_analysis.get("claims", []),
                "evidence_bundle": bundle,
                "resolution": response.get("resolution"),
            }
            if response.get("human_routing") is not None:
                result["niyet"] = response["human_routing"]
            if include_niyet:
                try:
                    niyet_result = runtime.route(text, responder_state=responder_state)
                    result["niyet"] = serialize_decision(niyet_result, "model")
                    result["responder_state"] = runtime.normalize_responder_state(
                        responder_state
                    )
                except Exception:
                    self._json(
                        500,
                        {"error": "routing_failed"},
                    )
                    return
            self._json(200, result)
            return

        if action:
            raw_responder_id = payload.get("responder_id", "")
            responder_id = raw_responder_id.strip() if isinstance(raw_responder_id, str) else ""
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

        if "requests" in payload and not isinstance(payload["requests"], list):
            self._json(400, {"error": "invalid_requests"})
            return

        if isinstance(payload.get("requests"), list):
            raw_requests = payload["requests"]
            if not raw_requests or len(raw_requests) > 20:
                self._json(400, {"error": "batch_size_out_of_range"})
                return

            requests = []
            intent_sources: dict[str, str] = {}
            request_ids: set[str] = set()
            try:
                for index, item in enumerate(raw_requests):
                    if not isinstance(item, dict):
                        raise ValueError("invalid_batch_request")
                    raw_text = item.get("text")
                    if not isinstance(raw_text, str):
                        raise ValueError("invalid_batch_text")
                    text = raw_text.strip()
                    if not text or len(text) > MAX_TEXT_LENGTH:
                        raise ValueError("invalid_batch_text")
                    raw_request_id = item.get("id")
                    if raw_request_id is None:
                        request_id = f"batch-{index + 1}"
                    elif not isinstance(raw_request_id, str):
                        raise ValueError("invalid_batch_request_id")
                    else:
                        request_id = raw_request_id.strip()
                        if not request_id or len(request_id) > MAX_REQUEST_ID_LENGTH:
                            raise ValueError("invalid_batch_request_id")
                    if request_id in request_ids:
                        raise ValueError("duplicate_batch_request_id")
                    request_ids.add(request_id)
                    override_raw = item.get("intent_override")
                    override = None
                    if override_raw is not None:
                        if not isinstance(override_raw, str):
                            raise ValueError("invalid_intent_override")
                        clean_override = override_raw.strip().lower()
                        if clean_override:
                            override = IntentType(clean_override)
                    excluded_ids = item.get("exclude_responder_ids", [])
                    if not _valid_responder_id_list(excluded_ids):
                        raise ValueError("invalid_exclude_responder_ids")
                    requests.append(
                        {
                            "id": request_id,
                            "text": text,
                            "intent_override": override,
                            "exclude_responder_ids": excluded_ids,
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
            except Exception:
                self._json(
                    500,
                    {"error": "batch_routing_failed"},
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

        raw_text = payload.get("text")
        text = raw_text.strip() if isinstance(raw_text, str) else ""
        override_raw = payload.get("intent_override")
        raw_excluded = payload.get("exclude_responder_ids", [])
        if not _valid_responder_id_list(raw_excluded):
            self._json(400, {"error": "invalid_exclude_responder_ids"})
            return
        excluded = tuple(raw_excluded)

        if not text:
            self._json(400, {"error": "text_required"})
            return
        if len(text) > MAX_TEXT_LENGTH:
            self._json(400, {"error": "text_too_long"})
            return

        intent_override = None
        if override_raw is not None:
            if not isinstance(override_raw, str):
                self._json(400, {"error": "invalid_intent_override"})
                return
            try:
                clean_override = override_raw.strip().lower()
                if clean_override:
                    intent_override = IntentType(clean_override)
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
        except Exception:
            self._json(
                500,
                {"error": "routing_failed"},
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
