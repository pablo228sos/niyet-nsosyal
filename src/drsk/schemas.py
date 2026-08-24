from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from sourcechain.schemas import BundleStatus, DistortionType


class ResolutionPath(StrEnum):
    EVIDENCE = "EVIDENCE"
    HUMAN = "HUMAN"
    BOTH = "BOTH"
    NONE = "NONE"
    DEFERRED = "DEFERRED"


@dataclass(frozen=True)
class HumanEscalationRequest:
    request_id: str
    claim_text: str
    topic: str
    evidence_status: BundleStatus
    distortion_types: tuple[DistortionType, ...]
    requested_resolution: str


@dataclass(frozen=True)
class ResolutionDecision:
    path: ResolutionPath
    reasons: tuple[str, ...]
    escalation: HumanEscalationRequest | None = None

    def to_dict(self) -> dict[str, Any]:
        raw = asdict(self)
        raw["path"] = self.path.value
        raw["reasons"] = list(self.reasons)
        if self.escalation:
            raw["escalation"]["evidence_status"] = self.escalation.evidence_status.value
            raw["escalation"]["distortion_types"] = [item.value for item in self.escalation.distortion_types]
        return raw
