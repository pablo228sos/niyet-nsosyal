from datetime import UTC, datetime

import pytest

from drsk.schemas import HumanEscalationRequest, ResolutionDecision, ResolutionPath
from sourcechain.schemas import (
    AtomicClaim,
    BundleStatus,
    DistortionType,
    EvidenceBundle,
    EvidenceItem,
    EvidenceRelation,
    PostAnalysis,
    StatementType,
)


NOW = datetime(2026, 8, 24, tzinfo=UTC)


def evidence(evidence_id: str = "ev-1") -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        claim_id="claim-1",
        source_url="https://example.org/report",
        canonical_url="https://example.org/report",
        title="Controlled report",
        publisher="Example Institute",
        publication_date=None,
        retrieved_at=NOW,
        passage="X was associated with Y.",
        passage_location="paragraph:3",
        document_hash="a" * 64,
        relation=EvidenceRelation.CONFLICTING,
        distortions=(DistortionType.CAUSALITY_SHIFT,),
        origin_cluster_id="origin-1",
        metadata={"corpus": "controlled-demo"},
    )


def test_bundle_json_round_trip_is_deterministic():
    analysis = PostAnalysis(
        text="Research proves X causes Y.",
        statement_type=StatementType.FACTUAL_CLAIM,
        check_worthy=True,
        claims=(AtomicClaim("claim-1", "Research proves X causes Y.", 0, 27),),
    )
    bundle = EvidenceBundle(
        bundle_id="bundle-1",
        version=1,
        analysis=analysis,
        evidence=(evidence(),),
        status=BundleStatus.CONFLICTING,
        sufficient=True,
        explanation="[ev-1] Evidence describes association, while the claim states causation.",
        cited_evidence_ids=("ev-1",),
        created_at=NOW,
    )

    assert EvidenceBundle.from_json(bundle.to_json()) == bundle
    assert bundle.to_json() == bundle.to_json()


def test_bundle_rejects_unknown_explanation_citation():
    with pytest.raises(ValueError, match="unknown evidence"):
        EvidenceBundle(
            bundle_id="bundle-1",
            version=1,
            analysis=PostAnalysis("x", StatementType.FACTUAL_CLAIM, True, ()),
            evidence=(evidence(),),
            status=BundleStatus.CONFLICTING,
            sufficient=False,
            explanation="[missing] no source",
            cited_evidence_ids=("missing",),
            created_at=NOW,
        )


def test_evidence_requires_safe_provenance_and_plain_text():
    with pytest.raises(ValueError, match="http or https"):
        evidence().__class__(**{**evidence().__dict__, "source_url": "file:///secret"})
    with pytest.raises(ValueError, match="HTML"):
        evidence().__class__(**{**evidence().__dict__, "passage": "<script>alert(1)</script>"})


def test_resolution_and_escalation_serialize():
    escalation = HumanEscalationRequest(
        request_id="human-1",
        claim_text="X causes Y",
        topic="research",
        evidence_status=BundleStatus.INSUFFICIENT,
        distortion_types=(),
        requested_resolution="expert interpretation",
    )
    decision = ResolutionDecision(
        path=ResolutionPath.HUMAN,
        reasons=("evidence_insufficient",),
        escalation=escalation,
    )
    assert decision.to_dict()["path"] == "HUMAN"
