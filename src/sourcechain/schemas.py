from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from urllib.parse import urlparse


class StatementType(StrEnum):
    FACTUAL_CLAIM = "FACTUAL_CLAIM"
    OPINION = "OPINION"
    PERSONAL_EXPERIENCE = "PERSONAL_EXPERIENCE"
    PREDICTION = "PREDICTION"
    QUESTION = "QUESTION"
    MIXED = "MIXED"


class EvidenceRelation(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT = "INSUFFICIENT"


class BundleStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT = "INSUFFICIENT"


class DistortionType(StrEnum):
    NONE = "NONE"
    CERTAINTY_SHIFT = "CERTAINTY_SHIFT"
    CAUSALITY_SHIFT = "CAUSALITY_SHIFT"
    NUMERIC_DISTORTION = "NUMERIC_DISTORTION"
    SCOPE_SHIFT = "SCOPE_SHIFT"
    ATTRIBUTION_SHIFT = "ATTRIBUTION_SHIFT"
    TEMPORAL_SHIFT = "TEMPORAL_SHIFT"


@dataclass(frozen=True)
class AtomicClaim:
    claim_id: str
    text: str
    start: int
    end: int

    def __post_init__(self) -> None:
        if not self.claim_id or not self.text.strip() or self.start < 0 or self.end <= self.start:
            raise ValueError("invalid atomic claim")


@dataclass(frozen=True)
class PostAnalysis:
    text: str
    statement_type: StatementType
    check_worthy: bool
    claims: tuple[AtomicClaim, ...]


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    claim_id: str
    source_url: str
    canonical_url: str
    title: str | None
    publisher: str | None
    publication_date: str | None
    retrieved_at: datetime
    passage: str
    passage_location: str
    document_hash: str
    relation: EvidenceRelation
    distortions: tuple[DistortionType, ...]
    origin_cluster_id: str
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        for value in (self.source_url, self.canonical_url):
            parsed = urlparse(value)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("evidence URL must use http or https")
        if not all((self.evidence_id, self.claim_id, self.passage.strip(), self.passage_location, self.document_hash)):
            raise ValueError("evidence provenance fields are required")
        if re.search(r"<\s*(?:script|style|iframe|object|embed|[a-z][^>]*)>", self.passage, re.I):
            raise ValueError("passage must be plain text, not HTML")


@dataclass(frozen=True)
class EvidenceBundle:
    bundle_id: str
    version: int
    analysis: PostAnalysis
    evidence: tuple[EvidenceItem, ...]
    status: BundleStatus
    sufficient: bool
    explanation: str
    cited_evidence_ids: tuple[str, ...]
    created_at: datetime

    def __post_init__(self) -> None:
        ids = [item.evidence_id for item in self.evidence]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate evidence ID")
        unknown = set(self.cited_evidence_ids) - set(ids)
        if unknown:
            raise ValueError("explanation cites unknown evidence")
        if self.version < 1 or not self.bundle_id:
            raise ValueError("invalid evidence bundle identity")

    def to_dict(self) -> dict[str, Any]:
        def encode(value: Any) -> Any:
            if isinstance(value, StrEnum):
                return value.value
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, tuple):
                return [encode(item) for item in value]
            if isinstance(value, dict):
                return {key: encode(item) for key, item in sorted(value.items())}
            return value

        return encode(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, payload: str) -> "EvidenceBundle":
        raw = json.loads(payload)
        analysis_raw = raw["analysis"]
        analysis = PostAnalysis(
            text=analysis_raw["text"],
            statement_type=StatementType(analysis_raw["statement_type"]),
            check_worthy=bool(analysis_raw["check_worthy"]),
            claims=tuple(AtomicClaim(**item) for item in analysis_raw["claims"]),
        )
        evidence = tuple(
            EvidenceItem(
                **{
                    **item,
                    "retrieved_at": datetime.fromisoformat(item["retrieved_at"]),
                    "relation": EvidenceRelation(item["relation"]),
                    "distortions": tuple(DistortionType(value) for value in item["distortions"]),
                }
            )
            for item in raw["evidence"]
        )
        return cls(
            bundle_id=raw["bundle_id"],
            version=int(raw["version"]),
            analysis=analysis,
            evidence=evidence,
            status=BundleStatus(raw["status"]),
            sufficient=bool(raw["sufficient"]),
            explanation=raw["explanation"],
            cited_evidence_ids=tuple(raw["cited_evidence_ids"]),
            created_at=datetime.fromisoformat(raw["created_at"]),
        )
