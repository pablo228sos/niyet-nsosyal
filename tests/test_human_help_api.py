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


def test_inspect_recommends_human_without_opening_a_request(api_server):
    text = (
        "Research proves coffee consumption causes lower mortality. "
        "Can someone explain what the study actually shows?"
    )

    status, inspected = post(api_server, {"action": "inspect", "text": text})
    assert status == 200
    assert inspected["resolution"]["path"] == "BOTH"
    assert inspected["evidence_context"]["status"] in {"PARTIAL", "CONFLICTING"}
    assert inspected["human_recommended"] is True
    assert inspected["human_available"] is True
    assert inspected["routing_preview"]["id"] == "r_research"
    assert inspected["request"] is None

    status, inbox = post(
        api_server,
        {"action": "inbox", "responder_id": "r_research"},
    )
    assert status == 200
    assert inbox["requests"] == []


def test_pure_human_question_has_no_sourcechain_failure_context(api_server):
    text = "Çizgi izleyen robotum virajlarda salınım yapıyor. PID ayarına nereden başlamalıyım?"

    status, inspected = post(api_server, {"action": "inspect", "text": text})

    assert status == 200
    assert inspected["resolution"]["path"] == "HUMAN"
    assert inspected["statement_type"] == "QUESTION"
    assert inspected["check_worthy"] is False
    assert inspected["evidence_context"] is None
    assert inspected["human_recommended"] is True
    assert inspected["request"] is None


def test_opinion_has_no_evidence_context_or_human_request(api_server):
    status, inspected = post(
        api_server,
        {"action": "inspect", "text": "Dark mode looks better than light mode."},
    )

    assert status == 200
    assert inspected["resolution"]["path"] == "NONE"
    assert inspected["statement_type"] == "OPINION"
    assert inspected["check_worthy"] is False
    assert inspected["evidence_context"] is None
    assert inspected["human_recommended"] is False
    assert inspected["request"] is None


def test_inspect_reports_recommended_but_unavailable_human_capacity(api_server):
    for responder in human_api.runtime.responders:
        human_api.service.set_responder_active(responder.responder.id, False)

    status, inspected = post(
        api_server,
        {
            "action": "inspect",
            "text": "Research proves coffee consumption causes lower mortality.",
        },
    )

    assert status == 200
    assert inspected["resolution"]["path"] == "BOTH"
    assert inspected["human_recommended"] is True
    assert inspected["human_available"] is False
    assert inspected["routing_preview"] is None
    assert inspected["request"] is None


def test_evidence_to_human_to_answer_round_trip(api_server):
    text = (
        "Research proves coffee consumption causes lower mortality. "
        "Can someone explain what the study actually shows?"
    )

    post_url = "https://nsosyal.com/home"
    status, opened = post(
        api_server,
        {"action": "resolve", "text": text, "post_url": post_url},
    )
    assert status == 200
    request = opened["request"]
    assert opened["resolution"]["path"] == "BOTH"
    assert opened["human_recommended"] is True
    assert opened["human_available"] is True
    assert request["assigned_responder"]["id"] == "r_research"
    assert request["evidence_context"]["status"] in {"PARTIAL", "CONFLICTING"}
    assert request["social_context"] == {
        "platform": "NSosyal",
        "post_url": post_url,
        "published_observed": True,
    }
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
    assert author["request"]["social_context"]["post_url"] == post_url


@pytest.mark.parametrize(
    "post_url",
    [
        "http://nsosyal.com/home",
        "https://example.com/home",
        "javascript:alert(1)",
    ],
)
def test_resolve_rejects_untrusted_published_post_urls(api_server, post_url):
    status, payload = post(
        api_server,
        {
            "action": "resolve",
            "text": "Can someone help me understand this study?",
            "post_url": post_url,
        },
    )

    assert status == 400
    assert payload["error"] == "invalid_post_url"


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
