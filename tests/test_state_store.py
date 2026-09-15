from __future__ import annotations

import json

import pytest

from drsk.state_store import (
    MemoryStateStore,
    UpstashRedisStateStore,
    state_store_from_environment,
)


class FakeUpstashStore(UpstashRedisStateStore):
    def __init__(self, initial_state, *, inject_conflict: bool = False):
        self.remote: dict[str, str] = {}
        self.inject_conflict = inject_conflict
        self.eval_calls = 0
        super().__init__(
            url="https://example.upstash.invalid",
            token="test-token",
            key="drsk:test",
            initial_state=initial_state,
            ttl_seconds=300,
        )

    def _command(self, command):
        name = command[0]
        if name == "GET":
            return self.remote.get(command[1])
        if name == "SET":
            key, value = command[1], command[2]
            if "NX" in command and key in self.remote:
                return None
            self.remote[key] = value
            return "OK"
        if name == "EVAL":
            self.eval_calls += 1
            key = command[3]
            expected = command[4]
            updated = command[5]
            if self.inject_conflict and self.eval_calls == 1:
                concurrent = json.loads(self.remote[key])
                concurrent["counter"] = 10
                self.remote[key] = json.dumps(
                    concurrent,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                return 0
            if self.remote.get(key) != expected:
                return 0
            self.remote[key] = updated
            return 1
        raise AssertionError(f"unexpected command: {command}")


def test_memory_store_does_not_leak_mutable_reads():
    store = MemoryStateStore({"items": [1]})
    snapshot = store.read()
    snapshot["items"].append(2)

    assert store.read() == {"items": [1]}


def test_memory_store_commits_one_transactional_mutation():
    store = MemoryStateStore({"counter": 0})

    result = store.mutate(lambda state: state.__setitem__("counter", 1) or "done")

    assert result == "done"
    assert store.read()["counter"] == 1


def test_upstash_store_retries_against_latest_snapshot_after_conflict():
    store = FakeUpstashStore({"counter": 0}, inject_conflict=True)

    def increment(state):
        state["counter"] += 1
        return state["counter"]

    result = store.mutate(increment)

    assert result == 11
    assert store.read()["counter"] == 11
    assert store.eval_calls == 2


def test_environment_without_credentials_uses_explicit_memory_fallback(monkeypatch):
    monkeypatch.delenv("UPSTASH_REDIS_REST_URL", raising=False)
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)

    store = state_store_from_environment({"counter": 0})

    assert store.backend_name == "memory"
    assert store.durable is False


def test_environment_rejects_half_configured_durable_store(monkeypatch):
    monkeypatch.setenv("UPSTASH_REDIS_REST_URL", "https://example.upstash.invalid")
    monkeypatch.delenv("UPSTASH_REDIS_REST_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="state_store_configuration_incomplete"):
        state_store_from_environment({"counter": 0})
