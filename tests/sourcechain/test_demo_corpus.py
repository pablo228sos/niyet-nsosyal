from drsk.orchestrator import DrskOrchestrator
from drsk.resolution import ResolutionEngine
from sourcechain.pipeline import SourcechainPipeline
from sourcechain.schemas import BundleStatus, DistortionType


def test_default_corpus_exposes_real_association_passage_and_causality_shift():
    bundle = SourcechainPipeline().analyze(
        "Research proves coffee consumption causes lower mortality."
    )

    assert bundle.status in {BundleStatus.PARTIAL, BundleStatus.CONFLICTING}
    assert bundle.evidence
    assert bundle.evidence[0].source_url == "https://pubmed.ncbi.nlm.nih.gov/26572796/"
    assert DistortionType.CAUSALITY_SHIFT in bundle.evidence[0].distortions
    assert bundle.evidence[0].evidence_id in bundle.cited_evidence_ids


def test_demo_provenance_and_explanation_are_traceable_to_stored_passage():
    bundle = SourcechainPipeline().analyze(
        "Research proves coffee consumption causes lower mortality."
    )
    item = bundle.evidence[0]

    assert item.source_url == item.canonical_url == "https://pubmed.ncbi.nlm.nih.gov/26572796/"
    assert item.title == "Association of Coffee Consumption With Total and Cause-Specific Mortality in 3 Large Prospective Cohorts"
    assert item.publisher == "Circulation"
    assert item.publication_date == "2015-12-15"
    assert item.passage == (
        "Higher consumption of total coffee, caffeinated coffee, and "
        "decaffeinated coffee was associated with lower risk of total mortality."
    )
    assert item.passage_location == "passage:1"
    assert item.document_hash
    assert f"[{item.evidence_id}]" in bundle.explanation
    assert item.passage in bundle.explanation


def test_who_exact_claim_follows_evidence_only_path():
    text = "Regular physical activity provides significant physical and mental health benefits."
    bundle = SourcechainPipeline().analyze(text)
    decision = ResolutionEngine().resolve(bundle, ask_human=True)

    assert bundle.status is BundleStatus.SUPPORTED
    assert bundle.sufficient is True
    assert len(bundle.evidence) == 1
    assert bundle.evidence[0].publisher == "World Health Organization"
    assert bundle.evidence[0].source_url == (
        "https://www.who.int/news-room/fact-sheets/detail/physical-activity"
    )
    assert decision.path.value == "EVIDENCE"
    assert decision.escalation is None


def test_nasa_numeric_change_is_conflicting_and_requires_human_context():
    text = (
        "Industrial activities have raised atmospheric carbon dioxide levels "
        "by nearly 90% since 1750."
    )
    result = DrskOrchestrator().analyze(text, ask_human=True)

    bundle = result["evidence_bundle"]
    assert bundle["status"] == "CONFLICTING"
    assert bundle["evidence"][0]["publisher"] == "NASA"
    assert bundle["evidence"][0]["source_url"] == (
        "https://science.nasa.gov/climate-change/causes/"
    )
    assert "NUMERIC_DISTORTION" in bundle["evidence"][0]["distortions"]
    assert result["resolution"]["path"] == "BOTH"
    assert result["human_routing"] is not None


def test_unknown_factual_claim_stays_insufficient_and_can_route_to_human():
    result = DrskOrchestrator().analyze(
        "Turkish NLP embedding retrieval accuracy is 40 percent worse.",
        ask_human=True,
    )

    assert result["evidence_bundle"]["status"] == "INSUFFICIENT"
    assert result["evidence_bundle"]["evidence"] == []
    assert result["resolution"]["path"] == "HUMAN"
    assert result["human_routing"]["responder_id"] == "r_ml"


def test_opinion_bypasses_evidence_and_human_resolution():
    result = DrskOrchestrator().analyze(
        "I think this interface feels calmer.",
        ask_human=True,
    )

    assert result["evidence_bundle"]["analysis"]["statement_type"] == "OPINION"
    assert result["evidence_bundle"]["evidence"] == []
    assert result["resolution"]["path"] == "NONE"
    assert result["human_routing"] is None
