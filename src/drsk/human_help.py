from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from niyet.runtime import NiyetRuntime, RouteDecision
from niyet.types import IntentType

from .state_store import MemoryStateStore, StateStore


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

    Domain transitions are storage-independent. Local development uses a locked
    in-memory store; deployments can supply a durable store so author and responder
    devices do not depend on landing on the same serverless process.
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
        decision: RouteDecision | None = None,
    ) -> HumanRequest:
        display_text = display_text.strip()
        if not display_text:
            raise ValueError("text_required")
        routing_text = (routing_text or display_text).strip()

        def mutation(state: dict[str, Any]) -> HumanRequest:
            responder_state = state["responder_state"]
            route = decision
            if route is not None and not self._route_is_currently_eligible(
                route, responder_state
            ):
                route = None
            if route is None:
                route = self.runtime.route(
                    routing_text,
                    intent_override=IntentType.ASK,
                    responder_state=responder_state,
                )

            now = time.time()
            request = HumanRequest(
                request_id=f"hr-{secrets.token_urlsafe(9)}",
                author_token=secrets.token_urlsafe(24),
                display_text=display_text,
                routing_text=routing_text,
                created_at=now,
                updated_at=now,
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
            state["requests"][request.request_id] = request.state_dict()
            return request

        return self.store.mutate(mutation)

    def open_from_routing(
        self,
        display_text: str,
        routing: dict[str, Any],
        *,
        routing_text: str | None = None,
        evidence_context: dict[str, Any] | None = None,
    ) -> HumanRequest:
        """Persist a DRSK -> NIYET route, rechecking live capacity before commit."""

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
            return request.public_dict()

        return self.store.mutate(mutation)

    def skip(self, request_id: str, responder_id: str) -> dict[str, Any]:
        def mutation(state: dict[str, Any]) -> dict[str, Any]:
            request = self._assigned_request(state, request_id, responder_id)
            if request.status is not HumanRequestStatus.OPEN:
                raise ValueError("request_not_open")
            request.excluded_responder_ids.append(responder_id)
            route = self.runtime.route(
                request.routing_text,
                intent_override=IntentType.ASK,
                responder_state=state["responder_state"],
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
            state["requests"][request_id] = request.state_dict()
            return request.public_dict()

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
            return dict(state["responder_state"][responder_id])

        return self.store.mutate(mutation)

    def _known_responder(self, responder_id: str) -> None:
        if responder_id not in self.runtime.responder_by_id:
            raise ValueError("unknown_responder")

    @staticmethod
    def _route_is_currently_eligible(
        decision: RouteDecision,
        responder_state: dict[str, dict[str, Any]],
    ) -> bool:
        if decision.responder_id is None:
            return True
        state = responder_state.get(decision.responder_id)
        return bool(
            state
            and state.get("active")
            and int(state.get("remaining_slots", 0)) > 0
        )

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
