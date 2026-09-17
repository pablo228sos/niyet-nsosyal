from __future__ import annotations

import re

from .schemas import DistortionType
from .text import normalize


_NUMBER_RE = re.compile(r"(?<!\w)(?:%\s*)?\d+(?:[.,]\d+)*(?:\s*%)?")
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
_PERCENT_RE = re.compile(
    r"(?:\b(?:yüzde|percent)\s+\d+(?:[.,]\d+)?|(?<!\w)%?\s*\d+(?:[.,]\d+)?\s*%)",
    re.I,
)
_MEASURE_RE = re.compile(
    r"(?<!\w)(\d+(?:[.,]\d+)*)\s*"
    r"(metres?|meters?|kilometres?|kilometers?|km|kilograms?|kg|"
    r"people|persons?|kişi(?:ydi|dir)?)\b",
    re.I,
)
_INCREASE = ("arttı", "yükseldi", "increased", "rose", "grew")
_DECREASE = ("azaldı", "düştü", "decreased", "fell", "declined")
_CAUSAL = ("neden", "sebep", "yol aç", "caus", "leads to", "results in")
_ASSOCIATION = ("ilişki", "bağlantı", "korelasyon", "associated", "correlat", "linked")
_CERTAIN = ("kesin", "kanıtladı", "ispatladı", "proves", "definitely", "always")
_UNCERTAIN = ("olabil", "abilir", "ebilir", "abilece", "muhtemel", "öneriyor", "suggests", "may", "might", "could", "possibly")
_UNIVERSAL_SCOPE = ("tüm", "bütün", "her biri", "all", "every")
_LIMITED_SCOPE = ("bazı", "kimi", "bir kısm", "some", "several")
_NEGATION_RE = re.compile(
    r"\b(?:no|not|never|neither|nor|değil|degil|yok|artırmaz|arttirmaz|azaltmaz)\b",
    re.I,
)


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    value = normalize(text)
    return any(normalize(needle) in value for needle in needles)


def numeric_values(text: str) -> tuple[str, ...]:
    without_years = _YEAR_RE.sub("", text)
    return tuple(match.group(0).replace(" ", "").replace(",", ".").lstrip("%").rstrip("%") for match in _NUMBER_RE.finditer(without_years))


def years(text: str) -> tuple[str, ...]:
    return tuple(match.group(0) for match in _YEAR_RE.finditer(text))


def has_negation(text: str) -> bool:
    return bool(_NEGATION_RE.search(normalize(text)))


def _canonical_number(value: str) -> str:
    clean = value.replace(" ", "").replace("%", "")
    if clean.count(".") + clean.count(",") > 1:
        return clean.replace(".", "").replace(",", "")
    return clean.replace(",", ".")


def _comparable_numeric_facts(text: str) -> tuple[tuple[str, str], ...]:
    """Return only numbers whose semantic unit is explicit enough to compare."""
    value = normalize(text)
    facts: list[tuple[str, str]] = []
    occupied: list[tuple[int, int]] = []
    for match in _PERCENT_RE.finditer(value):
        number = _NUMBER_RE.search(match.group(0))
        if number:
            facts.append(("percent", _canonical_number(number.group(0))))
            occupied.append(match.span())
    for match in _MEASURE_RE.finditer(value):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        unit = match.group(2).casefold()
        if unit.startswith(("metre", "meter")):
            kind = "length_m"
        elif unit.startswith(("kilometre", "kilometer")) or unit == "km":
            kind = "length_km"
        elif unit.startswith("kilogram") or unit == "kg":
            kind = "mass_kg"
        else:
            kind = "people"
        facts.append((kind, _canonical_number(match.group(1))))
    return tuple(facts)


def detect_distortions(claim: str, evidence: str) -> tuple[DistortionType, ...]:
    found: list[DistortionType] = []
    claim_facts = _comparable_numeric_facts(claim)
    evidence_facts = _comparable_numeric_facts(evidence)
    comparable_kinds = {kind for kind, _ in claim_facts} & {kind for kind, _ in evidence_facts}
    numeric_conflict = any(
        len(claim_values := [value for kind, value in claim_facts if kind == target]) == 1
        and len(evidence_values := [value for kind, value in evidence_facts if kind == target]) == 1
        and claim_values != evidence_values
        for target in comparable_kinds
    )
    if numeric_conflict:
        found.append(DistortionType.NUMERIC_DISTORTION)
    claim_years, evidence_years = years(claim), years(evidence)
    if claim_years and evidence_years and claim_years != evidence_years:
        found.append(DistortionType.TEMPORAL_SHIFT)
    if _contains_any(claim, _CAUSAL) and _contains_any(evidence, _ASSOCIATION) and not _contains_any(evidence, _CAUSAL):
        found.append(DistortionType.CAUSALITY_SHIFT)
    if (
        _contains_any(evidence, _UNCERTAIN)
        and not _contains_any(claim, _UNCERTAIN)
        and not _contains_any(evidence, _CERTAIN)
    ):
        found.append(DistortionType.CERTAINTY_SHIFT)
    if _contains_any(claim, _UNIVERSAL_SCOPE) and _contains_any(evidence, _LIMITED_SCOPE):
        found.append(DistortionType.SCOPE_SHIFT)
    if (_contains_any(claim, _INCREASE) and _contains_any(evidence, _DECREASE)) or (_contains_any(claim, _DECREASE) and _contains_any(evidence, _INCREASE)):
        if DistortionType.NUMERIC_DISTORTION not in found:
            found.append(DistortionType.NUMERIC_DISTORTION)
    return tuple(found) if found else (DistortionType.NONE,)
