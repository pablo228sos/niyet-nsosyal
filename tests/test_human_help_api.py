from __future__ import annotations

import http.client
import json
import threading
from http.server import HTTPServer

import pytest

import api.human_help as human_api


@pytest.fixture
def api_server():
    human_api.service.reset()
    server = HTTPServer(("127.0.0.1", 0), human_api.handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
        human_api.service.reset()


def post(address, payload):
    body = json.dumps(payload).encode("utf-8")
    connection = http.client.HTTPConnection(*address, timeout=4)
    connection.request(
        "POST",
        "/api/human-help",
        body=body,
        headers={"Content-Type": "application/json"},
    )
    response = connection.getresponse()
    result = response.status, json.loads(response.read())
    connection.close()
    return result


def get(address):
    connection = http.client.HTTPConnection(*address, timeout=4)
    connection.request("GET", "/api/human-help")
    response = connection.getresponse()
    result = response.status, json.loads(response.read())
    connection.close()
    return result


def test_health_exposes_state_backend_contract(api_server):
    status, payload = get(api_server)

    assert status == 200
    assert payload["status"] == "ok"
    assert payload["state_backend"] in {"memory", "upstash-redis-rest"}
    assert isinstance(payload["state_durable"], bool)
    assert payload["responders"]


def test_evidence_to_human_to_answer_round_trip(api_server):
    text = (
        "Research proves coffee consumption causes lower mortality. "
        "Can someone explain what the study actually shows?"
    )

    status, opened = post(api_server, {"action": "resolve", "text": text})
    assert status == 200
    request = opened["request"]
    assert opened["resolution"]["path"] == "BOTH"
    assert request["assigned_responder"]["id"] == "r_research"
    assert request["evidence_context"]["status"] in {"PARTIAL", "CONFLICTING"}
    evidence = request["evidence_context"]["evidence"][0]
    assert evidence["source_title"].startswith("Association of Coffee Consumption")
    assert evidence["source_url"] == "https://pubmed.ncbi.nlm.nih.gov/26572796/"
    assert "associated with lower risk" in evidence["passage"]
    assert "CAUSALITY_SHIFT" in evidence["distortions"]

    status, inbox = post(
        api_server,
        {"action": "inbox", "responder_id": "r_research"},
    )
    assert status == 200
    assert [item["request_id"] for item in inbox["requests"]] == [request["request_id"]]
    assert "author_token" not in inbox["requests"][0]

    status, accepted = post(
        api_server,
        {
            "action": "accept",
            "request_id": request["request_id"],
            "responder_id": "r_research",
        },
    )
    assert status == 200
    assert accepted["request"]["status"] == "ACCEPTED"

    answer = "The study reports an association. It does not establish that coffee caused the lower mortality."
    status, answered = post(
        api_server,
        {
            "action": "answer",
            "request_id": request["request_id"],
            "responder_id": "r_research",
            "answer": answer,
        },
    )
    assert status == 200
    assert answered["request"]["status"] == "ANSWERED"

    status, author = post(
        api_server,
        {
            "action": "status",
            "request_id": request["request_id"],
            "author_token": request["author_token"],
        },
    )
    assert status == 200
    assert author["request"]["answer"] == answer
    assert author["request"]["evidence_context"]["evidence"][0]["source_url"] == evidence["source_url"]


def test_stale_assignment_returns_conflict_instead_of_generic_bad_request(api_server):
    status, opened = post(
        api_server,
        {"action": "open", "text": "PID control loop tuning help needed."},
    )
    assert status == 200
    request = opened["request"]
    old_responder = request["assigned_responder"]["id"]

    status, paused = post(
        api_server,
        {"action": "pause", "responder_id": old_responder},
    )
    assert status == 200
    assert paused["responder_state"]["active"] is False

    status, conflict = post(
        api_server,
        {
            "action": "accept",
            "request_id": request["request_id"],
            "responder_id": old_responder,
        },
    )
    assert status == 409
    assert conflict["error"] == "request_not_assigned"


def test_reset_clears_shared_demo_state(api_server):
    status, opened = post(
        api_server,
        {"action": "open", "text": "PID control konusunda yardım arıyorum."},
    )
    assert status == 200
    request = opened["request"]

    status, reset = post(api_server, {"action": "reset"})
    assert status == 200
    assert reset["reset"] is True

    status, missing = post(
        api_server,
        {
            "action": "status",
            "request_id": request["request_id"],
            "author_token": request["author_token"],
        },
    )
    assert status == 404
    assert missing["error"] == "request_not_found"


def test_state_store_failures_map_to_service_unavailable_without_internal_details():
    assert human_api._runtime_error_response(
        RuntimeError("state_store_unavailable")
    ) == (503, "state_temporarily_unavailable")
    assert human_api._runtime_error_response(
        RuntimeError("state_store_conflict")
    ) == (503, "state_temporarily_unavailable")
