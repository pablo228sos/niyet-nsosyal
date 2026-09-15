from __future__ import annotations

from sourcechain.brave_context import BraveContextEvidenceProvider
from sourcechain.evidence import build_evidence_bundle
from sourcechain.pipeline import provider_from_environment
from sourcechain.retrieval import ControlledEvidenceProvider, FallbackEvidenceProvider, SourceDocument
from sourcechain.schemas import BundleStatus, DistortionType
from sourcechain.statement_classifier import analyze_post


def _payload():
    url = "https://example.org/coffee-study"
    return {
        "grounding": {
            "generic": [
                {
                    "url": url,
                    "title": "Coffee and mortality study",
                    "snippets": [
                        "Higher coffee consumption was associated with lower risk of total mortality.",
                        "The observational study does not establish that coffee causes lower mortality.",
                    ],
                }
            ]
        },
        "sources": {
            url: {
                "hostname": "example.org",
                "site_name": "Example Journal",
                "age": ["10 years ago", "2015-12-15T00:00:00Z"],
            }
        },
    }


def test_brave_provider_turns_live_context_into_provenanced_retrieval_hits():
    calls = []

    def transport(query: str, timeout: float):
        calls.append((query, timeout))
        return _payload()

    provider = BraveContextEvidenceProvider("secret", transport=transport)
    hits = provider.retrieve("coffee causes lower mortality", limit=3)

    assert calls and calls[0][0] == "coffee causes lower mortality"
    assert hits
    assert hits[0].provider == "brave_llm_context"
    assert hits[0].document.source_url == "https://example.org/coffee-study"
    assert hits[0].document.publisher == "Example Journal"
    assert hits[0].document.publication_date == "2015-12-15"
    assert hits[0].document.origin_cluster_id == "web:example.org"


def test_live_web_evidence_still_uses_sourcechain_relation_and_distortion_logic():
    provider = BraveContextEvidenceProvider("secret", transport=lambda _q, _t: _payload())
    analysis = analyze_post("Research proves coffee consumption causes lower mortality.")
    bundle = build_evidence_bundle(analysis, provider)

    assert bundle.status is BundleStatus.CONFLICTING
    assert bundle.evidence
    assert bundle.evidence[0].metadata["provider"] == "brave_llm_context"
    assert DistortionType.CAUSALITY_SHIFT in bundle.evidence[0].distortions
    assert bundle.evidence[0].source_url == "https://example.org/coffee-study"


def test_fallback_provider_uses_controlled_evidence_when_live_provider_fails():
    class BrokenProvider:
        def retrieve(self, query: str, *, limit: int = 5):
            raise TimeoutError("network down")

    controlled = ControlledEvidenceProvider(
        [
            SourceDocument(
                source_url="https://example.org/report",
                canonical_url="https://example.org/report",
                title="Report",
                publisher="Example",
                publication_date=None,
                text="Sales increased by 20 percent.",
                retrieved_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
                origin_cluster_id="example-report",
            )
        ]
    )
    provider = FallbackEvidenceProvider((BrokenProvider(), controlled))
    hits = provider.retrieve("Sales increased by 20 percent", limit=2)

    assert hits
    assert hits[0].provider == "controlled"


def test_environment_provider_keeps_offline_default_without_api_key(monkeypatch):
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    provider = provider_from_environment()
    assert isinstance(provider, ControlledEvidenceProvider)


def test_environment_provider_adds_live_search_when_key_is_configured(monkeypatch):
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "demo-secret")
    provider = provider_from_environment()
    assert isinstance(provider, FallbackEvidenceProvider)
    assert isinstance(provider.providers[0], BraveContextEvidenceProvider)
    assert isinstance(provider.providers[1], ControlledEvidenceProvider)
