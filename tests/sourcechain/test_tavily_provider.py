from __future__ import annotations

import json

import pytest

from sourcechain.evidence import build_evidence_bundle
from sourcechain.pipeline import provider_from_environment
from sourcechain.retrieval import (
    ControlledEvidenceProvider,
    FallbackEvidenceProvider,
    MinimumScoreEvidenceProvider,
)
from sourcechain.schemas import BundleStatus, DistortionType
from sourcechain.statement_classifier import analyze_post
from sourcechain.tavily_search import TavilyEvidenceProvider


def _payload():
    return {
        "query": "coffee causes lower mortality",
        "results": [
            {
                "title": "Coffee and mortality study",
                "url": "https://example.org/coffee-study",
                "content": (
                    "Higher coffee consumption was associated with lower risk of total mortality. "
                    "The observational study does not establish that coffee causes lower mortality."
                ),
                "score": 0.91,
            }
        ],
        "usage": {"credits": 1},
    }


def _weak_unrelated_payload():
    return {
        "query": "2026 Karakol sensor pilot reduced PM2.5 by 37 percent",
        "results": [
            {
                "title": "Seasonal particulate matter sensors",
                "url": "https://example.org/pm-sensors",
                "content": (
                    "A 2023 study measured annual PM2.5 concentrations with higher winter values "
                    "using municipal low-cost particulate matter sensors in another city."
                ),
                "score": 0.82,
            }
        ],
    }


def _numeric_coincidence_payload():
    return {
        "query": "2026 Karakol sensor pilot reduced PM2.5 by exactly 37 percent",
        "results": [
            {
                "title": "Largest number divisible by 37",
                "url": "https://example.org/math/37",
                "content": "What is the largest 5-digit number which is exactly divisible by 37?",
                "score": 0.95,
            },
            {
                "title": "Calculate 37 percent of 5",
                "url": "https://example.org/math/percentage",
                "content": "What is 37 percent of 5? For example: 37% of 5 = 1.85.",
                "score": 0.91,
            },
        ],
    }


def _strong_turkish_payload():
    return {
        "query": "Düzenli fiziksel aktivite kalp hastalığı riski",
        "results": [
            {
                "title": "Fiziksel aktivite ve kalp sağlığı",
                "url": "https://example.org/tr/activity",
                "content": (
                    "Düzenli fiziksel aktivite daha düşük kardiyovasküler hastalık riski ile ilişkilidir."
                ),
                "score": 0.89,
            }
        ],
    }


def test_tavily_provider_turns_search_results_into_provenanced_hits():
    calls = []

    def transport(query: str, timeout: float):
        calls.append((query, timeout))
        return _payload()

    provider = TavilyEvidenceProvider("secret", transport=transport)
    hits = provider.retrieve("coffee causes lower mortality", limit=3)

    assert calls == [("coffee causes lower mortality", 8.0)]
    assert hits
    assert hits[0].provider == "tavily_search"
    assert hits[0].document.source_url == "https://example.org/coffee-study"
    assert hits[0].document.publisher == "example.org"
    assert hits[0].document.origin_cluster_id == "web:example.org"


def test_tavily_evidence_still_uses_sourcechain_relation_and_distortion_logic():
    provider = TavilyEvidenceProvider("secret", transport=lambda _q, _t: _payload())
    analysis = analyze_post("Research proves coffee consumption causes lower mortality.")
    bundle = build_evidence_bundle(analysis, provider)

    assert bundle.status is BundleStatus.CONFLICTING
    assert bundle.evidence
    assert bundle.evidence[0].metadata["provider"] == "tavily_search"
    assert DistortionType.CAUSALITY_SHIFT in bundle.evidence[0].distortions


def test_tavily_fails_closed_on_weak_live_match():
    provider = TavilyEvidenceProvider("secret", transport=lambda _q, _t: _weak_unrelated_payload())
    hits = provider.retrieve(
        "The 2026 Karakol municipal sensor pilot reduced winter PM2.5 by exactly 37 percent.",
        limit=3,
    )

    assert hits == ()


def test_tavily_fails_closed_when_numbers_create_spurious_overlap():
    provider = TavilyEvidenceProvider("secret", transport=lambda _q, _t: _numeric_coincidence_payload())
    hits = provider.retrieve(
        "The 2026 Karakol municipal sensor pilot reduced winter PM2.5 by exactly 37 percent.",
        limit=3,
    )

    assert hits == ()


def test_tavily_keeps_strong_turkish_live_match():
    provider = TavilyEvidenceProvider("secret", transport=lambda _q, _t: _strong_turkish_payload())
    hits = provider.retrieve(
        "Düzenli fiziksel aktivite daha düşük kalp hastalığı riski ile ilişkilidir.",
        limit=3,
    )

    assert hits
    assert hits[0].provider == "tavily_search"
    assert hits[0].score >= 0.30


def test_tavily_rejects_underspecified_deictic_claim_without_search():
    calls = []
    provider = TavilyEvidenceProvider(
        "secret",
        transport=lambda query, timeout: calls.append((query, timeout)) or _payload(),
    )

    hits = provider.retrieve("This new battery lasts twice as long.", limit=3)

    assert hits == ()
    assert calls == []


def test_tavily_excludes_user_generated_sources_from_evidence():
    payload = {
        "results": [
            {
                "title": "Social post",
                "url": "https://www.facebook.com/example/posts/1",
                "content": "The Eiffel Tower is 330 metres tall.",
            },
            {
                "title": "Official visitor information",
                "url": "https://www.toureiffel.paris/en/monument/key-figures",
                "content": "The Eiffel Tower is 330 metres tall including its antenna.",
            },
        ]
    }
    provider = TavilyEvidenceProvider("secret", transport=lambda _q, _t: payload)

    hits = provider.retrieve("The Eiffel Tower is 330 metres tall.", limit=3)

    assert [hit.document.publisher for hit in hits] == ["www.toureiffel.paris"]


def test_tavily_sends_configured_search_depth(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, _limit):
            return json.dumps({"results": []}).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("sourcechain.tavily_search.urlopen", fake_urlopen)
    provider = TavilyEvidenceProvider("secret", search_depth="advanced")

    assert provider.retrieve("coffee mortality", limit=1) == ()
    assert captured["payload"]["search_depth"] == "advanced"
    assert captured["timeout"] == 8.0


def test_tavily_rejects_unknown_search_depth():
    with pytest.raises(ValueError, match="search_depth"):
        TavilyEvidenceProvider("secret", search_depth="deep")


def test_environment_uses_verified_first_advanced_live_cascade(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-secret")
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "brave-secret")

    provider = provider_from_environment()

    assert isinstance(provider, FallbackEvidenceProvider)
    assert isinstance(provider.providers[0], MinimumScoreEvidenceProvider)
    assert isinstance(provider.providers[0].provider, ControlledEvidenceProvider)
    assert provider.providers[0].min_score == 0.38
    assert isinstance(provider.providers[1], TavilyEvidenceProvider)
    assert provider.providers[1].search_depth == "advanced"
    assert provider.providers[2].__class__.__name__ == "BraveContextEvidenceProvider"
    assert isinstance(provider.providers[3], ControlledEvidenceProvider)


def test_verified_judge_case_short_circuits_live_search(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-secret")
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    provider = provider_from_environment()

    hits = provider.retrieve("Research proves coffee consumption causes lower mortality.", limit=3)

    assert hits
    assert all(hit.provider == "controlled" for hit in hits)
    assert hits[0].document.publisher == "Circulation"


def test_topic_only_controlled_match_does_not_block_live_retrieval(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tavily-secret")
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
    provider = provider_from_environment()
    priority_provider = provider.providers[0]

    hits = priority_provider.retrieve(
        "Regular physical activity is associated with a lower risk of cardiovascular disease.",
        limit=3,
    )

    assert hits == ()


def test_environment_stays_controlled_without_live_provider_keys(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

    provider = provider_from_environment()

    assert isinstance(provider, ControlledEvidenceProvider)
