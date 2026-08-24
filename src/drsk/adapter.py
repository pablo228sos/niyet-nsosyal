from __future__ import annotations

from dataclasses import asdict
from typing import Any

from niyet.runtime import NiyetRuntime, RouteDecision
from niyet.types import IntentType

from .schemas import HumanEscalationRequest


class NiyetEscalationAdapter:
    """Translate a DRSK human request into an explicit NIYET ASK route."""

    def __init__(self, runtime: NiyetRuntime | None = None) -> None:
        self.runtime = runtime if runtime is not None else NiyetRuntime()

    def route(
        self,
        request: HumanEscalationRequest,
        *,
        responder_state: dict | None = None,
    ) -> dict[str, Any]:
        context = self._structured_context(request)
        decision = self.runtime.route(
            context,
            intent_override=IntentType.ASK,
            responder_state=responder_state,
        )
        return route_decision_to_dict(decision)

    @staticmethod
    def _structured_context(request: HumanEscalationRequest) -> str:
        distortions = ", ".join(item.value for item in request.distortion_types) or "NONE"
        return "\n".join(
            (
                f"topic: {request.topic}",
                f"claim: {request.claim_text}",
                f"evidence_status: {request.evidence_status.value}",
                f"distortions: {distortions}",
                f"requested_resolution: {request.requested_resolution}",
            )
        )


def route_decision_to_dict(decision: RouteDecision) -> dict[str, Any]:
    raw = asdict(decision)
    raw["reason"] = list(decision.reason)
    return raw
