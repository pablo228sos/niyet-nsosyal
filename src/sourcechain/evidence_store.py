from __future__ import annotations

import copy
import hashlib
import json
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .alignment import align_claim
from .evidence import _bundle_status, _stable_id, build_evidence_bundle
from .explanation import build_explanation
from .mismatch import source_mismatch
from .passage_ranker import split_passages
from .retrieval import ControlledEvidenceProvider, SourceDocument
from .schemas import (
    AtomicClaim,
    BundleStatus,
    DistortionType,
    EvidenceBundle,
    EvidenceItem,
    EvidenceRelation,
    PostAnalysis,
    StatementType,
)
from .structured_checks import detect_distortions


class EvidenceStoreError(Exception):
    """Base exception for evidence store errors."""


class ImmutableVersionConflictError(EvidenceStoreError):
    """Raised when an attempt is made to overwrite an existing bundle version with different data."""


class ContributionRejectedError(EvidenceStoreError):
    """Raised when a human-submitted source fails validation or produces no aligned evidence."""


class EvidenceNotFoundError(EvidenceStoreError):
    """Raised when a requested bundle or contribution does not exist."""


class ContributionStatus(StrEnum):
    PENDING = "PENDING"
    INGESTED = "INGESTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class BundleVersionRecord:
    """Immutable envelope for an EvidenceBundle version, with cryptographic hash and audit metadata."""

    bundle_id: str
    version: int
    bundle: EvidenceBundle
    bundle_hash: str
    created_at: datetime
    audit_metadata: dict[str, Any]
    document_hashes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "version": self.version,
            "bundle": self.bundle.to_dict(),
            "bundle_hash": self.bundle_hash,
            "created_at": self.created_at.isoformat(),
            "audit_metadata": copy.deepcopy(self.audit_metadata),
            "document_hashes": list(self.document_hashes),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BundleVersionRecord:
        bundle = EvidenceBundle.from_json(json.dumps(data["bundle"]))
        return cls(
            bundle_id=data["bundle_id"],
            version=int(data["version"]),
            bundle=bundle,
            bundle_hash=data["bundle_hash"],
            created_at=datetime.fromisoformat(data["created_at"]),
            audit_metadata=copy.deepcopy(data.get("audit_metadata", {})),
            document_hashes=tuple(data.get("document_hashes", ())),
        )


@dataclass(frozen=True)
class HumanSourceContribution:
    """A human-submitted candidate source awaiting algorithmic verification."""

    contribution_id: str
    claim_id: str
    source_url: str
    canonical_url: str
    title: str | None
    publisher: str | None
    text: str
    contributor_id: str
    rationale: str
    submitted_at: datetime
    status: ContributionStatus = ContributionStatus.PENDING
    rejection_reason: str | None = None
    ingested_evidence_id: str | None = None

    def __post_init__(self) -> None:
        if not self.contribution_id or not self.claim_id or not self.contributor_id:
            raise ValueError("contribution_id, claim_id, and contributor_id are required")
        for u in (self.source_url, self.canonical_url):
            parsed = urlparse(u)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("source URLs must use valid http or https scheme")
        if not self.text.strip():
            raise ValueError("contribution text is required")

    @property
    def document_hash(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "contribution_id": self.contribution_id,
            "claim_id": self.claim_id,
            "source_url": self.source_url,
            "canonical_url": self.canonical_url,
            "title": self.title,
            "publisher": self.publisher,
            "text": self.text,
            "contributor_id": self.contributor_id,
            "rationale": self.rationale,
            "submitted_at": self.submitted_at.isoformat(),
            "status": self.status.value,
            "rejection_reason": self.rejection_reason,
            "ingested_evidence_id": self.ingested_evidence_id,
            "document_hash": self.document_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HumanSourceContribution:
        return cls(
            contribution_id=data["contribution_id"],
            claim_id=data["claim_id"],
            source_url=data["source_url"],
            canonical_url=data["canonical_url"],
            title=data.get("title"),
            publisher=data.get("publisher"),
            text=data["text"],
            contributor_id=data["contributor_id"],
            rationale=data.get("rationale", ""),
            submitted_at=datetime.fromisoformat(data["submitted_at"]),
            status=ContributionStatus(data.get("status", "PENDING")),
            rejection_reason=data.get("rejection_reason"),
            ingested_evidence_id=data.get("ingested_evidence_id"),
        )


@dataclass(frozen=True)
class AuditRecord:
    """Audit log entry capturing state transitions and evidence provenance actions."""

    record_id: str
    bundle_id: str
    version: int
    action: str
    timestamp: datetime
    actor_id: str
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "bundle_id": self.bundle_id,
            "version": self.version,
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
            "actor_id": self.actor_id,
            "details": copy.deepcopy(self.details),
        }


def compute_bundle_hash(bundle: EvidenceBundle) -> str:
    """Compute deterministic SHA-256 hash of an EvidenceBundle's canonical JSON."""
    return hashlib.sha256(bundle.to_json().encode("utf-8")).hexdigest()


class MemoryEvidenceStore:
    """Thread-safe in-memory evidence store with strict immutability and contribution verification."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # Key: (bundle_id, version) -> BundleVersionRecord
        self._bundles: dict[tuple[str, int], BundleVersionRecord] = {}
        # Key: bundle_id -> latest_version
        self._latest_versions: dict[str, int] = {}
        # Key: contribution_id -> HumanSourceContribution
        self._contributions: dict[str, HumanSourceContribution] = {}
        # Key: bundle_id -> list[AuditRecord]
        self._audit_logs: dict[str, list[AuditRecord]] = {}

    def save_bundle(
        self,
        bundle: EvidenceBundle,
        *,
        actor_id: str = "system",
        audit_metadata: dict[str, Any] | None = None,
    ) -> BundleVersionRecord:
        """Persist an immutable EvidenceBundle version.

        If (bundle_id, version) already exists:
        - If bundle_hash matches, returns the existing record (idempotent).
        - If bundle_hash differs, raises ImmutableVersionConflictError.
        """
        audit_meta = copy.deepcopy(audit_metadata or {})
        bundle_hash = compute_bundle_hash(bundle)
        doc_hashes = tuple(item.document_hash for item in bundle.evidence)
        now = datetime.now(UTC)

        with self._lock:
            key = (bundle.bundle_id, bundle.version)
            if key in self._bundles:
                existing = self._bundles[key]
                if existing.bundle_hash != bundle_hash:
                    raise ImmutableVersionConflictError(
                        f"Cannot mutate bundle '{bundle.bundle_id}' version {bundle.version}: "
                        f"existing hash {existing.bundle_hash} != {bundle_hash}"
                    )
                return existing

            record = BundleVersionRecord(
                bundle_id=bundle.bundle_id,
                version=bundle.version,
                bundle=bundle,
                bundle_hash=bundle_hash,
                created_at=now,
                audit_metadata=audit_meta,
                document_hashes=doc_hashes,
            )

            self._bundles[key] = record
            curr_latest = self._latest_versions.get(bundle.bundle_id, 0)
            if bundle.version > curr_latest:
                self._latest_versions[bundle.bundle_id] = bundle.version

            self._record_audit(
                bundle_id=bundle.bundle_id,
                version=bundle.version,
                action="SAVE_BUNDLE",
                actor_id=actor_id,
                details={"bundle_hash": bundle_hash, "status": bundle.status.value, **audit_meta},
            )

            return record

    def get_bundle(self, bundle_id: str, version: int | None = None) -> EvidenceBundle | None:
        """Retrieve an EvidenceBundle by ID and optional version (defaults to latest)."""
        with self._lock:
            if version is None:
                version = self._latest_versions.get(bundle_id)
                if version is None:
                    return None
            record = self._bundles.get((bundle_id, version))
            return record.bundle if record is not None else None

    def get_version_record(self, bundle_id: str, version: int) -> BundleVersionRecord | None:
        with self._lock:
            return self._bundles.get((bundle_id, version))

    def list_versions(self, bundle_id: str) -> tuple[BundleVersionRecord, ...]:
        with self._lock:
            records = [rec for (b_id, _), rec in self._bundles.items() if b_id == bundle_id]
            records.sort(key=lambda r: r.version)
            return tuple(records)

    def submit_human_source(
        self,
        contribution: HumanSourceContribution,
        *,
        actor_id: str | None = None,
    ) -> HumanSourceContribution:
        """Submit a candidate source from a human contributor.

        Stored initially in PENDING status. Must re-enter algorithmic verification
        before any evidence or truth claims can be derived from it.
        """
        actor = actor_id or contribution.contributor_id
        with self._lock:
            self._contributions[contribution.contribution_id] = contribution
            self._record_audit(
                bundle_id="global",
                version=0,
                action="SUBMIT_HUMAN_SOURCE",
                actor_id=actor,
                details={
                    "contribution_id": contribution.contribution_id,
                    "claim_id": contribution.claim_id,
                    "source_url": contribution.source_url,
                    "document_hash": contribution.document_hash,
                },
            )
            return contribution

    def get_contribution(self, contribution_id: str) -> HumanSourceContribution | None:
        with self._lock:
            return self._contributions.get(contribution_id)

    def list_contributions(
        self,
        *,
        claim_id: str | None = None,
        status: ContributionStatus | None = None,
    ) -> tuple[HumanSourceContribution, ...]:
        with self._lock:
            results = list(self._contributions.values())
            if claim_id is not None:
                results = [c for c in results if c.claim_id == claim_id]
            if status is not None:
                results = [c for c in results if c.status == status]
            results.sort(key=lambda c: c.submitted_at)
            return tuple(results)

    def ingest_human_contribution(
        self,
        contribution_id: str,
        bundle_id: str,
        *,
        actor_id: str,
        now: datetime | None = None,
    ) -> tuple[EvidenceBundle, EvidenceItem]:
        """Verify and ingest a human-submitted source into a new bundle version.

        Crucial architectural invariant:
        Human sources are NEVER accepted as truth by submission or voting alone.
        The source is parsed into passages, matched against the target claim,
        and evaluated by SOURCECHAIN's claim alignment and distortion detection.
        If aligned evidence is found, a new immutable bundle version is created.
        """
        current_time = now or datetime.now(UTC)

        with self._lock:
            contrib = self._contributions.get(contribution_id)
            if contrib is None:
                raise EvidenceNotFoundError(f"Contribution '{contribution_id}' not found")

            if contrib.status is ContributionStatus.INGESTED:
                raise ContributionRejectedError(
                    f"Contribution '{contribution_id}' has already been ingested"
                )

            current_bundle = self.get_bundle(bundle_id)
            if current_bundle is None:
                raise EvidenceNotFoundError(f"Bundle '{bundle_id}' not found")

            # Locate target claim in bundle analysis
            target_claim: AtomicClaim | None = None
            for claim in current_bundle.analysis.claims:
                if claim.claim_id == contrib.claim_id:
                    target_claim = claim
                    break

            if target_claim is None:
                contrib_rejected = HumanSourceContribution(
                    contribution_id=contrib.contribution_id,
                    claim_id=contrib.claim_id,
                    source_url=contrib.source_url,
                    canonical_url=contrib.canonical_url,
                    title=contrib.title,
                    publisher=contrib.publisher,
                    text=contrib.text,
                    contributor_id=contrib.contributor_id,
                    rationale=contrib.rationale,
                    submitted_at=contrib.submitted_at,
                    status=ContributionStatus.REJECTED,
                    rejection_reason=f"Target claim '{contrib.claim_id}' not present in bundle '{bundle_id}'",
                )
                self._contributions[contribution_id] = contrib_rejected
                raise ContributionRejectedError(contrib_rejected.rejection_reason)

            # Algorithmic Verification: split passages and evaluate alignment
            passages = split_passages(contrib.text, limit=8)
            best_hit: tuple[str, str, EvidenceRelation, list[DistortionType]] | None = None

            for p_idx, passage in enumerate(passages):
                relation = align_claim(target_claim.text, passage)
                if relation is EvidenceRelation.INSUFFICIENT:
                    continue
                distortions = list(detect_distortions(target_claim.text, passage))
                if source_mismatch(target_claim.text, publisher=contrib.publisher) is True:
                    if DistortionType.ATTRIBUTION_SHIFT not in distortions:
                        distortions.append(DistortionType.ATTRIBUTION_SHIFT)
                if len(distortions) > 1 and DistortionType.NONE in distortions:
                    distortions.remove(DistortionType.NONE)

                best_hit = (passage, f"passage:{p_idx + 1}", relation, distortions)
                break

            if best_hit is None:
                contrib_rejected = HumanSourceContribution(
                    contribution_id=contrib.contribution_id,
                    claim_id=contrib.claim_id,
                    source_url=contrib.source_url,
                    canonical_url=contrib.canonical_url,
                    title=contrib.title,
                    publisher=contrib.publisher,
                    text=contrib.text,
                    contributor_id=contrib.contributor_id,
                    rationale=contrib.rationale,
                    submitted_at=contrib.submitted_at,
                    status=ContributionStatus.REJECTED,
                    rejection_reason="No passage aligned with claim with sufficient evidence relation",
                )
                self._contributions[contribution_id] = contrib_rejected
                raise ContributionRejectedError(contrib_rejected.rejection_reason)

            passage, p_loc, relation, distortions = best_hit
            parsed_url = urlparse(contrib.canonical_url)
            origin_cluster = f"web:{parsed_url.hostname or 'human-contributed'}"

            evidence_id = _stable_id("ev-human", bundle_id, contrib.claim_id, contrib.document_hash, p_loc)

            evidence_item = EvidenceItem(
                evidence_id=evidence_id,
                claim_id=contrib.claim_id,
                source_url=contrib.source_url,
                canonical_url=contrib.canonical_url,
                title=contrib.title or parsed_url.hostname,
                publisher=contrib.publisher or parsed_url.hostname,
                publication_date=contrib.submitted_at.strftime("%Y-%m-%d"),
                retrieved_at=contrib.submitted_at,
                passage=passage,
                passage_location=p_loc,
                document_hash=contrib.document_hash,
                relation=relation,
                distortions=tuple(distortions),
                origin_cluster_id=origin_cluster,
                metadata={
                    "contribution_id": contrib.contribution_id,
                    "contributor_id": contrib.contributor_id,
                    "rationale": contrib.rationale,
                    "source_type": "human_submitted",
                },
            )

            # Update contribution record to INGESTED
            contrib_ingested = HumanSourceContribution(
                contribution_id=contrib.contribution_id,
                claim_id=contrib.claim_id,
                source_url=contrib.source_url,
                canonical_url=contrib.canonical_url,
                title=contrib.title,
                publisher=contrib.publisher,
                text=contrib.text,
                contributor_id=contrib.contributor_id,
                rationale=contrib.rationale,
                submitted_at=contrib.submitted_at,
                status=ContributionStatus.INGESTED,
                ingested_evidence_id=evidence_id,
            )
            self._contributions[contribution_id] = contrib_ingested

            # Form updated immutable bundle version
            new_evidence = current_bundle.evidence + (evidence_item,)
            new_status = _bundle_status(current_bundle.analysis, new_evidence)
            new_explanation, cited_ids = build_explanation(new_status, new_evidence)

            new_version = current_bundle.version + 1
            new_bundle = EvidenceBundle(
                bundle_id=current_bundle.bundle_id,
                version=new_version,
                analysis=current_bundle.analysis,
                evidence=new_evidence,
                status=new_status,
                sufficient=new_status is BundleStatus.SUPPORTED,
                explanation=new_explanation,
                cited_evidence_ids=cited_ids,
                created_at=current_time,
            )

            self.save_bundle(
                new_bundle,
                actor_id=actor_id,
                audit_metadata={
                    "action": "INGEST_HUMAN_CONTRIBUTION",
                    "contribution_id": contribution_id,
                    "contributor_id": contrib.contributor_id,
                    "ingested_evidence_id": evidence_id,
                },
            )

            return new_bundle, evidence_item

    def _record_audit(
        self,
        bundle_id: str,
        version: int,
        action: str,
        actor_id: str,
        details: dict[str, Any],
    ) -> None:
        record_id = _stable_id("audit", bundle_id, str(version), action, str(datetime.now(UTC).timestamp()))
        record = AuditRecord(
            record_id=record_id,
            bundle_id=bundle_id,
            version=version,
            action=action,
            timestamp=datetime.now(UTC),
            actor_id=actor_id,
            details=details,
        )
        self._audit_logs.setdefault(bundle_id, []).append(record)

    def get_audit_trail(self, bundle_id: str) -> tuple[AuditRecord, ...]:
        with self._lock:
            return tuple(self._audit_logs.get(bundle_id, ()))
