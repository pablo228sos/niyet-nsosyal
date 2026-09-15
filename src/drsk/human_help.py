from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from niyet.runtime import NiyetRuntime
from niyet.types import IntentType

from .state_store import MemoryStateStore, StateStore


MAX_ALLOCATION_WINDOW = 20


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

    def state_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "author_token": self.author_token,
            "display_text": self.display_text,
            "routing_text": self.routing_text,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status.value,
            "assigned_responder_id": self.assigned_responder_id,
            "assigned_responder_name": self.assigned_responder_name,
            "match_reason": list(self.match_reason),
            "excluded_responder_ids": list(self.excluded_responder_ids),
            "evidence_context": self.evidence_context,
            "answer": self.answer,
        }

    @classmethod
    def from_state_dict(cls, value: dict[str, Any]) -> HumanRequest:
        return cls(
            request_id=str(value["request_id"]),
            author_token=str(value["author_token"]),
            display_text=str(value["display_text"]),
            routing_text=str(value["routing_text"]),
            created_at=float(value["created_at"]),
            updated_at=float(value["updated_at"]),
            status=HumanRequestStatus(value["status"]),
            assigned_responder_id=value.get("assigned_responder_id"),
            assigned_responder_name=value.get("assigned_responder_name"),
            match_reason=tuple(value.get("match_reason") or ()),
            excluded_responder_ids=list(value.get("excluded_responder_ids") or ()),
            evidence_context=value.get("evidence_context"),
            answer=value.get("answer"),
        )


class HumanHelpService:
    """Authoritative state machine for the evidence-to-human resolution loop.

    Pending requests are reallocated as one bounded NIYET window. Accepted work
    is pinned and has already consumed capacity; OPEN/UNMATCHED requests compete
    for the remaining slots. Domain transitions stay storage-independent so the
    same semantics work with local memory or a durable shared state store.
    """

    def __init__(self, runtime: NiyetRuntime, *, store: StateStore | None = None) -> None:
        self.runtime = runtime
        initial = self._initial_state()
        self.store = store if store is not None else MemoryStateStore(initial)

    @property
    def state_backend(self) -> str:
        return self.store.backend_name

    @property
    def state_durable(self) -> bool:
        return self.store.durable

    def _initial_state(self) -> dict[str, Any]:
        return {
            "requests": {},
            "responder_state": self.runtime.default_responder_state(),
        }

    def reset(self) -> None:
        self.store.reset(self._initial_state())

    def responder_state(self) -> dict[str, dict[str, Any]]:
        state = self.store.read()
        return {
            responder_id: dict(value)
            for responder_id, value in state["responder_state"].items()
        }

    def open_request(
        self,
        display_text: str,
        *,
        routing_text: str | None = None,
        evidence_context: dict[str, Any] | None = None,
    ) -> HumanRequest:
        display_text = display_text.strip()
        if not display_text:
            raise ValueError("text_required")
        routing_text = (routing_text or display_text).strip()

        def mutation(state: dict[str, Any]) -> HumanRequest:
            now = time.time()
            request = HumanRequest(
                request_id=f"hr-{secrets.token_urlsafe(9)}",
                author_token=secrets.token_urlsafe(24),
                display_text=display_text,
                routing_text=routing_text,
                created_at=now,
                updated_at=now,
                status=HumanRequestStatus.UNMATCHED,
                evidence_context=evidence_context,
            )
            state["requests"][request.request_id] = request.state_dict()
            self._rebalance_pending(state)
            return self._request(state, request.request_id)

        return self.store.mutate(mutation)

    def open_from_routing(
        self,
        display_text: str,
        routing: dict[str, Any],
        *,
        routing_text: str | None = None,
        evidence_context: dict[str, Any] | None = None,
    ) -> HumanRequest:
        """Persist DRSK escalation inside the authoritative shared allocation window."""
        stored_routing_text = (
            routing_text
            or str(routing.get("routing_text") or "").strip()
            or display_text
        )
        return self.open_request(
            display_text,
            routing_text=stored_routing_text,
            evidence_context=evidence_context,
        )

    def inbox(self, responder_id: str) -> list[dict[str, Any]]:
        self._known_responder(responder_id)
        state = self.store.read()
        requests = [
            HumanRequest.from_state_dict(value)
            for value in state["requests"].values()
        ]
        visible = [
            request
            for request in requests
            if request.assigned_responder_id == responder_id
            and request.status in {HumanRequestStatus.OPEN, HumanRequestStatus.ACCEPTED}
        ]
        visible.sort(key=lambda item: item.created_at)
        return [request.public_dict() for request in visible]

    def status(self, request_id: str, author_token: str) -> dict[str, Any]:
        state = self.store.read()
        request = self._request(state, request_id)
        if not secrets.compare_digest(request.author_token, author_token):
            raise ValueError("invalid_author_token")
        return request.public_dict()

    def accept(self, request_id: str, responder_id: str) -> dict[str, Any]:
        def mutation(state: dict[str, Any]) -> dict[str, Any]:
            request = self._assigned_request(state, request_id, responder_id)
            if request.status is not HumanRequestStatus.OPEN:
                raise ValueError("request_not_open")

            responder = state["responder_state"][responder_id]
            if not responder.get("active") or int(responder.get("remaining_slots", 0)) <= 0:
                raise ValueError("responder_capacity_exhausted")

            state["responder_state"] = self.runtime.update_responder_state(
                state["responder_state"],
                responder_id,
                action="accept",
            )
            request.status = HumanRequestStatus.ACCEPTED
            request.updated_at = time.time()
            state["requests"][request_id] = request.state_dict()
            self._rebalance_pending(state)
            return self._request(state, request_id).public_dict()

        return self.store.mutate(mutation)

    def skip(self, request_id: str, responder_id: str) -> dict[str, Any]:
        def mutation(state: dict[str, Any]) -> dict[str, Any]:
            request = self._assigned_request(state, request_id, responder_id)
            if request.status is not HumanRequestStatus.OPEN:
                raise ValueError("request_not_open")
            if responder_id not in request.excluded_responder_ids:
                request.excluded_responder_ids.append(responder_id)
            request.status = HumanRequestStatus.UNMATCHED
            request.assigned_responder_id = None
            request.assigned_responder_name = None
            request.match_reason = ()
            request.updated_at = time.time()
            state["requests"][request_id] = request.state_dict()
            self._rebalance_pending(state)
            return self._request(state, request_id).public_dict()

        return self.store.mutate(mutation)

    def answer(self, request_id: str, responder_id: str, answer: str) -> dict[str, Any]:
        answer = answer.strip()
        if not answer:
            raise ValueError("answer_required")

        def mutation(state: dict[str, Any]) -> dict[str, Any]:
            request = self._assigned_request(state, request_id, responder_id)
            if request.status is not HumanRequestStatus.ACCEPTED:
                raise ValueError("request_not_accepted")
            request.answer = answer
            request.status = HumanRequestStatus.ANSWERED
            request.updated_at = time.time()
            state["requests"][request_id] = request.state_dict()
            return request.public_dict()

        return self.store.mutate(mutation)

    def set_responder_active(self, responder_id: str, active: bool) -> dict[str, Any]:
        self._known_responder(responder_id)

        def mutation(state: dict[str, Any]) -> dict[str, Any]:
            state["responder_state"] = self.runtime.update_responder_state(
                state["responder_state"],
                responder_id,
                action="resume" if active else "pause",
            )
            self._rebalance_pending(state)
            return dict(state["responder_state"][responder_id])

        return self.store.mutate(mutation)

    def _rebalance_pending(self, state: dict[str, Any]) -> None:
        pending = [
            HumanRequest.from_state_dict(value)
            for value in state["requests"].values()
            if HumanRequestStatus(value["status"])
            in {HumanRequestStatus.OPEN, HumanRequestStatus.UNMATCHED}
        ]
        pending.sort(key=lambda item: (item.created_at, item.request_id))

        for request in pending:
            request.status = HumanRequestStatus.UNMATCHED
            request.assigned_responder_id = None
            request.assigned_responder_name = None
            request.match_reason = ()
            state["requests"][request.request_id] = request.state_dict()

        window = pending[:MAX_ALLOCATION_WINDOW]
        overflow = pending[MAX_ALLOCATION_WINDOW:]
        if window:
            decisions = self.runtime.route_many(
                [
                    {
                        "id": request.request_id,
                        "text": request.routing_text,
                        "intent_override": IntentType.ASK,
                        "exclude_responder_ids": tuple(request.excluded_responder_ids),
                    }
                    for request in window
                ],
                responder_state=state["responder_state"],
            )
            decisions_by_id = {
                decision.request_id: decision
                for decision in decisions
                if decision.request_id is not None
            }

            for request in window:
                decision = decisions_by_id.get(request.request_id)
                if decision is not None and decision.responder_id is not None:
                    request.status = HumanRequestStatus.OPEN
                    request.assigned_responder_id = decision.responder_id
                    request.assigned_responder_name = decision.responder_name
                    request.match_reason = tuple(decision.reason)
                request.updated_at = time.time()
                state["requests"][request.request_id] = request.state_dict()

        for request in overflow:
            request.match_reason = ("waiting_for_next_allocation_window",)
            request.updated_at = time.time()
            state["requests"][request.request_id] = request.state_dict()

    def _known_responder(self, responder_id: str) -> None:
        if responder_id not in self.runtime.responder_by_id:
            raise ValueError("unknown_responder")

    @staticmethod
    def _request(state: dict[str, Any], request_id: str) -> HumanRequest:
        raw = state["requests"].get(request_id)
        if raw is None:
            raise ValueError("request_not_found")
        return HumanRequest.from_state_dict(raw)

    def _assigned_request(
        self,
        state: dict[str, Any],
        request_id: str,
        responder_id: str,
    ) -> HumanRequest:
        self._known_responder(responder_id)
        request = self._request(state, request_id)
        if request.assigned_responder_id != responder_id:
            raise ValueError("request_not_assigned")
        return request
