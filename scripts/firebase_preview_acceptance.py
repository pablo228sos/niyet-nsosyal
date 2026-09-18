#!/usr/bin/env python3
"""Targeted acceptance runner for the isolated Firebase-backed NIYET Preview.

This script intentionally lives outside the shared CI workflow. It exercises the
real Firebase Auth + Vercel Preview + Firestore path without touching /live,
/api/human_help, the NSosyal extension, SOURCECHAIN, or production.

Required environment variables:
  NIYET_PREVIEW_URL
  NIYET_AUTHOR_EMAIL
  NIYET_AUTHOR_PASSWORD
  NIYET_RESPONDER_EMAIL
  NIYET_RESPONDER_PASSWORD

Optional third responder (required to prove Skip/Pause reallocation):
  NIYET_RESPONDER2_EMAIL
  NIYET_RESPONDER2_PASSWORD

Optional dedicated revocation account + fresh Admin credential (required to
prove check_revoked=True against a real revoked token):
  NIYET_REVOKE_EMAIL
  NIYET_REVOKE_PASSWORD
  FIREBASE_PROJECT_ID
  FIREBASE_CLIENT_EMAIL
  FIREBASE_PRIVATE_KEY

Do not reuse a compromised service-account key. The revocation check should be
run only with a freshly rotated Admin credential.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


TIMEOUT_SECONDS = 30
POLL_SECONDS = 15
SUPPORTED_INTENTS = ["ask", "feedback", "collaborate", "discuss"]


class AcceptanceFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class Account:
    email: str
    uid: str
    id_token: str


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise AcceptanceFailure(f"missing environment variable: {name}")
    return value


def _request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    token: str | None = None,
) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
            parsed = json.loads(raw.decode("utf-8")) if raw else {}
            return int(response.status), parsed if isinstance(parsed, dict) else {"value": parsed}
    except HTTPError as exc:
        raw = exc.read()
        try:
            parsed = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = {}
        return int(exc.code), parsed if isinstance(parsed, dict) else {"value": parsed}
    except URLError as exc:
        raise AcceptanceFailure(f"network failure for {url}: {exc.reason}") from exc


def _expect(status: int, expected: int, body: dict[str, Any], label: str) -> dict[str, Any]:
    if status != expected:
        code = body.get("error", {}).get("code") if isinstance(body.get("error"), dict) else None
        raise AcceptanceFailure(f"{label}: expected HTTP {expected}, got {status} ({code or 'no_error_code'})")
    return body


def _api_url(base: str, action: str | None = None, **query: str) -> str:
    url = f"{base.rstrip('/')}/api/niyet"
    values: dict[str, str] = dict(query)
    if action:
        values["action"] = action
    return f"{url}?{urlencode(values)}" if values else url


def _api_get(base: str, account: Account, action: str, **query: str) -> tuple[int, dict[str, Any]]:
    return _request_json(_api_url(base, action, **query), token=account.id_token)


def _api_post(base: str, account: Account, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    return _request_json(_api_url(base), method="POST", payload=payload, token=account.id_token)


def _firebase_config(base: str) -> dict[str, str]:
    status, body = _request_json(_api_url(base, "config"))
    value = _expect(status, 200, body, "preview Firebase config").get("firebase")
    if not isinstance(value, dict):
        raise AcceptanceFailure("preview Firebase config: malformed response")
    required = {"apiKey", "projectId", "authDomain", "appId"}
    missing = sorted(required - set(value))
    if missing:
        raise AcceptanceFailure(f"preview Firebase config missing fields: {', '.join(missing)}")
    return {str(key): str(item) for key, item in value.items()}


def _sign_in(api_key: str, email_env: str, password_env: str) -> Account:
    email = _required(email_env)
    password = _required(password_env)
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={quote(api_key)}"
    status, body = _request_json(
        url,
        method="POST",
        payload={"email": email, "password": password, "returnSecureToken": True},
    )
    if status != 200:
        message = body.get("error", {}).get("message") if isinstance(body.get("error"), dict) else None
        raise AcceptanceFailure(f"Firebase sign-in failed for {email_env}: HTTP {status} ({message or 'unknown'})")
    uid = body.get("localId")
    token = body.get("idToken")
    if not isinstance(uid, str) or not uid or not isinstance(token, str) or not token:
        raise AcceptanceFailure(f"Firebase sign-in returned no UID/token for {email_env}")
    return Account(email=email, uid=uid, id_token=token)


def _sync(base: str, account: Account) -> None:
    status, body = _api_post(base, account, {"action": "sync_user"})
    _expect(status, 200, body, f"sync_user {account.uid}")


def _profile(base: str, account: Account) -> dict[str, Any]:
    status, body = _api_get(base, account, "profile")
    return _expect(status, 200, body, f"profile {account.uid}")["responder_profile"]


def _configure_responder(base: str, account: Account, marker: str, *, capacity: int = 50) -> dict[str, Any]:
    status, body = _api_post(
        base,
        account,
        {
            "action": "update_profile",
            "topics": [marker, "python", "fastapi", "backend", "firebase"],
            "profile_text": f"Preview acceptance responder for {marker} Python FastAPI backend Firebase requests.",
            "languages": ["en"],
            "willing_intents": SUPPORTED_INTENTS,
            "willing": True,
            "active": True,
            "capacity_total": capacity,
            "quality_threshold": 0.0,
        },
    )
    return _expect(status, 200, body, f"update_profile {account.uid}")["responder_profile"]


def _create_request(base: str, author: Account, marker: str, key: str) -> dict[str, Any]:
    status, body = _api_post(
        base,
        author,
        {
            "action": "create_request",
            "text": f"Can someone help review {marker} Python FastAPI backend architecture?",
            "intent": "discuss",  # deliberately untrusted; server derives the routing intent.
            "author_uid": "forged-client-uid",
            "idempotency_key": key,
        },
    )
    request = _expect(status, 200, body, "create_request").get("request")
    if not isinstance(request, dict):
        raise AcceptanceFailure("create_request returned no request object")
    if request.get("author_uid") != author.uid:
        raise AcceptanceFailure("actor UID spoof protection failed")
    return request


def _inbox(base: str, account: Account) -> list[dict[str, Any]]:
    status, body = _api_get(base, account, "inbox")
    values = _expect(status, 200, body, f"inbox {account.uid}").get("assignments")
    return values if isinstance(values, list) else []


def _find_assignment(base: str, account: Account, request_id: str, *, timeout: int = POLL_SECONDS) -> dict[str, Any] | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        for assignment in _inbox(base, account):
            if assignment.get("request_id") == request_id:
                return assignment
        time.sleep(1)
    return None


def _author_request(base: str, author: Account, request_id: str) -> dict[str, Any]:
    status, body = _api_get(base, author, "request", request_id=request_id)
    request = _expect(status, 200, body, "author request refresh").get("request")
    if not isinstance(request, dict):
        raise AcceptanceFailure("author request refresh returned no request")
    return request


def _wait_for_reassignment(
    base: str,
    author: Account,
    request_id: str,
    old_assignment_id: str,
    *,
    timeout: int = POLL_SECONDS,
) -> dict[str, Any] | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        request = _author_request(base, author, request_id)
        assignment_id = request.get("current_assignment_id")
        if assignment_id and assignment_id != old_assignment_id:
            return request
        time.sleep(1)
    return None


def _direct_firestore_denial(config: dict[str, str], account: Account) -> None:
    project_id = quote(config["projectId"], safe="")
    uid = quote(account.uid, safe="")
    api_key = quote(config["apiKey"], safe="")
    url = (
        f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/"
        f"documents/users/{uid}?key={api_key}"
    )
    anonymous_status, _ = _request_json(url)
    if anonymous_status not in {401, 403}:
        raise AcceptanceFailure(f"unauthenticated direct Firestore access was not denied: HTTP {anonymous_status}")
    authenticated_status, _ = _request_json(url, token=account.id_token)
    if authenticated_status != 403:
        raise AcceptanceFailure(f"authenticated direct Firestore access was not denied: HTTP {authenticated_status}")


def _revoked_token_check(base: str, api_key: str) -> bool:
    email = os.getenv("NIYET_REVOKE_EMAIL", "").strip()
    password = os.getenv("NIYET_REVOKE_PASSWORD", "").strip()
    project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "").strip()
    private_key = os.getenv("FIREBASE_PRIVATE_KEY", "").strip().replace("\\n", "\n")
    values = [email, password, project_id, client_email, private_key]
    if not any(values):
        return False
    if not all(values):
        raise AcceptanceFailure("revocation acceptance variables are partially configured")

    account = _sign_in(api_key, "NIYET_REVOKE_EMAIL", "NIYET_REVOKE_PASSWORD")
    time.sleep(1.2)  # ensure revocation timestamp is later than the issued token auth_time.

    import firebase_admin
    from firebase_admin import auth, credentials

    app_name = f"drsk-niyet-acceptance-{uuid.uuid4().hex}"
    app = firebase_admin.initialize_app(
        credentials.Certificate(
            {
                "type": "service_account",
                "project_id": project_id,
                "client_email": client_email,
                "private_key": private_key,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        ),
        {"projectId": project_id},
        name=app_name,
    )
    try:
        auth.revoke_refresh_tokens(account.uid, app=app)
        deadline = time.time() + 10
        while time.time() < deadline:
            status, _ = _api_get(base, account, "me")
            if status == 401:
                return True
            time.sleep(1)
    finally:
        firebase_admin.delete_app(app)
    raise AcceptanceFailure("real revoked Firebase token was still accepted by Preview")


def main() -> int:
    base = _required("NIYET_PREVIEW_URL").rstrip("/")
    config = _firebase_config(base)
    print(f"Preview: {base}")
    print(f"Firebase project: {config['projectId']}")

    author = _sign_in(config["apiKey"], "NIYET_AUTHOR_EMAIL", "NIYET_AUTHOR_PASSWORD")
    responder = _sign_in(config["apiKey"], "NIYET_RESPONDER_EMAIL", "NIYET_RESPONDER_PASSWORD")
    if author.uid == responder.uid:
        raise AcceptanceFailure("author and responder must be different Firebase accounts")

    marker = f"niyet-preview-{uuid.uuid4().hex[:12]}"
    _sync(base, author)
    _sync(base, responder)
    _configure_responder(base, responder, marker)
    print("PASS real Firebase login + user sync + responder profile")

    # Invalid token must be rejected before any state access.
    invalid_status, _ = _request_json(_api_url(base, "me"), token="definitely-not-a-firebase-token")
    if invalid_status != 401:
        raise AcceptanceFailure(f"invalid token rejection failed: HTTP {invalid_status}")
    print("PASS invalid token rejected")

    # Baseline author -> route -> responder -> Accept -> Answer -> persisted author result.
    key = f"preview_{uuid.uuid4().hex}"
    created = _create_request(base, author, marker, key)
    request_id = str(created.get("id") or created.get("request_id") or "")
    if not request_id:
        raise AcceptanceFailure("created request has no id")
    assignment = _find_assignment(base, responder, request_id)
    if assignment is None:
        assigned = _author_request(base, author, request_id).get("assigned_responder")
        raise AcceptanceFailure(f"request was not routed to expected responder; observed={assigned}")
    assignment_id = str(assignment.get("id") or assignment.get("assignment_id") or "")
    if not assignment_id:
        raise AcceptanceFailure("routed assignment has no id")
    print("PASS request routed to authenticated responder inbox")

    # Cross-user authorization on author request and assignment mutation.
    status, _ = _api_get(base, responder, "request", request_id=request_id)
    if status != 403:
        raise AcceptanceFailure(f"cross-user request read was not denied: HTTP {status}")
    status, _ = _api_post(base, author, {"action": "accept", "assignment_id": assignment_id})
    if status != 403:
        raise AcceptanceFailure(f"cross-user assignment Accept was not denied: HTTP {status}")
    print("PASS cross-user request/assignment access denied")

    before = int(_profile(base, responder)["capacity_remaining"])
    status, body = _api_post(base, responder, {"action": "accept", "assignment_id": assignment_id})
    accepted = _expect(status, 200, body, "Accept")["assignment"]
    if accepted.get("status") != "ACCEPTED":
        raise AcceptanceFailure("Accept did not transition assignment to ACCEPTED")
    after_first = int(_profile(base, responder)["capacity_remaining"])
    status, body = _api_post(base, responder, {"action": "accept", "assignment_id": assignment_id})
    _expect(status, 200, body, "duplicate Accept")
    after_duplicate = int(_profile(base, responder)["capacity_remaining"])
    if after_first != before - 1 or after_duplicate != after_first:
        raise AcceptanceFailure("Accept idempotency/capacity accounting failed")
    print("PASS Accept is idempotent and consumes capacity once")

    answer_text = f"Preview acceptance answer {marker}"
    status, body = _api_post(
        base,
        responder,
        {"action": "answer", "assignment_id": assignment_id, "answer": answer_text},
    )
    answered = _expect(status, 200, body, "Answer")["assignment"]
    if answered.get("status") != "ANSWERED":
        raise AcceptanceFailure("Answer did not transition assignment to ANSWERED")
    resolved = _author_request(base, author, request_id)
    if resolved.get("status") != "ANSWERED" or resolved.get("answer") != answer_text:
        raise AcceptanceFailure("author did not receive persisted resolved result")
    print("PASS Answer persisted and author sees resolved result")

    # Reusing the same operation key must not create a duplicate request or spend capacity again.
    retried = _create_request(base, author, marker, key)
    retry_id = str(retried.get("id") or retried.get("request_id") or "")
    if retry_id != request_id:
        raise AcceptanceFailure("idempotent request retry created a second request")
    if int(_profile(base, responder)["capacity_remaining"]) != after_duplicate:
        raise AcceptanceFailure("idempotent request retry changed responder capacity")
    print("PASS request retry is idempotent and does not double-spend capacity")

    _direct_firestore_denial(config, author)
    print("PASS direct unauthenticated/authenticated Firestore client access denied")

    # Pause/Resume itself is testable with two accounts.
    status, body = _api_post(base, responder, {"action": "pause"})
    paused = _expect(status, 200, body, "Pause")["responder_profile"]
    if paused.get("paused") is not True:
        raise AcceptanceFailure("Pause did not persist paused=true")
    status, body = _api_post(base, responder, {"action": "resume"})
    resumed = _expect(status, 200, body, "Resume")["responder_profile"]
    if resumed.get("paused") is not False:
        raise AcceptanceFailure("Resume did not persist paused=false")
    print("PASS Pause/Resume persisted")

    complete = True
    responder2_email = os.getenv("NIYET_RESPONDER2_EMAIL", "").strip()
    responder2_password = os.getenv("NIYET_RESPONDER2_PASSWORD", "").strip()
    if responder2_email or responder2_password:
        if not responder2_email or not responder2_password:
            raise AcceptanceFailure("third responder credentials are partially configured")
        responder2 = _sign_in(config["apiKey"], "NIYET_RESPONDER2_EMAIL", "NIYET_RESPONDER2_PASSWORD")
        if responder2.uid in {author.uid, responder.uid}:
            raise AcceptanceFailure("third responder must be a distinct Firebase account")
        _sync(base, responder2)
        _configure_responder(base, responder2, marker)

        # Skip -> same request must reallocate to the other eligible responder.
        skip_key = f"preview_{uuid.uuid4().hex}"
        skip_request = _create_request(base, author, marker, skip_key)
        skip_request_id = str(skip_request.get("id") or skip_request.get("request_id") or "")
        first = _find_assignment(base, responder, skip_request_id, timeout=4)
        first_actor = responder
        other_actor = responder2
        if first is None:
            first = _find_assignment(base, responder2, skip_request_id, timeout=4)
            first_actor, other_actor = responder2, responder
        if first is None:
            raise AcceptanceFailure("Skip scenario: neither responder received the request")
        old_id = str(first.get("id") or first.get("assignment_id") or "")
        status, body = _api_post(base, first_actor, {"action": "skip", "assignment_id": old_id})
        _expect(status, 200, body, "Skip")
        replacement = _find_assignment(base, other_actor, skip_request_id)
        if replacement is None or str(replacement.get("id") or replacement.get("assignment_id")) == old_id:
            raise AcceptanceFailure("Skip did not reallocate to the other eligible responder")
        print("PASS Skip reallocates to a different eligible responder")

        # Pause while PENDING -> old assignment cancelled and same request reallocated.
        pause_key = f"preview_{uuid.uuid4().hex}"
        pause_request = _create_request(base, author, marker, pause_key)
        pause_request_id = str(pause_request.get("id") or pause_request.get("request_id") or "")
        first = _find_assignment(base, responder, pause_request_id, timeout=4)
        first_actor = responder
        other_actor = responder2
        if first is None:
            first = _find_assignment(base, responder2, pause_request_id, timeout=4)
            first_actor, other_actor = responder2, responder
        if first is None:
            raise AcceptanceFailure("Pause reallocation scenario: neither responder received the request")
        old_id = str(first.get("id") or first.get("assignment_id") or "")
        status, body = _api_post(base, first_actor, {"action": "pause"})
        _expect(status, 200, body, "Pause pending responder")
        refreshed = _wait_for_reassignment(base, author, pause_request_id, old_id)
        if refreshed is None:
            raise AcceptanceFailure("Pause did not reallocate pending request")
        replacement = _find_assignment(base, other_actor, pause_request_id)
        if replacement is None:
            raise AcceptanceFailure("Pause reallocation was not visible in the other responder inbox")
        status, body = _api_post(base, first_actor, {"action": "resume"})
        resumed = _expect(status, 200, body, "Resume paused responder")["responder_profile"]
        if resumed.get("paused") is not False:
            raise AcceptanceFailure("Resume after reallocation did not persist")
        print("PASS Pause releases pending assignment, reallocates, and Resume restores eligibility")
    else:
        complete = False
        print("SKIP Skip/Pause reallocation proof: NIYET_RESPONDER2_* not configured")

    if _revoked_token_check(base, config["apiKey"]):
        print("PASS real revoked Firebase token rejected")
    else:
        complete = False
        print("SKIP real revoked-token proof: dedicated revocation account/Admin credential not configured")

    if complete:
        print("ACCEPTANCE RESULT: PASS")
        return 0
    print("ACCEPTANCE RESULT: INCOMPLETE (baseline passed; optional production gates remain)")
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AcceptanceFailure as exc:
        print(f"ACCEPTANCE RESULT: FAIL — {exc}", file=sys.stderr)
        raise SystemExit(1)
