from __future__ import annotations

import hashlib
from datetime import UTC, datetime

from .alignment import align_claim
from .explanation import build_explanation
from .mismatch import source_mismatch
from .retrieval import ControlledEvidenceProvider
from .schemas import BundleStatus, DistortionType, EvidenceBundle, EvidenceItem, EvidenceRelation, PostAnalysis
from .structured_checks import detect_distortions


def _stable_id(prefix: str, *values: str) -> str:
    digest = hashlib.sha256("\x1f".join(values).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _bundle_status(evidence: tuple[EvidenceItem, ...]) -> BundleStatus:
    relations = {item.relation for item in evidence}
    if EvidenceRelation.CONFLICTING in relations:
        return BundleStatus.CONFLICTING
    if EvidenceRelation.PARTIALLY_SUPPORTED in relations:
        return BundleStatus.PARTIAL
    if EvidenceRelation.SUPPORTED in relations:
        return BundleStatus.SUPPORTED
    return BundleStatus.INSUFFICIENT


def build_evidence_bundle(
    analysis: PostAnalysis,
    provider: ControlledEvidenceProvider,
    *,
    now: datetime | None = None,
    version: int = 1,
    hits_per_claim: int = 3,
) -> EvidenceBundle:
    created_at = now or datetime.now(UTC)
    items: list[EvidenceItem] = []
    for claim in analysis.claims:
        for hit in provider.retrieve(claim.text, limit=hits_per_claim):
            relation = align_claim(claim.text, hit.passage)
            if relation is EvidenceRelation.INSUFFICIENT:
                continue
            distortions = list(detect_distortions(claim.text, hit.passage))
            if source_mismatch(claim.text, publisher=hit.document.publisher) is True:
                if DistortionType.ATTRIBUTION_SHIFT not in distortions:
                    distortions.append(DistortionType.ATTRIBUTION_SHIFT)
            if len(distortions) > 1 and DistortionType.NONE in distortions:
                distortions.remove(DistortionType.NONE)
            evidence_id = _stable_id("ev", claim.claim_id, hit.document.canonical_url, hit.passage_location, hit.document.document_hash)
            items.append(EvidenceItem(
                evidence_id=evidence_id,
                claim_id=claim.claim_id,
                source_url=hit.document.source_url,
                canonical_url=hit.document.canonical_url,
                title=hit.document.title,
                publisher=hit.document.publisher,
                publication_date=hit.document.publication_date,
                retrieved_at=hit.document.retrieved_at,
                passage=hit.passage,
                passage_location=hit.passage_location,
                document_hash=hit.document.document_hash,
                relation=relation,
                distortions=tuple(distortions),
                origin_cluster_id=hit.document.origin_cluster_id,
                metadata={"provider": "controlled", "lexical_score": round(hit.score, 6)},
            ))
    evidence = tuple(items)
    status = _bundle_status(evidence)
    explanation, citations = build_explanation(status, evidence)
    return EvidenceBundle(
        bundle_id=_stable_id("bundle", analysis.text, str(version), *(item.evidence_id for item in evidence)),
        version=version,
        analysis=analysis,
        evidence=evidence,
        status=status,
        sufficient=status is not BundleStatus.INSUFFICIENT,
        explanation=explanation,
        cited_evidence_ids=citations,
        created_at=created_at,
    )

