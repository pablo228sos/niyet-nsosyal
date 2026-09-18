from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_firebase_auth_and_persistent_niyet_controls_are_on_live_surface() -> None:
    html = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
    client = (ROOT / "web" / "firebase-client.js").read_text(encoding="utf-8")
    live = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    for control in (
        'id="signUpEmail"',
        'id="signInEmail"',
        'id="signInGoogle"',
        'id="signOutUser"',
        'id="responderProfileForm"',
    ):
        assert control in html
    assert 'type="module" src="/live.js"' in html
    assert "browserLocalPersistence" in client
    assert "Authorization: `Bearer ${token}`" in client
    assert "author_uid" not in client
    assert "/api/human-help" not in live
    assert "resetDemo" not in live
    assert "acceptAssignment" in live
    assert "answerAssignment" in live


def test_browser_has_no_direct_firestore_data_surface() -> None:
    client = (ROOT / "web" / "firebase-client.js").read_text(encoding="utf-8")
    rules = (ROOT / "firestore.rules").read_text(encoding="utf-8")
    assert "firebase-firestore" not in client
    assert "getFirestore" not in client
    assert "allow read, write: if true" not in rules
    assert "allow read, write: if false" in rules
    assert rules.count("allow ") == 1


def test_proxy_forwards_authenticated_niyet_without_cookies() -> None:
    worker = (ROOT / "scripts" / "site_worker.mjs").read_text(encoding="utf-8")
    assert "url.pathname === '/api/niyet'" in worker
    assert "upstreamHeaders.Authorization = authorization" in worker
    assert "request.headers.get('cookie')" not in worker


def test_legacy_browser_trusted_mutations_are_disabled() -> None:
    api = (ROOT / "api" / "index.py").read_text(encoding="utf-8")
    human_api = (ROOT / "api" / "human_help.py").read_text(encoding="utf-8")
    assert 'self._json(401, {"error": "firebase_auth_required"})' in api
    assert 'self._json(410, {"error": "legacy_demo_endpoint_disabled"})' in human_api


def test_firestore_assignment_queries_have_required_composite_indexes() -> None:
    repository = (ROOT / "src" / "drsk" / "niyet_persistence.py").read_text(encoding="utf-8")
    indexes = (ROOT / "firestore.indexes.json").read_text(encoding="utf-8")
    assert '.where("willing", "==", True)' in repository
    assert '.where("responder_uid", "==", uid)' in repository
    assert '.where("status", "==", "PENDING")' in repository
    assert '.where("status", "in", sorted(ACTIVE_ASSIGNMENT_STATUSES))' in repository
    assert '.where("expires_at", "<=", _now())' in repository
    assert '"collectionGroup": "assignments"' in indexes
    assert '"fieldPath": "responder_uid"' in indexes
    assert '"fieldPath": "status"' in indexes
    assert '"fieldPath": "expires_at"' in indexes
