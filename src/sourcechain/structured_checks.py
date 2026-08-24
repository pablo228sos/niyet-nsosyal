from __future__ import annotations

import re

from .schemas import DistortionType
from .text import normalize


_NUMBER_RE = re.compile(r"(?<!\w)(?:%\s*)?\d+(?:[.,]\d+)?(?:\s*%)?")
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_INCREASE = ("arttı", "yükseldi", "increased", "rose", "grew")
_DECREASE = ("azaldı", "düştü", "decreased", "fell", "declined")
_CAUSAL = ("neden", "sebep", "yol aç", "caus", "leads to", "results in")
_ASSOCIATION = ("ilişki", "bağlantı", "korelasyon", "associated", "correlat", "linked")
_CERTAIN = ("kesin", "kanıtladı", "ispatladı", "proves", "definitely", "always")
_UNCERTAIN = ("olabil", "muhtemel", "öneriyor", "suggests", "may", "might", "could", "possibly")


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    value = normalize(text)
    return any(needle in value for needle in needles)


def numeric_values(text: str) -> tuple[str, ...]:
    without_years = _YEAR_RE.sub("", text)
    return tuple(match.group(0).replace(" ", "").replace(",", ".").lstrip("%").rstrip("%") for match in _NUMBER_RE.finditer(without_years))


def years(text: str) -> tuple[str, ...]:
    return tuple(match.group(0) for match in _YEAR_RE.finditer(text))


def detect_distortions(claim: str, evidence: str) -> tuple[DistortionType, ...]:
    found: list[DistortionType] = []
    claim_numbers, evidence_numbers = numeric_values(claim), numeric_values(evidence)
    if claim_numbers and evidence_numbers and claim_numbers != evidence_numbers:
        found.append(DistortionType.NUMERIC_DISTORTION)
    claim_years, evidence_years = years(claim), years(evidence)
    if claim_years and evidence_years and claim_years != evidence_years:
        found.append(DistortionType.TEMPORAL_SHIFT)
    if _contains_any(claim, _CAUSAL) and _contains_any(evidence, _ASSOCIATION) and not _contains_any(evidence, _CAUSAL):
        found.append(DistortionType.CAUSALITY_SHIFT)
    if _contains_any(claim, _CERTAIN) and _contains_any(evidence, _UNCERTAIN) and not _contains_any(evidence, _CERTAIN):
        found.append(DistortionType.CERTAINTY_SHIFT)
    if (_contains_any(claim, _INCREASE) and _contains_any(evidence, _DECREASE)) or (_contains_any(claim, _DECREASE) and _contains_any(evidence, _INCREASE)):
        if DistortionType.NUMERIC_DISTORTION not in found:
            found.append(DistortionType.NUMERIC_DISTORTION)
    return tuple(found) if found else (DistortionType.NONE,)
