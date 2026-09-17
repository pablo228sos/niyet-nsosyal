from __future__ import annotations

import os
from datetime import datetime

from .corpus import demo_documents
from .evidence import build_evidence_bundle
from .retrieval import (
    ControlledEvidenceProvider,
    EvidenceProvider,
    FallbackEvidenceProvider,
    MinimumScoreEvidenceProvider,
)
from .schemas import EvidenceBundle
from .statement_classifier import analyze_post


# Keep only genuinely strong verified-corpus matches on the fast path. The
# coffee judge case scores about 0.40 and the NASA case about 0.67, while a
# topic-only physical-activity match sits around 0.35 and should continue to
# live retrieval for more specific evidence.
CONTROLLED_PRIORITY_SCORE = 0.38
LIVE_BASIC_PRIORITY_SCORE = 0.40


def provider_from_environment() -> EvidenceProvider:
    """Build the evidence acquisition chain without exposing credentials client-side.

    A strong match in the small verified corpus is preferred because it is fast,
    deterministic and provenance-stable. Unseen claims first use a cheap Tavily
    basic search with a stricter quality gate, then advanced search only when the
    basic result is too weak. The full controlled corpus remains the final
    offline fallback so provider failure never creates invented evidence.
    """

    controlled = ControlledEvidenceProvider(demo_documents())

    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    brave_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    if not tavily_key and not brave_key:
        return controlled

    providers: list[EvidenceProvider] = [
        MinimumScoreEvidenceProvider(controlled, min_score=CONTROLLED_PRIORITY_SCORE)
    ]

    if tavily_key:
        from .tavily_search import TavilyEvidenceProvider

        providers.append(
            MinimumScoreEvidenceProvider(
                TavilyEvidenceProvider(tavily_key, search_depth="basic"),
                min_score=LIVE_BASIC_PRIORITY_SCORE,
            )
        )
        providers.append(TavilyEvidenceProvider(tavily_key, search_depth="advanced"))

    if brave_key:
        from .brave_context import BraveContextEvidenceProvider

        providers.append(BraveContextEvidenceProvider(brave_key))

    providers.append(controlled)
    return FallbackEvidenceProvider(providers)


class SourcechainPipeline:
    """End-to-end evidence pipeline with a pluggable acquisition boundary."""

    def __init__(self, provider: EvidenceProvider | None = None) -> None:
        self.provider = provider or provider_from_environment()

    def analyze(self, text: str, *, now: datetime | None = None) -> EvidenceBundle:
        analysis = analyze_post(text)
        return build_evidence_bundle(analysis, self.provider, now=now)
