from __future__ import annotations

from dataclasses import dataclass

from .schemas import DistortionType
from .structured_checks import detect_distortions


@dataclass(frozen=True)
class DistortionLensResult:
    claim: str
    evidence: str
    distortions: tuple[DistortionType, ...]
    count: int


def distortion_lens(claim: str, evidence: str) -> DistortionLensResult:
    distortions = tuple(item for item in detect_distortions(claim, evidence) if item is not DistortionType.NONE)
    return DistortionLensResult(claim, evidence, distortions, len(distortions))

