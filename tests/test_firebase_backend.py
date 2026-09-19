from __future__ import annotations

import pytest

import drsk.firebase_backend as backend
from drsk.firebase_backend import FirebaseConfigurationError, firebase_credentials_from_environment, get_firebase_app


def test_firebase_credentials_normalize_escaped_newlines() -> None:
    config = firebase_credentials_from_environment(
        {
            "FIREBASE_PROJECT_ID": "drsk-web",
            "FIREBASE_CLIENT_EMAIL": "firebase-admin@example.test",
            "FIREBASE_PRIVATE_KEY": "line-one\\nline-two\\n",
        }
    )
    assert config.project_id == "drsk-web"
    assert "\\n" not in config.private_key
    assert config.private_key.splitlines()[1] == "line-two"


def test_partial_firebase_credentials_fail_closed() -> None:
    with pytest.raises(FirebaseConfigurationError, match="firebase_configuration_incomplete"):
        firebase_credentials_from_environment({"FIREBASE_PROJECT_ID": "drsk-web"})


def test_missing_firebase_credentials_fail_closed() -> None:
    with pytest.raises(FirebaseConfigurationError, match="firebase_configuration_missing"):
        firebase_credentials_from_environment({})


def test_partial_emulator_configuration_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "drsk-web-test")
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    with pytest.raises(FirebaseConfigurationError, match="firebase_emulator_configuration_incomplete"):
        get_firebase_app()


def test_token_verification_checks_revocation(monkeypatch) -> None:
    from firebase_admin import auth

    seen = {}
    fake_app = object()
    monkeypatch.setattr(backend, "get_firebase_app", lambda: fake_app)

    def verify(token, *, app, check_revoked):
        seen.update(token=token, app=app, check_revoked=check_revoked)
        return {"uid": "verified"}

    monkeypatch.setattr(auth, "verify_id_token", verify)
    assert backend.verify_firebase_token("signed-token")["uid"] == "verified"
    assert seen == {"token": "signed-token", "app": fake_app, "check_revoked": True}


def test_firebase_admin_uses_dedicated_named_app(monkeypatch) -> None:
    import firebase_admin

    seen = {}
    fake_app = object()

    monkeypatch.setattr(backend, "_app", None)
    monkeypatch.delenv("FIRESTORE_EMULATOR_HOST", raising=False)
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "drsk-web")
    monkeypatch.setenv("FIREBASE_CLIENT_EMAIL", "firebase-admin@example.test")
    monkeypatch.setenv("FIREBASE_PRIVATE_KEY", "test-private-key")

    def get_app(name):
        seen["get_name"] = name
        raise ValueError("missing")

    def initialize_app(credential=None, options=None, name=None):
        seen.update(init_name=name, options=options)
        return fake_app

    monkeypatch.setattr(firebase_admin, "get_app", get_app)
    monkeypatch.setattr(firebase_admin, "initialize_app", initialize_app)
    monkeypatch.setattr("firebase_admin.credentials.Certificate", lambda value: value)

    assert backend.get_firebase_app() is fake_app
    assert seen["get_name"] == "drsk-niyet"
    assert seen["init_name"] == "drsk-niyet"
    assert seen["options"] == {"projectId": "drsk-web"}
