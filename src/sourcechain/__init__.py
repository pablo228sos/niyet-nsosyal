"""Deterministic SOURCECHAIN core with controlled-corpus evidence retrieval."""

from .evidence import build_evidence_bundle
from .pipeline import SourcechainPipeline
from .retrieval import ControlledEvidenceProvider, SourceDocument
from .safe_web import (
    SafeFetchResult,
    SafeUrlFetcher,
    SafeWebEvidenceProvider,
    SSRFProtectionError,
)
from .schemas import EvidenceBundle
from .statement_classifier import analyze_post

__all__ = [
    "ControlledEvidenceProvider",
    "EvidenceBundle",
    "SSRFProtectionError",
    "SafeFetchResult",
    "SafeUrlFetcher",
    "SafeWebEvidenceProvider",
    "SourceDocument",
    "SourcechainPipeline",
    "analyze_post",
    "build_evidence_bundle",
]
