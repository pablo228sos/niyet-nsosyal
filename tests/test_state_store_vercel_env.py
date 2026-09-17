from __future__ import annotations

import pytest

from drsk.state_store import (
    _default_state_namespace,
    _redis_credentials_from_environment,
)


def _clear(monkeypatch):
    for name in (
        "UPSTASH_REDIS_REST_URL",
        "UPSTASH_REDIS_REST_TOKEN",
        "KV_REST_API_URL",
        "KV_REST_API_TOKEN",
        "DRSK_STATE_NAMESPACE",
        "VERCEL_ENV",
    ):
        monkeypatch.delenv(name, raising=False)


def test_vercel_alias_pair_is_accepted(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("KV_REST_API_URL", "endpoint")
    monkeypatch.setenv("KV_REST_API_TOKEN", "credential")

    assert _redis_credentials_from_environment() == ("endpoint", "credential")


def test_direct_pair_has_priority_over_vercel_alias(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "direct-endpoint")
    monkeypatch.setenv("UPSTASH_REDIS_REST_TOKEN", "direct-credential")
    monkeypatch.setenv("KV_REST_API_URL", "alias-endpoint")
    monkeypatch.setenv("KV_REST_API_TOKEN", "alias-credential")

    assert _redis_credentials_from_environment() == (
        "direct-endpoint",
        "direct-credential",
    )


@pytest.mark.parametrize(
    "name",
    ["UPSTASH_REDIS_REST_URL", "KV_REST_API_URL"],
)
def test_half_configured_pair_is_rejected(monkeypatch, name):
    _clear(monkeypatch)
    monkeypatch.setenv(name, "endpoint")

    with pytest.raises(RuntimeError, match="state_store_configuration_incomplete"):
        _redis_credentials_from_environment()


def test_preview_uses_isolated_default_namespace(monkeypatch):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL_ENV", "preview")

    assert _default_state_namespace() == "jury-demo-v2-preview"


@pytest.mark.parametrize("vercel_env", ["production", "development", ""])
def test_non_preview_uses_jury_default_namespace(monkeypatch, vercel_env):
    _clear(monkeypatch)
    monkeypatch.setenv("VERCEL_ENV", vercel_env)

    assert _default_state_namespace() == "jury-demo-v2"
