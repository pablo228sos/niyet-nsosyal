from __future__ import annotations

import pytest

from drsk.state_store import _redis_credentials_from_environment


def _clear(monkeypatch):
    for name in (
        "UPSTASH_REDIS_REST_URL",
        "UPSTASH_REDIS_REST_TOKEN",
        "KV_REST_API_URL",
        "KV_REST_API_TOKEN",
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
