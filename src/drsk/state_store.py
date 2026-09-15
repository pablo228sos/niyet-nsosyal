from __future__ import annotations

import copy
import json
import os
import threading
from collections.abc import Callable
from typing import Any, Protocol, TypeVar
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


T = TypeVar("T")
State = dict[str, Any]


class StateStore(Protocol):
    """Small transactional boundary for mutable demo state.

    Mutations receive an isolated JSON-compatible state object and may modify it
    in place. Durable implementations must publish the resulting state atomically
    or retry when another writer wins the race.
    """

    backend_name: str
    durable: bool

    def read(self) -> State: ...

    def mutate(self, mutation: Callable[[State], T]) -> T: ...

    def reset(self, state: State) -> None: ...


class MemoryStateStore:
    """Thread-safe process-local store used for tests and local development."""

    backend_name = "memory"
    durable = False

    def __init__(self, initial_state: State) -> None:
        self._lock = threading.RLock()
        self._state = copy.deepcopy(initial_state)

    def read(self) -> State:
        with self._lock:
            return copy.deepcopy(self._state)

    def mutate(self, mutation: Callable[[State], T]) -> T:
        with self._lock:
            working = copy.deepcopy(self._state)
            result = mutation(working)
            self._state = working
            return result

    def reset(self, state: State) -> None:
        with self._lock:
            self._state = copy.deepcopy(state)


class UpstashRedisStateStore:
    """JSON state stored in Upstash Redis through its serverless REST API.

    Each mutation uses a compare-and-set Lua script. The caller reads a snapshot,
    applies one local mutation, and publishes it only if no other writer changed
    the snapshot in the meantime. This keeps the two-device demo coherent across
    Vercel function instances without coupling domain code to Redis commands.
    """

    backend_name = "upstash-redis-rest"
    durable = True

    _CAS_SCRIPT = """
local current = redis.call('GET', KEYS[1])
if current == ARGV[1] then
  redis.call('SET', KEYS[1], ARGV[2], 'EX', ARGV[3])
  return 1
end
return 0
""".strip()

    def __init__(
        self,
        *,
        url: str,
        token: str,
        key: str,
        initial_state: State,
        ttl_seconds: int = 86_400,
        timeout_seconds: float = 3.0,
        max_retries: int = 6,
    ) -> None:
        if not url.strip() or not token.strip():
            raise ValueError("state_store_credentials_required")
        if ttl_seconds < 60:
            raise ValueError("state_store_ttl_too_short")
        if max_retries < 1:
            raise ValueError("state_store_retries_required")

        self._url = url.rstrip("/")
        self._token = token
        self._key = key
        self._initial_state = copy.deepcopy(initial_state)
        self._ttl_seconds = ttl_seconds
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._ensure_initialized()

    def read(self) -> State:
        raw = self._read_raw()
        return self._decode_state(raw)

    def mutate(self, mutation: Callable[[State], T]) -> T:
        for _ in range(self._max_retries):
            raw = self._read_raw()
            working = self._decode_state(raw)
            result = mutation(working)
            updated = self._encode_state(working)
            swapped = self._command(
                [
                    "EVAL",
                    self._CAS_SCRIPT,
                    "1",
                    self._key,
                    raw,
                    updated,
                    str(self._ttl_seconds),
                ]
            )
            if int(swapped or 0) == 1:
                return result
        raise RuntimeError("state_store_conflict")

    def reset(self, state: State) -> None:
        raw = self._encode_state(state)
        result = self._command(
            ["SET", self._key, raw, "EX", str(self._ttl_seconds)]
        )
        if result != "OK":
            raise RuntimeError("state_store_write_failed")

    def _ensure_initialized(self) -> None:
        initial = self._encode_state(self._initial_state)
        self._command(
            [
                "SET",
                self._key,
                initial,
                "NX",
                "EX",
                str(self._ttl_seconds),
            ]
        )

    def _read_raw(self) -> str:
        raw = self._command(["GET", self._key])
        if raw is None:
            self._ensure_initialized()
            raw = self._command(["GET", self._key])
        if not isinstance(raw, str):
            raise RuntimeError("state_store_missing")
        return raw

    @staticmethod
    def _encode_state(state: State) -> str:
        try:
            return json.dumps(
                state,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise ValueError("state_not_json_serializable") from exc

    @staticmethod
    def _decode_state(raw: str) -> State:
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("state_store_corrupt") from exc
        if not isinstance(value, dict):
            raise RuntimeError("state_store_corrupt")
        return value

    def _command(self, command: list[Any]) -> Any:
        payload = json.dumps(command, ensure_ascii=False).encode("utf-8")
        request = Request(
            self._url,
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "drsk-final-prototype/1.0",
            },
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("state_store_unavailable") from exc

        if not isinstance(body, dict):
            raise RuntimeError("state_store_invalid_response")
        if body.get("error"):
            raise RuntimeError("state_store_command_failed")
        return body.get("result")


def state_store_from_environment(initial_state: State) -> StateStore:
    """Select durable state when configured, otherwise explicit local fallback."""

    url = os.getenv("UPSTASH_REDIS_REST_URL", "").strip()
    token = os.getenv("UPSTASH_REDIS_REST_TOKEN", "").strip()
    if bool(url) != bool(token):
        raise RuntimeError("state_store_configuration_incomplete")
    if not url:
        return MemoryStateStore(initial_state)

    namespace = os.getenv("DRSK_STATE_NAMESPACE", "final-demo").strip() or "final-demo"
    ttl_raw = os.getenv("DRSK_STATE_TTL_SECONDS", "86400")
    try:
        ttl_seconds = int(ttl_raw)
    except ValueError as exc:
        raise RuntimeError("state_store_invalid_ttl") from exc

    return UpstashRedisStateStore(
        url=url,
        token=token,
        key=f"drsk:human-help:{namespace}",
        initial_state=initial_state,
        ttl_seconds=ttl_seconds,
    )
