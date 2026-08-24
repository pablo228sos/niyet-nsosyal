from __future__ import annotations

from .schemas import BundleStatus, EvidenceItem, EvidenceRelation


def citation_line(item: EvidenceItem) -> str:
    publisher = item.publisher or "Unknown publisher"
    date = item.publication_date or "date unknown"
    return f"[{item.evidence_id}] {publisher} ({date}, {item.canonical_url}): {item.passage}"


def build_explanation(status: BundleStatus, evidence: tuple[EvidenceItem, ...]) -> tuple[str, tuple[str, ...]]:
    cited = tuple(item for item in evidence if item.relation is not EvidenceRelation.INSUFFICIENT)
    if not cited:
        return "No sufficiently relevant passage was found in the controlled evidence corpus.", ()
    prefix = {
        BundleStatus.SUPPORTED: "The controlled evidence supports the claim.",
        BundleStatus.PARTIAL: "The controlled evidence supports only part of the claim.",
        BundleStatus.CONFLICTING: "The controlled evidence conflicts with at least one part of the claim.",
        BundleStatus.INSUFFICIENT: "The controlled evidence is insufficient.",
    }[status]
    return " ".join((prefix, *(citation_line(item) for item in cited))), tuple(item.evidence_id for item in cited)
