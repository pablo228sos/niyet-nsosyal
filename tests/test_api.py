from __future__ import annotations

import http.client
import json
import threading
from http.server import HTTPServer
from pathlib import Path

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


def raw_post(address, body, headers=None):
    connection = http.client.HTTPConnection(*address, timeout=3)
    connection.request(
        "POST",
        "/api",
        body=body,
        headers=headers or {},
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
    assert response.getheader("Content-Security-Policy") == (
        "default-src 'none'; frame-ancestors 'none'"
    )
    assert response.getheader("Permissions-Policy") == (
        "camera=(), microphone=(), geolocation=()"
    )
    assert response.getheader("Cross-Origin-Resource-Policy") == "same-origin"
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


def test_vercel_applies_transport_and_isolation_headers():
    config = json.loads((Path(__file__).parents[1] / "vercel.json").read_text())
    headers = {
        item["key"]: item["value"]
        for rule in config["headers"]
        for item in rule["headers"]
    }
    assert headers["Strict-Transport-Security"] == "max-age=31536000"
    assert headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert headers["Cross-Origin-Opener-Policy"] == "same-origin"


@pytest.mark.parametrize(
    ("body", "expected_error"),
    [
        (b"{", "invalid_json"),
        (b'"unterminated', "invalid_json"),
        (b"\xff", "invalid_json"),
        (b'{"text":"first","text":"second"}', "invalid_json"),
        (b'{"text":NaN}', "invalid_json"),
    ],
)
def test_api_rejects_malformed_json(api_server, body, expected_error):
    status, payload = raw_post(
        api_server,
        body,
        {"Content-Type": "application/json"},
    )
    assert status == 400
    assert payload == {"error": expected_error}


def test_api_requires_json_content_type(api_server):
    status, payload = raw_post(
        api_server,
        b'{"text":"PID ayari nasil yapilir?"}',
        {"Content-Type": "text/plain"},
    )
    assert status == 415
    assert payload == {"error": "unsupported_media_type"}


def test_api_requires_content_length(api_server):
    connection = http.client.HTTPConnection(*api_server, timeout=3)
    connection.putrequest("POST", "/api")
    connection.putheader("Content-Type", "application/json")
    connection.endheaders()
    response = connection.getresponse()
    assert response.status == 411
    assert json.loads(response.read()) == {"error": "content_length_required"}
    connection.close()


@pytest.mark.parametrize("raw_length", ["invalid", "-1"])
def test_api_rejects_invalid_content_length(api_server, raw_length):
    connection = http.client.HTTPConnection(*api_server, timeout=3)
    connection.putrequest("POST", "/api")
    connection.putheader("Content-Type", "application/json")
    connection.putheader("Content-Length", raw_length)
    connection.endheaders()
    response = connection.getresponse()
    assert response.status == 400
    assert json.loads(response.read())["error"] == "invalid_content_length"
    connection.close()


@pytest.mark.parametrize(
    "invalid_values",
    [
        "active",
        {"remaining_slots": "many", "active": True},
        {"remaining_slots": 1, "active": "yes"},
        {"remaining_slots": 1, "active": True, "admin": True},
    ],
)
def test_api_rejects_untrusted_responder_state_shapes(api_server, invalid_values):
    responder_id = next(iter(api.runtime.default_responder_state()))
    status, payload = post(
        api_server,
        {
            "text": "PID ayari nasil yapilir?",
            "responder_state": {responder_id: invalid_values},
        },
    )
    assert status == 400
    assert payload == {"error": "invalid_responder_state"}


def test_api_rejects_unknown_responder_state_id(api_server):
    status, payload = post(
        api_server,
        {
            "text": "PID ayari nasil yapilir?",
            "responder_state": {
                "unknown": {"remaining_slots": 1, "active": True}
            },
        },
    )
    assert status == 400
    assert payload == {"error": "invalid_responder_state"}


def test_api_rejects_responder_capacity_above_server_profile(api_server):
    responder_id = next(iter(api.runtime.default_responder_state()))
    daily_budget = api.runtime.responder_by_id[responder_id].daily_budget
    status, payload = post(
        api_server,
        {
            "text": "PID ayari nasil yapilir?",
            "responder_state": {
                responder_id: {
                    "remaining_slots": daily_budget + 1,
                    "active": True,
                }
            },
        },
    )
    assert status == 400
    assert payload == {"error": "invalid_responder_state"}


def test_api_rejects_duplicate_batch_ids_after_normalization(api_server):
    status, payload = post(
        api_server,
        {
            "requests": [
                {"id": "same", "text": "PID ayari nasil yapilir?"},
                {"id": " same ", "text": "Motor kontrolu nasil yapilir?"},
            ]
        },
    )
    assert status == 400
    assert payload == {"error": "duplicate_batch_request_id"}


@pytest.mark.parametrize("requests", [[], [{}] * 21])
def test_api_enforces_batch_bounds(api_server, requests):
    status, payload = post(api_server, {"requests": requests})
    assert status == 400
    assert payload == {"error": "batch_size_out_of_range"}


@pytest.mark.parametrize("request_id", ["", " ", "x" * 81])
def test_api_rejects_invalid_explicit_batch_ids(api_server, request_id):
    status, payload = post(
        api_server,
        {"requests": [{"id": request_id, "text": "PID ayari nasil yapilir?"}]},
    )
    assert status == 400
    assert payload == {"error": "invalid_batch_request_id"}


def test_api_does_not_leak_internal_exception_types(api_server, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("database-password=secret")

    monkeypatch.setattr(api.runtime, "route", fail)
    status, payload = post(api_server, {"text": "PID ayari nasil yapilir?"})
    assert status == 500
    assert payload == {"error": "routing_failed"}


def test_drsk_does_not_leak_internal_exception_types(api_server, monkeypatch):
    class FailingOrchestrator:
        def analyze(self, *args, **kwargs):
            raise RuntimeError("api-key=secret")

    monkeypatch.setattr(api, "_drsk_orchestrator", lambda: FailingOrchestrator())
    status, payload = post(api_server, {"action": "analyze", "text": "X causes Y."})
    assert status == 500
    assert payload == {"error": "drsk_analysis_failed"}


@pytest.mark.parametrize(
    "excluded",
    [
        ["unknown"],
        ["r_control", "r_control"],
    ],
)
def test_api_rejects_invalid_excluded_responder_ids(api_server, excluded):
    status, payload = post(
        api_server,
        {
            "text": "PID ayari nasil yapilir?",
            "exclude_responder_ids": excluded,
        },
    )
    assert status == 400
    assert payload == {"error": "invalid_exclude_responder_ids"}


@pytest.mark.parametrize("override", [[], 0, False])
def test_api_rejects_non_string_intent_override(api_server, override):
    status, payload = post(
        api_server,
        {"text": "PID ayari nasil yapilir?", "intent_override": override},
    )
    assert status == 400
    assert payload == {"error": "invalid_intent_override"}


def test_drsk_rejects_long_claim_before_analysis(api_server, monkeypatch):
    def forbidden_orchestrator():
        raise AssertionError("orchestrator should not be constructed")

    monkeypatch.setattr(api, "_drsk_orchestrator", forbidden_orchestrator)
    status, payload = post(
        api_server,
        {"action": "analyze", "text": "x" * (api.MAX_TEXT_LENGTH + 1)},
    )
    assert status == 400
    assert payload == {"error": "text_too_long"}


def test_drsk_rejects_unsafe_evidence_urls_without_leaking_details(
    api_server, monkeypatch
):
    class UnsafeOrchestrator:
        def analyze(self, *args, **kwargs):
            return {
                "evidence_bundle": {
                    "analysis": {"claims": []},
                    "evidence": [
                        {
                            "source_url": "file:///etc/passwd",
                            "canonical_url": "https://example.org/source",
                            "metadata": {"provider": "controlled"},
                        }
                    ],
                },
                "resolution": {"path": "EVIDENCE"},
            }

    monkeypatch.setattr(api, "_drsk_orchestrator", lambda: UnsafeOrchestrator())
    status, payload = post(api_server, {"action": "analyze", "text": "X causes Y."})
    assert status == 500
    assert payload == {"error": "invalid_drsk_response"}


def test_drsk_filters_private_evidence_metadata(api_server, monkeypatch):
    class MetadataOrchestrator:
        def analyze(self, text, **kwargs):
            return {
                "evidence_bundle": {
                    "analysis": {"claims": []},
                    "evidence": [
                        {
                            "source_url": "https://example.org/source",
                            "canonical_url": "https://example.org/source",
                            "metadata": {
                                "provider": "controlled",
                                "lexical_score": 0.5,
                                "api_key": "secret",
                                "filesystem_path": "C:/private/data.txt",
                            },
                        }
                    ],
                },
                "resolution": {"path": "EVIDENCE"},
            }

    monkeypatch.setattr(api, "_drsk_orchestrator", lambda: MetadataOrchestrator())
    status, payload = post(api_server, {"action": "analyze", "text": "X causes Y."})
    assert status == 200
    assert payload["evidence_bundle"]["evidence"][0]["metadata"] == {
        "provider": "controlled",
        "lexical_score": 0.5,
    }


def test_api_does_not_fetch_user_supplied_urls(api_server, monkeypatch):
    def forbidden_fetch(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr("urllib.request.urlopen", forbidden_fetch)
    supplied_url = "http://169.254.169.254/latest/meta-data/"
    status, payload = post(
        api_server,
        {
            "action": "analyze",
            "text": "X causes Y.",
            "source_url": supplied_url,
            "url": supplied_url,
        },
    )
    assert status == 200
    assert supplied_url not in json.dumps(payload)


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
