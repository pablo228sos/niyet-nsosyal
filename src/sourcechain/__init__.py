"""Deterministic SOURCECHAIN core with controlled-corpus evidence retrieval."""

from .evidence import build_evidence_bundle
from .pipeline import SourcechainPipeline
from .retrieval import ControlledEvidenceProvider, SourceDocument
from .schemas import EvidenceBundle
from .statement_classifier import analyze_post

__all__ = [
    "ControlledEvidenceProvider",
    "EvidenceBundle",
    "SourceDocument",
    "SourcechainPipeline",
    "analyze_post",
    "build_evidence_bundle",
]
