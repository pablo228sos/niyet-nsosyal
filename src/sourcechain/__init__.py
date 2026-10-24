"""Deterministic SOURCECHAIN core with controlled-corpus evidence retrieval."""

from .evidence import build_evidence_bundle
from .evidence_store import (
    AuditRecord,
    BundleVersionRecord,
    ContributionRejectedError,
    ContributionStatus,
    EvidenceNotFoundError,
    EvidenceStoreError,
    HumanSourceContribution,
    ImmutableVersionConflictError,
    MemoryEvidenceStore,
    compute_bundle_hash,
)
from .pipeline import SourcechainPipeline
from .retrieval import ControlledEvidenceProvider, SourceDocument
from .schemas import EvidenceBundle
from .statement_classifier import analyze_post

__all__ = [
    "AuditRecord",
    "BundleVersionRecord",
    "ContributionRejectedError",
    "ContributionStatus",
    "ControlledEvidenceProvider",
    "EvidenceBundle",
    "EvidenceNotFoundError",
    "EvidenceStoreError",
    "HumanSourceContribution",
    "ImmutableVersionConflictError",
    "MemoryEvidenceStore",
    "SourceDocument",
    "SourcechainPipeline",
    "analyze_post",
    "build_evidence_bundle",
    "compute_bundle_hash",
]
