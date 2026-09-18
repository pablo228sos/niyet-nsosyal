from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main_file(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"origin/main:{path}"], cwd=ROOT)


def restore_from_main(paths: list[str]) -> None:
    for path in paths:
        target = ROOT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(main_file(path))


def replace_once(path: str, old: str, new: str, label: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# Keep the judge-facing NSosyal surface exactly on main. Firebase is an additive
# backend/auth/persistence track until its Preview acceptance is complete.
restore_from_main([
    "api/human_help.py",
    "api/index.py",
    "src/drsk/state_store.py",
    "scripts/build_site.py",
    "scripts/serve_local.py",
    "scripts/site_worker.mjs",
    "web/live-ux.css",
    "web/live.html",
    "web/live.js",
    "tests/test_api.py",
    "tests/test_live_surface.py",
    "tests/test_site_delivery.py",
    "vercel.json",
])

for obsolete in (
    "web/firebase-client.js",
    "tests/test_firebase_web_contract.py",
):
    target = ROOT / obsolete
    if target.exists():
        target.unlink()

# Capacity parity: the existing NIYET runtime models remaining_slots as an
# attention/daily budget. Accept consumes a slot; Answer completes the request
# but does not silently replenish the consumed budget.
replace_once(
    "src/drsk/niyet_persistence.py",
    '''            profile = self.profiles.get(uid)\n            if profile is not None:\n                profile["capacity_remaining"] = min(\n                    int(profile["capacity_total"]), int(profile["capacity_remaining"]) + 1\n                )\n                profile["updated_at"] = now\n''',
    '''            # Preserve the existing NIYET attention-budget contract:\n            # Accept consumes capacity; completing the answer does not restore it.\n''',
    "memory answer capacity",
)
replace_once(
    "src/drsk/niyet_persistence.py",
    '''            profile_ref = self.client.collection("responder_profiles").document(uid)\n            profile_snapshot = profile_ref.get(transaction=transaction)\n            if not profile_snapshot.exists:\n                raise DomainError("responder_profile_not_found", 404)\n            profile = profile_snapshot.to_dict() or {}\n''',
    '''            # Capacity is an attention/daily budget consumed on Accept,\n            # not a concurrent-work slot released on Answer.\n''',
    "firestore answer profile read",
)
replace_once(
    "src/drsk/niyet_persistence.py",
    '''            capacity_total = int(profile.get("capacity_total", 0))\n            capacity_remaining = int(profile.get("capacity_remaining", 0))\n            transaction.update(profile_ref, {\n                "capacity_remaining": min(capacity_total, capacity_remaining + 1),\n                "updated_at": firestore.SERVER_TIMESTAMP,\n            })\n''',
    "",
    "firestore answer capacity",
)

capacity_test = '''from __future__ import annotations\n\nfrom drsk.firebase_auth import AuthenticatedUser\nfrom drsk.niyet_persistence import MemoryNiyetRepository, NiyetService\n\n\ndef actor(uid: str) -> AuthenticatedUser:\n    return AuthenticatedUser(\n        uid=uid,\n        email=f"{uid}@example.test",\n        display_name=uid.title(),\n        photo_url=None,\n        provider_ids=("password",),\n        claims={"uid": uid},\n    )\n\n\ndef configure_responder(service: NiyetService, uid: str, *, capacity: int = 1) -> None:\n    service.sync_user(actor(uid))\n    service.update_responder_profile(\n        actor(uid),\n        {\n            "topics": ["python", "backend"],\n            "languages": ["en"],\n            "willing": True,\n            "active": True,\n            "capacity_total": capacity,\n        },\n    )\n\n\ndef test_answer_does_not_replenish_consumed_attention_budget() -> None:\n    repository = MemoryNiyetRepository()\n    service = NiyetService(repository)\n    service.sync_user(actor("author-a"))\n    service.sync_user(actor("author-b"))\n    configure_responder(service, "responder", capacity=1)\n\n    first = service.create_request(\n        actor("author-a"),\n        text="Need Python backend help",\n        intent="ask",\n    )\n    first_assignment_id = first["current_assignment_id"]\n    assert first_assignment_id\n\n    service.accept(actor("responder"), first_assignment_id)\n    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 0\n\n    second = service.create_request(\n        actor("author-b"),\n        text="Need Python backend review",\n        intent="ask",\n    )\n    assert second["current_assignment_id"] is None\n\n    service.answer(actor("responder"), first_assignment_id, "Use a transaction.")\n    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 0\n    assert repository.get_request(second["id"])["current_assignment_id"] is None\n\n    # Retrying the same answer remains idempotent and cannot change budget.\n    service.answer(actor("responder"), first_assignment_id, "Use a transaction.")\n    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 0\n'''
(ROOT / "tests/test_niyet_capacity_lifecycle.py").write_text(capacity_test, encoding="utf-8")

replace_once(
    "tests/test_niyet_persistence.py",
    '''    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 2\n    saved = service.get_author_request(actor("author"), request["id"])\n''',
    '''    # Answer does not replenish the attention/daily budget consumed by Accept.\n    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 1\n    saved = service.get_author_request(actor("author"), request["id"])\n''',
    "persistence capacity assertion",
)

emulator_test = '''from __future__ import annotations\n\nimport os\nimport urllib.error\nimport urllib.request\n\nimport pytest\n\nfrom drsk.firebase_auth import AuthenticatedUser\nfrom drsk.niyet_persistence import FirestoreNiyetRepository, NiyetService\n\n\npytestmark = pytest.mark.skipif(\n    not os.getenv("FIRESTORE_EMULATOR_HOST"),\n    reason="start Firebase Emulator Suite and set FIRESTORE_EMULATOR_HOST",\n)\n\n\ndef actor(uid: str) -> AuthenticatedUser:\n    return AuthenticatedUser(uid, f"{uid}@example.test", uid, None, ("password",), {"uid": uid})\n\n\n@pytest.fixture\ndef firestore_client():\n    pytest.importorskip("firebase_admin")\n    from google.auth.credentials import AnonymousCredentials\n    from google.cloud import firestore\n\n    client = firestore.Client(project="drsk-web-test", credentials=AnonymousCredentials())\n    collections = ("events", "assignments", "niyet_requests", "posts", "responder_profiles", "users")\n    for collection in collections:\n        for snapshot in client.collection(collection).stream():\n            snapshot.reference.delete()\n    yield client\n    for collection in collections:\n        for snapshot in client.collection(collection).stream():\n            snapshot.reference.delete()\n\n\ndef test_firestore_crud_assignment_and_idempotent_accept(firestore_client) -> None:\n    service = NiyetService(FirestoreNiyetRepository(firestore_client))\n    service.sync_user(actor("author"))\n    service.sync_user(actor("responder"))\n    service.update_responder_profile(\n        actor("responder"),\n        {"topics": ["python", "backend"], "languages": ["en"], "willing": True, "active": True, "capacity_total": 2},\n    )\n    request = service.create_request(actor("author"), text="Python backend help", intent="ask")\n    assignment_id = request["current_assignment_id"]\n    assert assignment_id\n    service.accept(actor("responder"), assignment_id)\n    service.accept(actor("responder"), assignment_id)\n    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 1\n    service.answer(actor("responder"), assignment_id, "Persisted answer")\n    service.answer(actor("responder"), assignment_id, "Persisted answer")\n    saved = service.get_author_request(actor("author"), request["id"])\n    assert saved["status"] == "ANSWERED"\n    assert saved["answer"] == "Persisted answer"\n    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 1\n\n\ndef test_firestore_pause_releases_and_reallocates_pending_assignment(firestore_client) -> None:\n    service = NiyetService(FirestoreNiyetRepository(firestore_client))\n    service.sync_user(actor("author"))\n    for uid in ("first", "second"):\n        service.sync_user(actor(uid))\n        service.update_responder_profile(\n            actor(uid),\n            {"topics": ["python"], "languages": ["en"], "willing": True, "active": True, "capacity_total": 2},\n        )\n    request = service.create_request(actor("author"), text="Python help", intent="ask")\n    old = service.repository.get_assignment(request["current_assignment_id"])\n    service.pause(actor(old["responder_uid"]))\n    refreshed = service.repository.get_request(request["id"])\n    replacement = service.repository.get_assignment(refreshed["current_assignment_id"])\n    assert service.repository.get_assignment(old["id"])["status"] == "CANCELLED"\n    assert replacement["responder_uid"] != old["responder_uid"]\n\n\ndef test_firestore_rules_deny_direct_client_rest_access(firestore_client) -> None:\n    # Server/Admin persistence can write, while an unauthenticated browser-style\n    # REST read must still be denied by firestore.rules.\n    firestore_client.collection("users").document("browser-probe").set({"uid": "browser-probe"})\n    host = os.environ["FIRESTORE_EMULATOR_HOST"]\n    url = (\n        f"http://{host}/v1/projects/drsk-web-test/databases/(default)/"\n        "documents/users/browser-probe"\n    )\n    request = urllib.request.Request(url, headers={"Accept": "application/json"})\n    with pytest.raises(urllib.error.HTTPError) as caught:\n        urllib.request.urlopen(request, timeout=5)\n    assert caught.value.code == 403\n'''
(ROOT / "tests/test_firestore_emulator.py").write_text(emulator_test, encoding="utf-8")

backend_test = '''from __future__ import annotations\n\nimport pytest\n\nimport drsk.firebase_backend as backend\nfrom drsk.firebase_backend import FirebaseConfigurationError, firebase_credentials_from_environment, get_firebase_app\n\n\ndef test_firebase_credentials_normalize_escaped_newlines() -> None:\n    config = firebase_credentials_from_environment(\n        {\n            "FIREBASE_PROJECT_ID": "drsk-web",\n            "FIREBASE_CLIENT_EMAIL": "firebase-admin@example.test",\n            "FIREBASE_PRIVATE_KEY": "line-one\\\\nline-two\\\\n",\n        }\n    )\n    assert config.project_id == "drsk-web"\n    assert "\\\\n" not in config.private_key\n    assert config.private_key.splitlines()[1] == "line-two"\n\n\ndef test_partial_firebase_credentials_fail_closed() -> None:\n    with pytest.raises(FirebaseConfigurationError, match="firebase_configuration_incomplete"):\n        firebase_credentials_from_environment({"FIREBASE_PROJECT_ID": "drsk-web"})\n\n\ndef test_missing_firebase_credentials_fail_closed() -> None:\n    with pytest.raises(FirebaseConfigurationError, match="firebase_configuration_missing"):\n        firebase_credentials_from_environment({})\n\n\ndef test_partial_emulator_configuration_fails_closed(monkeypatch) -> None:\n    monkeypatch.setenv("FIREBASE_PROJECT_ID", "drsk-web-test")\n    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")\n    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)\n    with pytest.raises(FirebaseConfigurationError, match="firebase_emulator_configuration_incomplete"):\n        get_firebase_app()\n\n\ndef test_token_verification_checks_revocation(monkeypatch) -> None:\n    from firebase_admin import auth\n\n    seen = {}\n    fake_app = object()\n    monkeypatch.setattr(backend, "get_firebase_app", lambda: fake_app)\n\n    def verify(token, *, app, check_revoked):\n        seen.update(token=token, app=app, check_revoked=check_revoked)\n        return {"uid": "verified"}\n\n    monkeypatch.setattr(auth, "verify_id_token", verify)\n    assert backend.verify_firebase_token("signed-token")["uid"] == "verified"\n    assert seen == {"token": "signed-token", "app": fake_app, "check_revoked": True}\n'''
(ROOT / "tests/test_firebase_backend.py").write_text(backend_test, encoding="utf-8")

workflow = '''name: tests\n\non:\n  push:\n  pull_request:\n\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: "3.11"\n      - run: node --check web/app.js\n      - run: node --check web/lab.js\n      - run: node --check web/live.js\n      - run: node --check web/live-motion.js\n      - run: node --check web/live-theme.js\n      - run: node --check demo/nsosyal-overlay/background.js\n      - run: node --check demo/nsosyal-overlay/content-v2.js\n      - run: python scripts/build_site.py\n      - run: python scripts/package_nsosyal_overlay.py\n      - run: python -m pip install --upgrade pip\n      - run: pip install -c constraints.txt -e . pytest\n      - run: python -m compileall -q src api scripts experiments\n      - run: pytest -q\n      - run: python experiments/evaluate_matching_draft.py\n      - run: python experiments/evaluate_sourcechain_v0.py\n      - run: python scripts/validate_annotations.py data/intent_seed_v1.csv\n      - run: python scripts/validate_annotations.py data/response_gate_seed_v1.csv\n      - run: python scripts/validate_sourcebench.py data/sourcebench_tr\n      - uses: actions/upload-artifact@v4\n        with:\n          name: drsk-nsosyal-overlay-${{ github.sha }}\n          path: dist/drsk-nsosyal-overlay.zip\n          if-no-files-found: error\n          retention-days: 7\n\n  firestore-emulator:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: "3.11"\n      - uses: actions/setup-node@v4\n        with:\n          node-version: "24"\n      - uses: actions/setup-java@v4\n        with:\n          distribution: "temurin"\n          java-version: "21"\n      - run: python -m pip install --upgrade pip\n      - run: pip install -c constraints.txt -e . pytest\n      - run: npm install --global firebase-tools\n      - run: firebase emulators:exec --only firestore --project drsk-web-test "python -m pytest -q tests/test_firestore_emulator.py"\n'''
(ROOT / ".github/workflows/tests.yml").write_text(workflow, encoding="utf-8")

print("Firebase hardening track changes staged in working tree")
