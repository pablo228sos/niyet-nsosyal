from __future__ import annotations

import http.client
import json
import threading
from http.server import HTTPServer

import pytest

import api.index as api


@pytest.fixture
def api_server():
    server = HTTPServer(("127.0.0.1", 0), api.handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def post(address, payload, headers=None):
    body = json.dumps(payload).encode("utf-8")
    connection = http.client.HTTPConnection(*address, timeout=3)
    connection.request(
        "POST",
        "/api",
        body=body,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    response = connection.getresponse()
    result = response.status, json.loads(response.read())
    connection.close()
    return result


def test_api_rejects_non_object_json(api_server):
    status, payload = post(api_server, ["not", "an", "object"])
    assert status == 400
    assert payload["error"] == "json_object_required"


def test_api_sets_basic_browser_security_headers(api_server):
    connection = http.client.HTTPConnection(*api_server, timeout=3)
    connection.request("GET", "/api")
    response = connection.getresponse()
    assert response.getheader("X-Content-Type-Options") == "nosniff"
    assert response.getheader("X-Frame-Options") == "DENY"
    assert response.getheader("Referrer-Policy") == "no-referrer"
    response.read()
    connection.close()


def test_drsk_orchestrator_is_reused_between_requests():
    assert api._drsk_orchestrator() is api._drsk_orchestrator()


def test_api_rejects_oversized_body_before_read(api_server):
    connection = http.client.HTTPConnection(*api_server, timeout=3)
    connection.putrequest("POST", "/api")
    connection.putheader("Content-Type", "application/json")
    connection.putheader("Content-Length", str(api.MAX_REQUEST_BYTES + 1))
    connection.endheaders()
    response = connection.getresponse()
    assert response.status == 413
    assert json.loads(response.read())["error"] == "request_body_too_large"
    connection.close()


def test_drsk_action_exposes_analysis_evidence_resolution_and_optional_niyet(
    api_server, monkeypatch
):
    class FakeOrchestrator:
        def analyze(self, text, ask_human=False, responder_state=None):
            assert text == "X causes Y."
            assert ask_human is True
            return {
                "evidence_bundle": {
                    "analysis": {
                        "text": text,
                        "statement_type": "FACTUAL_CLAIM",
                        "check_worthy": True,
                        "claims": [{"claim_id": "c1", "text": text}],
                    },
                    "evidence": [],
                    "status": "INSUFFICIENT",
                },
                "resolution": {"path": "HUMAN", "reasons": ["evidence_insufficient"]},
                "human_routing": {"response_needed": True, "intent": "ASK"},
            }

    monkeypatch.setattr(api, "_drsk_orchestrator", lambda: FakeOrchestrator())
    status, payload = post(
        api_server,
        {"action": "resolve", "text": "X causes Y.", "ask_human": True},
    )

    assert status == 200
    assert payload["post_analysis"]["statement_type"] == "FACTUAL_CLAIM"
    assert payload["claims"][0]["claim_id"] == "c1"
    assert payload["evidence_bundle"]["status"] == "INSUFFICIENT"
    assert payload["resolution"]["path"] == "HUMAN"
    assert payload["niyet"]["intent"] == "ASK"


def test_legacy_niyet_request_still_works_without_action(api_server):
    status, payload = post(
        api_server,
        {"text": "PID ayarı için nereden başlamalıyım?", "intent_override": "ask"},
    )
    assert status == 200
    assert payload["status"] == "ok"
    assert payload["intent"] == "ASK"
