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
