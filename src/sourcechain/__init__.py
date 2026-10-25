"""Deterministic SOURCECHAIN core with controlled-corpus evidence retrieval."""

from .alignment_model import (
    AlignmentPrediction,
    TurkishAlignmentClassifier,
    extract_alignment_features,
)
from .evidence import build_evidence_bundle
from .pipeline import SourcechainPipeline
from .retrieval import ControlledEvidenceProvider, SourceDocument
from .schemas import EvidenceBundle
from .statement_classifier import analyze_post

__all__ = [
    "AlignmentPrediction",
    "ControlledEvidenceProvider",
    "EvidenceBundle",
    "SourceDocument",
    "SourcechainPipeline",
    "TurkishAlignmentClassifier",
    "analyze_post",
    "build_evidence_bundle",
    "extract_alignment_features",
]
