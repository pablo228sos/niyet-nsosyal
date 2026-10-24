from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import pytest

from sourcechain.claim_evolution import (
    ClaimEvolutionChain,
    ClaimTransformationHop,
    evaluate_claim_evolution_benchmark,
    trace_claim_evolution,
)
from sourcechain.lineage import (
    OriginCluster,
    calculate_token_jaccard,
    cluster_evidence_origins,
    detect_syndication,
    extract_root_domain,
    independent_origin_count,
    origin_cluster_counts,
)
from sourcechain.schemas import DistortionType, EvidenceItem, EvidenceRelation

NOW = datetime(2026, 8, 24, 12, 0, 0, tzinfo=UTC)


def make_evidence_item(
    item_id: str,
    url: str,
    passage: str,
    *,
    publisher: str | None = None,
    origin_cluster_id: str = "cluster-default",
) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=item_id,
        claim_id="claim-1",
        source_url=url,
        canonical_url=url,
        title="Title",
        publisher=publisher,
        publication_date="2026-08-20",
        retrieved_at=NOW,
        passage=passage,
        passage_location="p:1",
        document_hash=f"hash-{item_id}",
        relation=EvidenceRelation.SUPPORTED,
        distortions=(DistortionType.NONE,),
        origin_cluster_id=origin_cluster_id,
        metadata={},
    )


def test_extract_root_domain():
    assert extract_root_domain("https://www.reuters.com/world/article") == "reuters.com"
    assert extract_root_domain("https://m.news.bbc.co.uk/story") == "bbc.co.uk"
    assert extract_root_domain("https://haberler.hurriyet.com.tr/gundem") == "hurriyet.com.tr"
    assert extract_root_domain("https://sub.domain.example.org/path") == "example.org"


def test_detect_syndication():
    assert detect_syndication("(Reuters) - The central bank announced new rates.") == "reuters"
    assert detect_syndication("Demirören Haber Ajansı'nın bildirdiğine göre...") == "demiroren_ajansi"
    assert detect_syndication("Haber metni burada.", publisher="Anadolu Ajansı") == "anadolu_ajansi"
    assert detect_syndication("AP News reported the decision.") == "associated_press"
    assert detect_syndication("Bağımsız yerel blog yazısı.") is None


def test_calculate_token_jaccard():
    t1 = "Şirketin kârı bu çeyrekte yüzde 20 arttı ve rekor kırdı."
    t2 = "Şirketin kârı bu çeyrekte yüzde 20 arttı ve rekor kırdı."
    assert calculate_token_jaccard(t1, t2) == 1.0

    t3 = "Hava durumu yarın güneşli ve sıcak olacak."
    assert calculate_token_jaccard(t1, t3) < 0.1

    t4 = "Şirketin kârı bu çeyrekte yüzde 20 arttı."
    sim = calculate_token_jaccard(t1, t4)
    assert 0.5 < sim < 1.0


def test_syndicated_wire_deduplication():
    # Three distinct news URLs all syndicating the exact same Reuters wire story
    item1 = make_evidence_item(
        "ev-1",
        "https://www.portal-a.com/story1",
        "(Reuters) - The European Central Bank kept interest rates unchanged.",
        publisher="Portal A",
        origin_cluster_id="cluster-a",
    )
    item2 = make_evidence_item(
        "ev-2",
        "https://news.portal-b.org/article",
        "Reuters reported that the European Central Bank kept interest rates unchanged.",
        publisher="Portal B",
        origin_cluster_id="cluster-b",
    )
    item3 = make_evidence_item(
        "ev-3",
        "https://financial-post.net/news",
        "According to Thomson Reuters, the European Central Bank kept interest rates unchanged.",
        publisher="Financial Post",
        origin_cluster_id="cluster-c",
    )

    clusters = cluster_evidence_origins([item1, item2, item3])
    # Must group into 1 independent origin cluster because they all stem from the Reuters wire
    assert len(clusters) == 1
    assert clusters[0].cluster_type == "syndicated_wire"
    assert clusters[0].wire_agency == "reuters"
    assert independent_origin_count([item1, item2, item3]) == 1


def test_shared_domain_and_content_duplicate_clustering():
    # Two subdomains of the same publisher
    item1 = make_evidence_item(
        "ev-1",
        "https://www.bbc.com/news/1",
        "Inflation fell to 2 percent in the latest quarter.",
        publisher="BBC",
        origin_cluster_id="c1",
    )
    item2 = make_evidence_item(
        "ev-2",
        "https://m.bbc.com/news/1-mobile",
        "Inflation dropped to 2 percent in the previous period.",
        publisher="BBC",
        origin_cluster_id="c2",
    )

    # An independent source from another institution
    item3 = make_evidence_item(
        "ev-3",
        "https://www.reuters.com/economy",
        "The Office for National Statistics confirmed inflation hit 2 percent.",
        publisher="Reuters",
        origin_cluster_id="c3",
    )

    clusters = cluster_evidence_origins([item1, item2, item3])
    assert len(clusters) == 2
    assert independent_origin_count([item1, item2, item3]) == 2

    counts = origin_cluster_counts([item1, item2, item3])
    assert len(counts) == 2


def test_verbatim_duplicate_deduplication():
    # Two different domains with verbatim duplicate press release text without explicit wire mentions
    press_release = "Acme Corp launched its new solar battery storage module today with 10kWh capacity."
    item1 = make_evidence_item("ev-1", "https://tech-site-one.com/acme", press_release, publisher="Tech One", origin_cluster_id="c1")
    item2 = make_evidence_item("ev-2", "https://clean-energy-daily.org/acme", press_release, publisher="Clean Energy", origin_cluster_id="c2")

    clusters = cluster_evidence_origins([item1, item2])
    assert len(clusters) == 1
    assert clusters[0].cluster_type == "content_duplicate"
    assert independent_origin_count([item1, item2]) == 1


def test_trace_claim_evolution_multihop():
    chain = trace_claim_evolution(
        chain_id="test-chain-1",
        scenario="medical_exaggeration",
        statements=[
            "Yeni laboratuvar çalışmasında, bileşik X'in farelerde tümör hücre büyümesiyle ilişkili olabileceği öneriliyor.",
            "Yeni çalışma, bileşik X'in tümör hücre büyümesiyle ilişkili olduğunu kesin kanıtladı.",
            "Bileşik X kansere doğrudan neden olur.",
        ],
        notes=["Hop 1: Certainty inflation", "Hop 2: Correlation to causation shift"],
    )

    assert chain.chain_id == "test-chain-1"
    assert chain.hop_count == 2
    assert chain.is_distorted is True

    hop1 = chain.hops[0]
    assert hop1.hop_index == 1
    assert DistortionType.CERTAINTY_SHIFT in hop1.distortions

    hop2 = chain.hops[1]
    assert hop2.hop_index == 2
    assert DistortionType.CAUSALITY_SHIFT in hop2.distortions

    assert DistortionType.CERTAINTY_SHIFT in chain.cumulative_distortions
    assert DistortionType.CAUSALITY_SHIFT in chain.cumulative_distortions

    chain_dict = chain.to_dict()
    assert chain_dict["chain_id"] == "test-chain-1"
    assert len(chain_dict["hops"]) == 2


def test_trace_claim_evolution_requires_two_statements():
    with pytest.raises(ValueError, match="must contain at least 2 statements"):
        trace_claim_evolution("short-chain", "scenario", ["Only one statement"])


def test_claim_evolution_benchmark_evaluation():
    benchmark_file = Path(__file__).resolve().parents[2] / "data" / "sourcebench_tr" / "claim_evolution.jsonl"
    results = evaluate_claim_evolution_benchmark(benchmark_file)

    assert results["total_chains"] >= 6
    assert results["total_hops"] >= 9
    assert results["hop_accuracy"] >= 0.85
    assert results["chain_accuracy"] >= 0.80

    # Ensure key distortion dimensions are evaluated with high F1
    assert results["distortion_f1"]["CERTAINTY_SHIFT"] >= 0.80
    assert results["distortion_f1"]["CAUSALITY_SHIFT"] >= 0.80
    assert results["distortion_f1"]["NUMERIC_DISTORTION"] >= 0.80
    assert results["distortion_f1"]["SCOPE_SHIFT"] >= 0.80
    assert results["distortion_f1"]["TEMPORAL_SHIFT"] >= 0.80
