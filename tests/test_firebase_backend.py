from __future__ import annotations

import pytest

from drsk.firebase_backend import (
    FirebaseConfigurationError,
    firebase_credentials_from_environment,
    get_firebase_app,
)
from drsk.state_store import state_store_from_environment


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


def test_legacy_state_store_cannot_shadow_configured_firestore(monkeypatch) -> None:
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "drsk-web")
    monkeypatch.setenv("FIREBASE_CLIENT_EMAIL", "firebase-admin@example.test")
    monkeypatch.setenv("FIREBASE_PRIVATE_KEY", "private-key")
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="structured_firestore_repository_required"):
        state_store_from_environment({"requests": {}})


def test_legacy_memory_state_is_forbidden_in_production(monkeypatch) -> None:
    for name in (
        "FIREBASE_PROJECT_ID", "FIREBASE_CLIENT_EMAIL", "FIREBASE_PRIVATE_KEY",
        "FIRESTORE_EMULATOR_HOST", "UPSTASH_REDIS_REST_URL", "UPSTASH_REDIS_REST_TOKEN",
        "KV_REST_API_URL", "KV_REST_API_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("VERCEL_ENV", "production")
    with pytest.raises(RuntimeError, match="legacy_demo_state_disabled_in_production"):
        state_store_from_environment({"requests": {}})


def test_partial_emulator_configuration_fails_closed(monkeypatch) -> None:
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "drsk-web-test")
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
    monkeypatch.delenv("FIREBASE_AUTH_EMULATOR_HOST", raising=False)
    with pytest.raises(FirebaseConfigurationError, match="firebase_emulator_configuration_incomplete"):
        get_firebase_app()
