"""Deterministic SOURCECHAIN core with controlled-corpus evidence retrieval."""

from .claim_evolution import (
    ClaimEvolutionChain,
    ClaimTransformationHop,
    evaluate_claim_evolution_benchmark,
    trace_claim_evolution,
)
from .evidence import build_evidence_bundle
from .lineage import (
    OriginCluster,
    cluster_evidence_origins,
    independent_origin_count,
    origin_cluster_counts,
)
from .pipeline import SourcechainPipeline
from .retrieval import ControlledEvidenceProvider, SourceDocument
from .schemas import EvidenceBundle
from .statement_classifier import analyze_post

__all__ = [
    "ClaimEvolutionChain",
    "ClaimTransformationHop",
    "ControlledEvidenceProvider",
    "EvidenceBundle",
    "OriginCluster",
    "SourceDocument",
    "SourcechainPipeline",
    "analyze_post",
    "build_evidence_bundle",
    "cluster_evidence_origins",
    "evaluate_claim_evolution_benchmark",
    "independent_origin_count",
    "origin_cluster_counts",
    "trace_claim_evolution",
]
