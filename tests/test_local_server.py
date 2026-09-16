from __future__ import annotations

import http.client
import json
import threading
from http.server import ThreadingHTTPServer

import pytest

from api import human_help as human_api
from scripts.serve_local import LocalHandler


@pytest.fixture
def local_server():
    human_api.service.reset()
    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
        human_api.service.reset()


def request(address, method: str, path: str, payload: dict | None = None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    connection = http.client.HTTPConnection(*address, timeout=5)
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    result = response.status, json.loads(response.read())
    connection.close()
    return result


def test_local_human_help_post_delegates_the_domain_dispatch(local_server):
    text = (
        "Research proves coffee consumption causes lower mortality. "
        "Can someone explain what the study actually shows?"
    )

    status, inspected = request(
        local_server,
        "POST",
        "/api/human-help",
        {"action": "inspect", "text": text},
    )

    assert status == 200
    assert inspected["resolution"]["path"] == "BOTH"
    assert inspected["request"] is None
    assert inspected["human_recommended"] is True


def test_local_server_still_serves_the_main_api(local_server):
    status, payload = request(local_server, "GET", "/api")

    assert status == 200
    assert payload["status"] == "ok"
