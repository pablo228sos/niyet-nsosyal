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
