from __future__ import annotations

from collections.abc import Iterable

from .schemas import EvidenceItem


def independent_origin_count(evidence: Iterable[EvidenceItem]) -> int:
    return len({item.origin_cluster_id for item in evidence if item.origin_cluster_id})


def origin_cluster_counts(evidence: Iterable[EvidenceItem]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in evidence:
        counts[item.origin_cluster_id] = counts.get(item.origin_cluster_id, 0) + 1
    return dict(sorted(counts.items()))

