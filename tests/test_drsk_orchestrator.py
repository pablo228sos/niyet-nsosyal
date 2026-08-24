from datetime import UTC, datetime

from drsk.orchestrator import DrskOrchestrator
from drsk.schemas import HumanEscalationRequest
from niyet.runtime import RouteDecision
from sourcechain.schemas import (
    AtomicClaim,
    BundleStatus,
    EvidenceBundle,
    PostAnalysis,
    StatementType,
)


class StubSourcechain:
    def analyze(self, text: str) -> EvidenceBundle:
        return EvidenceBundle(
            bundle_id="bundle-1",
            version=1,
            analysis=PostAnalysis(
                text=text,
                statement_type=StatementType.FACTUAL_CLAIM,
                check_worthy=True,
                claims=(AtomicClaim("claim-1", text, 0, len(text)),),
            ),
            evidence=(),
            status=BundleStatus.INSUFFICIENT,
            sufficient=False,
            explanation="No controlled evidence.",
            cited_evidence_ids=(),
            created_at=datetime(2026, 8, 24, tzinfo=UTC),
        )


class SpyNiyet:
    def __init__(self) -> None:
        self.text = ""
        self.state = None

    def route(self, text: str, *, intent_override, responder_state=None):
        self.text = text
        self.state = responder_state
        return RouteDecision(
            response_needed=True,
            intent=intent_override.value,
            responder_id="r_research",
            responder_name="Researcher",
            reason=("topic profile: research",),
            development_utility=0.9,
            retrieval_similarity=0.8,
            request_id="route-1",
        )


def test_orchestrator_routes_structured_human_escalation_and_returns_json_ready_result():
    niyet = SpyNiyet()
    orchestrator = DrskOrchestrator(sourcechain=StubSourcechain(), niyet_runtime=niyet)
    state = {"r_research": {"remaining_slots": 1, "active": True}}

    result = orchestrator.analyze("Research proves X causes Y.", ask_human=True, responder_state=state)

    assert result["resolution"]["path"] == "HUMAN"
    assert result["evidence_bundle"]["status"] == "INSUFFICIENT"
    assert result["human_routing"]["responder_id"] == "r_research"
    assert "evidence_status: INSUFFICIENT" in niyet.text
    assert "claim: Research proves X causes Y." in niyet.text
    assert niyet.state is state


def test_adapter_contract_is_a_human_escalation_request():
    orchestrator = DrskOrchestrator(sourcechain=StubSourcechain(), niyet_runtime=SpyNiyet())

    result = orchestrator.analyze("Research proves X causes Y.", ask_human=True)

    escalation = result["resolution"]["escalation"]
    assert HumanEscalationRequest(**{
        **escalation,
        "evidence_status": BundleStatus(escalation["evidence_status"]),
        "distortion_types": tuple(escalation["distortion_types"]),
    }).claim_text == "Research proves X causes Y."


def test_real_sourcechain_to_niyet_path_is_executable():
    result = DrskOrchestrator().analyze(
        "Makine öğrenmesi modeli üretimde yüzde 40 daha başarılıdır.",
        ask_human=True,
    )

    assert result["evidence_bundle"]["status"] == "INSUFFICIENT"
    assert result["resolution"]["path"] == "HUMAN"
    assert result["human_routing"]["intent"] == "ask"
    assert result["human_routing"]["responder_id"] == "r_ml"
