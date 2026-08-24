from datetime import UTC, datetime

from drsk.resolution import ResolutionEngine
from drsk.schemas import ResolutionPath
from sourcechain.schemas import (
    AtomicClaim,
    BundleStatus,
    EvidenceBundle,
    PostAnalysis,
    StatementType,
    DistortionType,
    EvidenceItem,
    EvidenceRelation,
)


def bundle(
    status: BundleStatus,
    *,
    statement_type: StatementType = StatementType.FACTUAL_CLAIM,
    sufficient: bool = False,
) -> EvidenceBundle:
    text = "Research proves X causes Y."
    return EvidenceBundle(
        bundle_id="bundle-1",
        version=1,
        analysis=PostAnalysis(
            text=text,
            statement_type=statement_type,
            check_worthy=statement_type == StatementType.FACTUAL_CLAIM,
            claims=(AtomicClaim("claim-1", text, 0, len(text)),),
        ),
        evidence=(),
        status=status,
        sufficient=sufficient,
        explanation="Controlled result.",
        cited_evidence_ids=(),
        created_at=datetime(2026, 8, 24, tzinfo=UTC),
    )


def test_opinion_requires_no_resolution():
    decision = ResolutionEngine().resolve(
        bundle(BundleStatus.INSUFFICIENT, statement_type=StatementType.OPINION)
    )

    assert decision.path is ResolutionPath.NONE
    assert decision.escalation is None


def test_supported_sufficient_claim_uses_evidence():
    decision = ResolutionEngine().resolve(
        bundle(BundleStatus.SUPPORTED, sufficient=True)
    )

    assert decision.path is ResolutionPath.EVIDENCE
    assert decision.escalation is None


def test_conflicting_claim_uses_evidence_and_human():
    decision = ResolutionEngine().resolve(bundle(BundleStatus.CONFLICTING))

    assert decision.path is ResolutionPath.BOTH
    assert decision.escalation is not None
    assert decision.escalation.evidence_status is BundleStatus.CONFLICTING


def test_partial_low_confidence_claim_uses_evidence_and_human():
    decision = ResolutionEngine().resolve(bundle(BundleStatus.PARTIAL))

    assert decision.path is ResolutionPath.BOTH
    assert decision.escalation is not None


def test_insufficient_claim_escalates_only_when_requested():
    engine = ResolutionEngine()

    deferred = engine.resolve(bundle(BundleStatus.INSUFFICIENT))
    escalated = engine.resolve(bundle(BundleStatus.INSUFFICIENT), ask_human=True)

    assert deferred.path is ResolutionPath.DEFERRED
    assert deferred.escalation is None
    assert escalated.path is ResolutionPath.HUMAN
    assert escalated.escalation is not None


def test_source_mismatch_requires_evidence_and_human_interpretation():
    base = bundle(BundleStatus.PARTIAL, sufficient=True)
    evidence = EvidenceItem(
        evidence_id="ev-1",
        claim_id="claim-1",
        source_url="https://example.org/report",
        canonical_url="https://example.org/report",
        title="Report",
        publisher="Example Institute",
        publication_date="2026-08-24",
        retrieved_at=datetime(2026, 8, 24, tzinfo=UTC),
        passage="X is associated with Y.",
        passage_location="passage:1",
        document_hash="abc",
        relation=EvidenceRelation.PARTIALLY_SUPPORTED,
        distortions=(DistortionType.ATTRIBUTION_SHIFT, DistortionType.CAUSALITY_SHIFT),
        origin_cluster_id="origin-1",
        metadata={},
    )
    mismatched = EvidenceBundle(
        **{**base.__dict__, "evidence": (evidence,), "cited_evidence_ids": ("ev-1",)}
    )

    decision = ResolutionEngine().resolve(mismatched)

    assert decision.path is ResolutionPath.BOTH
    assert decision.escalation is not None
    assert "source_mismatch" in decision.reasons


def test_causality_distortion_requires_evidence_and_human_interpretation():
    base = bundle(BundleStatus.PARTIAL, sufficient=True)
    evidence = EvidenceItem(
        evidence_id="ev-causal",
        claim_id="claim-1",
        source_url="https://example.org/study",
        canonical_url="https://example.org/study",
        title="Study",
        publisher="Example Journal",
        publication_date="2026-08-24",
        retrieved_at=datetime(2026, 8, 24, tzinfo=UTC),
        passage="X is associated with Y.",
        passage_location="passage:1",
        document_hash="causal-hash",
        relation=EvidenceRelation.PARTIALLY_SUPPORTED,
        distortions=(DistortionType.CAUSALITY_SHIFT,),
        origin_cluster_id="origin-1",
        metadata={},
    )
    distorted = EvidenceBundle(
        **{**base.__dict__, "evidence": (evidence,), "cited_evidence_ids": ("ev-causal",)}
    )

    decision = ResolutionEngine().resolve(distorted)

    assert decision.path is ResolutionPath.BOTH
    assert decision.escalation is not None
    assert "evidence_distorted" in decision.reasons
