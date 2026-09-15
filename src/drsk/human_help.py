from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from niyet.runtime import NiyetRuntime, RouteDecision
from niyet.types import IntentType


class HumanRequestStatus(StrEnum):
    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    ANSWERED = "ANSWERED"
    UNMATCHED = "UNMATCHED"


@dataclass
class HumanRequest:
    request_id: str
    author_token: str
    display_text: str
    routing_text: str
    created_at: float
    updated_at: float
    status: HumanRequestStatus
    assigned_responder_id: str | None = None
    assigned_responder_name: str | None = None
    match_reason: tuple[str, ...] = ()
    excluded_responder_ids: list[str] = field(default_factory=list)
    evidence_context: dict[str, Any] | None = None
    answer: str | None = None

    def public_dict(self, *, include_author_token: bool = False) -> dict[str, Any]:
        result: dict[str, Any] = {
            "request_id": self.request_id,
            "text": self.display_text,
            "status": self.status.value,
            "assigned_responder": (
                {
                    "id": self.assigned_responder_id,
                    "name": self.assigned_responder_name,
                    "reason": list(self.match_reason),
                }
                if self.assigned_responder_id
                else None
            ),
            "evidence_context": self.evidence_context,
            "answer": self.answer,
        }
        if include_author_token:
            result["author_token"] = self.author_token
        return result


class HumanHelpService:
    """Process-scoped authoritative state for the jury/demo human-help loop.

    The browser may observe this state but cannot submit arbitrary responder capacity.
    The service is deliberately storage-agnostic at the boundary: this in-memory
    implementation is appropriate for a single demo process and local multi-device
    presentation. Durable production deployment still requires an external shared store.
    """

    def __init__(self, runtime: NiyetRuntime) -> None:
        self.runtime = runtime
        self._lock = threading.RLock()
        self.reset()

    def reset(self) -> None:
        with getattr(self, "_lock", threading.RLock()):
            self._requests: dict[str, HumanRequest] = {}
            self._responder_state = self.runtime.default_responder_state()

    def responder_state(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {
                responder_id: dict(state)
                for responder_id, state in self._responder_state.items()
            }

    def open_request(
        self,
        display_text: str,
        *,
        routing_text: str | None = None,
        evidence_context: dict[str, Any] | None = None,
        decision: RouteDecision | None = None,
    ) -> HumanRequest:
        display_text = display_text.strip()
        if not display_text:
            raise ValueError("text_required")
        routing_text = (routing_text or display_text).strip()

        with self._lock:
            route = decision or self.runtime.route(
                routing_text,
                intent_override=IntentType.ASK,
                responder_state=self._responder_state,
            )
            request = HumanRequest(
                request_id=f"hr-{secrets.token_urlsafe(9)}",
                author_token=secrets.token_urlsafe(24),
                display_text=display_text,
                routing_text=routing_text,
                created_at=time.time(),
                updated_at=time.time(),
                status=(
                    HumanRequestStatus.OPEN
                    if route.responder_id
                    else HumanRequestStatus.UNMATCHED
                ),
                assigned_responder_id=route.responder_id,
                assigned_responder_name=route.responder_name,
                match_reason=tuple(route.reason),
                evidence_context=evidence_context,
            )
            self._requests[request.request_id] = request
            return request

    def open_from_routing(
        self,
        display_text: str,
        routing: dict[str, Any],
        *,
        routing_text: str | None = None,
        evidence_context: dict[str, Any] | None = None,
    ) -> HumanRequest:
        """Persist an already-computed DRSK -> NIYET route without routing twice."""

        decision = RouteDecision(
            response_needed=bool(routing.get("response_needed")),
            intent=routing.get("intent"),
            responder_id=routing.get("responder_id"),
            responder_name=routing.get("responder_name"),
            reason=tuple(routing.get("reason") or ()),
            development_utility=routing.get("development_utility"),
            retrieval_similarity=routing.get("retrieval_similarity"),
            request_id=routing.get("request_id"),
        )
        return self.open_request(
            display_text,
            routing_text=routing_text,
            evidence_context=evidence_context,
            decision=decision,
        )

    def inbox(self, responder_id: str) -> list[dict[str, Any]]:
        self._known_responder(responder_id)
        with self._lock:
            requests = [
                request
                for request in self._requests.values()
                if request.assigned_responder_id == responder_id
                and request.status in {HumanRequestStatus.OPEN, HumanRequestStatus.ACCEPTED}
            ]
            requests.sort(key=lambda item: item.created_at)
            return [request.public_dict() for request in requests]

    def status(self, request_id: str, author_token: str) -> dict[str, Any]:
        with self._lock:
            request = self._request(request_id)
            if not secrets.compare_digest(request.author_token, author_token):
                raise ValueError("invalid_author_token")
            return request.public_dict()

    def accept(self, request_id: str, responder_id: str) -> dict[str, Any]:
        with self._lock:
            request = self._assigned_request(request_id, responder_id)
            if request.status is not HumanRequestStatus.OPEN:
                raise ValueError("request_not_open")
            self._responder_state = self.runtime.update_responder_state(
                self._responder_state,
                responder_id,
                action="accept",
            )
            request.status = HumanRequestStatus.ACCEPTED
            request.updated_at = time.time()
            return request.public_dict()

    def skip(self, request_id: str, responder_id: str) -> dict[str, Any]:
        with self._lock:
            request = self._assigned_request(request_id, responder_id)
            if request.status is not HumanRequestStatus.OPEN:
                raise ValueError("request_not_open")
            request.excluded_responder_ids.append(responder_id)
            route = self.runtime.route(
                request.routing_text,
                intent_override=IntentType.ASK,
                responder_state=self._responder_state,
                exclude_responder_ids=tuple(request.excluded_responder_ids),
            )
            request.assigned_responder_id = route.responder_id
            request.assigned_responder_name = route.responder_name
            request.match_reason = tuple(route.reason)
            request.status = (
                HumanRequestStatus.OPEN
                if route.responder_id
                else HumanRequestStatus.UNMATCHED
            )
            request.updated_at = time.time()
            return request.public_dict()

    def answer(self, request_id: str, responder_id: str, answer: str) -> dict[str, Any]:
        answer = answer.strip()
        if not answer:
            raise ValueError("answer_required")
        with self._lock:
            request = self._assigned_request(request_id, responder_id)
            if request.status is not HumanRequestStatus.ACCEPTED:
                raise ValueError("request_not_accepted")
            request.answer = answer
            request.status = HumanRequestStatus.ANSWERED
            request.updated_at = time.time()
            return request.public_dict()

    def set_responder_active(self, responder_id: str, active: bool) -> dict[str, Any]:
        self._known_responder(responder_id)
        with self._lock:
            self._responder_state = self.runtime.update_responder_state(
                self._responder_state,
                responder_id,
                action="resume" if active else "pause",
            )
            return dict(self._responder_state[responder_id])

    def _known_responder(self, responder_id: str) -> None:
        if responder_id not in self.runtime.responder_by_id:
            raise ValueError("unknown_responder")

    def _request(self, request_id: str) -> HumanRequest:
        request = self._requests.get(request_id)
        if request is None:
            raise ValueError("request_not_found")
        return request

    def _assigned_request(self, request_id: str, responder_id: str) -> HumanRequest:
        self._known_responder(responder_id)
        request = self._request(request_id)
        if request.assigned_responder_id != responder_id:
            raise ValueError("request_not_assigned")
        return request
