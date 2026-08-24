from datetime import UTC, datetime

from sourcechain.alignment import align_claim
from sourcechain.claim_extractor import extract_claims
from sourcechain.evidence import build_evidence_bundle
from sourcechain.lineage import independent_origin_count
from sourcechain.pipeline import SourcechainPipeline
from sourcechain.retrieval import ControlledEvidenceProvider, SourceDocument
from sourcechain.schemas import BundleStatus, EvidenceRelation, StatementType
from sourcechain.statement_classifier import analyze_post


NOW = datetime(2026, 8, 24, tzinfo=UTC)


def document(url: str, text: str, *, cluster: str = "origin-1") -> SourceDocument:
    return SourceDocument(
        source_url=url,
        canonical_url=url,
        title="Controlled report",
        publisher="Example Institute",
        publication_date="2026-08-20",
        text=text,
        retrieved_at=NOW,
        origin_cluster_id=cluster,
    )


def test_statement_gate_excludes_question_opinion_and_experience():
    assert analyze_post("Bu doğru mu?").statement_type is StatementType.QUESTION
    assert not analyze_post("Bence bu film harika.").check_worthy
    assert analyze_post("Dün başım ağrıdı.").statement_type is StatementType.PERSONAL_EXPERIENCE
    factual = analyze_post("Rapor, satışların yüzde 20 arttığını açıkladı.")
    assert factual.statement_type is StatementType.FACTUAL_CLAIM
    assert factual.check_worthy


def test_claim_extraction_is_bounded_and_preserves_exact_offsets():
    text = "Satışlar yüzde 20 arttı. Enflasyon yüzde 10 düştü. Üçüncü iddia doğrudur."
    claims = extract_claims(text, max_claims=2)
    assert [text[item.start:item.end] for item in claims] == [item.text for item in claims]
    assert [item.claim_id for item in claims] == ["claim-1", "claim-2"]


def test_controlled_provider_ranks_passages_and_never_fetches_network():
    provider = ControlledEvidenceProvider(
        (
            document("https://example.org/weather", "Bugün hava yağmurlu. Yarın güneşli."),
            document("https://example.org/sales", "Denetlenen rapora göre satışlar yüzde 20 arttı."),
        ),
        max_documents=2,
        max_passages_per_document=2,
    )
    hits = provider.retrieve("Satışlar yüzde 20 arttı", limit=2)
    assert hits[0].document.canonical_url.endswith("/sales")
    assert "yüzde 20" in hits[0].passage
    assert len(hits) <= 2


def test_alignment_has_all_four_relations():
    assert align_claim("Satışlar yüzde 20 arttı.", "Satışlar yüzde 20 arttı.") is EvidenceRelation.SUPPORTED
    assert align_claim("Satışlar yüzde 20 arttı.", "Satışlar arttı.") is EvidenceRelation.PARTIALLY_SUPPORTED
    assert align_claim("Satışlar yüzde 20 arttı.", "Satışlar yüzde 10 azaldı.") is EvidenceRelation.CONFLICTING
    assert align_claim("Satışlar yüzde 20 arttı.", "Bugün hava yağmurlu.") is EvidenceRelation.INSUFFICIENT


def test_bundle_is_citation_first_and_counts_independent_origins():
    analysis = analyze_post("Satışlar yüzde 20 arttı.")
    provider = ControlledEvidenceProvider(
        (
            document("https://example.org/a", "Satışlar yüzde 20 arttı.", cluster="wire-1"),
            document("https://example.org/b", "Satışlar yüzde 20 arttı.", cluster="wire-1"),
        )
    )
    bundle = build_evidence_bundle(analysis, provider, now=NOW)
    assert bundle.status is BundleStatus.SUPPORTED
    assert bundle.sufficient
    assert bundle.cited_evidence_ids
    assert all(f"[{item}]" in bundle.explanation for item in bundle.cited_evidence_ids)
    assert all(item.canonical_url in bundle.explanation for item in bundle.evidence)
    assert independent_origin_count(bundle.evidence) == 1


def test_bundle_fails_closed_when_controlled_corpus_has_no_match():
    analysis = analyze_post("Satışlar yüzde 20 arttı.")
    provider = ControlledEvidenceProvider((document("https://example.org/weather", "Bugün hava yağmurlu."),))
    bundle = build_evidence_bundle(analysis, provider, now=NOW)
    assert bundle.status is BundleStatus.INSUFFICIENT
    assert not bundle.sufficient
    assert bundle.cited_evidence_ids == ()


def test_default_pipeline_has_no_implicit_or_fake_evidence_source():
    bundle = SourcechainPipeline().analyze("Satışlar yüzde 20 arttı.", now=NOW)
    assert bundle.status is BundleStatus.INSUFFICIENT
    assert bundle.evidence == ()
