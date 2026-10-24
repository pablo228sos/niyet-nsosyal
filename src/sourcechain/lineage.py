from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from .schemas import EvidenceItem
from .text import normalize

# Common wire agencies and syndicated press syndicates
_SYNDICATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("reuters", re.compile(r"\b(?:reuters|thomson\s+reuters)\b", re.I)),
    ("associated_press", re.compile(r"\b(?:associated\s+press|ap\s+news|\bap\b)\b", re.I)),
    ("afp", re.compile(r"\b(?:agence\s+france[- ]presse|\bafp\b)\b", re.I)),
    ("bloomberg", re.compile(r"\b(?:bloomberg|bloomberg\s+news)\b", re.I)),
    ("anadolu_ajansi", re.compile(r"\b(?:anadolu\s+ajans[ıi]|\baa\b|anadolu\s+agency)\b", re.I)),
    ("demiroren_ajansi", re.compile(r"\b(?:demirören\s+haber\s+ajans[ıi]|\bdha\b)\b", re.I)),
    ("ihlas_ajansi", re.compile(r"\b(?:ihlas\s+haber\s+ajans[ıi]|\biha\b|i̇ha)\b", re.I)),
    ("anka_ajansi", re.compile(r"\b(?:anka\s+haber\s+ajans[ıi]|\banka\b)\b", re.I)),
    ("pr_newswire", re.compile(r"\b(?:pr\s+newswire|business\s+wire)\b", re.I)),
)

_COMMON_SUBDOMAINS = {"www", "m", "mobile", "news", "amp", "app", "tr", "en", "us", "uk", "feed"}


def extract_root_domain(url: str) -> str:
    """Extract registrable root domain or hostname, stripping common mobile/language prefixes."""
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        return ""
    parts = hostname.split(".")
    while len(parts) > 2 and parts[0] in _COMMON_SUBDOMAINS:
        parts.pop(0)
    # Handle country-code second-level domains like .co.uk, .com.tr, .org.tr
    if len(parts) >= 3 and parts[-1] in {"tr", "uk", "au", "br"} and parts[-2] in {"com", "co", "org", "net", "gov", "edu"}:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return hostname


def detect_syndication(text: str, publisher: str | None = None) -> str | None:
    """Identify whether a passage or publisher indicates content sourced from a wire syndicate."""
    target = f"{publisher or ''} {text}"
    for wire_id, pattern in _SYNDICATION_PATTERNS:
        if pattern.search(target):
            return wire_id
    return None


def calculate_token_jaccard(text1: str, text2: str) -> float:
    """Measure lexical similarity between two passages using normalized word tokens."""
    tokens1 = set(normalize(text1).split())
    tokens2 = set(normalize(text2).split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)
    return intersection / union if union > 0 else 0.0


@dataclass(frozen=True)
class OriginCluster:
    """A cluster of evidence items originating from the same primary root source."""

    cluster_id: str
    root_origin: str
    evidence_ids: tuple[str, ...]
    cluster_type: str
    wire_agency: str | None
    domain: str | None
    representative_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "root_origin": self.root_origin,
            "evidence_ids": list(self.evidence_ids),
            "cluster_type": self.cluster_type,
            "wire_agency": self.wire_agency,
            "domain": self.domain,
            "representative_url": self.representative_url,
        }


def cluster_evidence_origins(
    evidence: Iterable[EvidenceItem],
    similarity_threshold: float = 0.70,
) -> tuple[OriginCluster, ...]:
    """Group evidence items into measured independent origins.

    Prevents copied URLs, syndicated wire articles, and shared publisher domains
    from being artificially counted as independent corroborating evidence.
    """
    items = tuple(evidence)
    if not items:
        return ()

    n = len(items)
    # Disjoint Set Union (Union-Find)
    parent = list(range(n))

    def find(i: int) -> int:
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]

    def union(i: int, j: int) -> None:
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j

    wires: list[str | None] = []
    domains: list[str] = []

    for item in items:
        wire = detect_syndication(item.passage, item.publisher)
        domain = extract_root_domain(item.canonical_url or item.source_url)
        wires.append(wire)
        domains.append(domain)

    # Compare all pairs and merge non-independent sources
    for i in range(n):
        for j in range(i + 1, n):
            item_a, item_b = items[i], items[j]

            # 1. Same explicitly assigned origin_cluster_id
            if item_a.origin_cluster_id and item_a.origin_cluster_id == item_b.origin_cluster_id:
                union(i, j)
                continue

            # 2. Both cite the same syndicated wire agency
            if wires[i] is not None and wires[i] == wires[j]:
                union(i, j)
                continue

            # 3. Same registrable root domain or exact publisher
            if domains[i] and domains[i] == domains[j]:
                union(i, j)
                continue
            if item_a.publisher and item_b.publisher and normalize(item_a.publisher) == normalize(item_b.publisher):
                union(i, j)
                continue

            # 4. Verbatim or near-verbatim duplicate text (copied syndication)
            if calculate_token_jaccard(item_a.passage, item_b.passage) >= similarity_threshold:
                union(i, j)
                continue

    # Group into clusters
    groups: dict[int, list[int]] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)

    clusters: list[OriginCluster] = []
    for root_idx, member_indices in groups.items():
        member_items = [items[idx] for idx in member_indices]
        first_item = member_items[0]

        # Determine dominant origin identity
        detected_wire = next((wires[idx] for idx in member_indices if wires[idx]), None)
        dominant_domain = next((domains[idx] for idx in member_indices if domains[idx]), "unknown-domain")

        if detected_wire:
            cluster_type = "syndicated_wire"
            root_origin = f"wire:{detected_wire}"
        elif len(member_indices) > 1 and any(
            calculate_token_jaccard(items[a].passage, items[b].passage) >= similarity_threshold
            for a in member_indices for b in member_indices if a != b
        ):
            cluster_type = "content_duplicate"
            root_origin = f"content-dup:{dominant_domain}"
        elif len({domains[idx] for idx in member_indices}) == 1 and dominant_domain:
            cluster_type = "shared_publisher"
            root_origin = f"domain:{dominant_domain}"
        else:
            cluster_type = "independent_origin"
            root_origin = first_item.origin_cluster_id or f"origin:{dominant_domain}"

        clusters.append(
            OriginCluster(
                cluster_id=f"cluster-{root_idx}-{len(member_indices)}",
                root_origin=root_origin,
                evidence_ids=tuple(item.evidence_id for item in member_items),
                cluster_type=cluster_type,
                wire_agency=detected_wire,
                domain=dominant_domain,
                representative_url=first_item.canonical_url or first_item.source_url,
            )
        )

    # Sort deterministically
    clusters.sort(key=lambda c: c.root_origin)
    return tuple(clusters)


def independent_origin_count(evidence: Iterable[EvidenceItem], similarity_threshold: float = 0.70) -> int:
    """Return the measured count of truly independent origins among evidence items."""
    return len(cluster_evidence_origins(evidence, similarity_threshold=similarity_threshold))


def origin_cluster_counts(evidence: Iterable[EvidenceItem]) -> dict[str, int]:
    """Return distribution of evidence items across independent origin clusters."""
    clusters = cluster_evidence_origins(evidence)
    counts: dict[str, int] = {}
    for c in clusters:
        counts[c.root_origin] = len(c.evidence_ids)
    return dict(sorted(counts.items()))
