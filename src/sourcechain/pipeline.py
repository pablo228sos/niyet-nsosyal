from __future__ import annotations

import os
from datetime import datetime

from .corpus import demo_documents
from .evidence import build_evidence_bundle
from .retrieval import ControlledEvidenceProvider, EvidenceProvider, FallbackEvidenceProvider
from .schemas import EvidenceBundle
from .statement_classifier import analyze_post


def provider_from_environment() -> EvidenceProvider:
    """Build the evidence acquisition chain without exposing credentials client-side.

    The verified in-repo corpus remains the deterministic fallback. Tavily is the
    preferred live provider when TAVILY_API_KEY is configured. Brave remains an
    optional secondary provider. Local/tests and offline demo behavior stay fully
    reproducible when no live-search credentials are present.
    """

    controlled = ControlledEvidenceProvider(demo_documents())
    providers: list[EvidenceProvider] = []

    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    if tavily_key:
        from .tavily_search import TavilyEvidenceProvider

        providers.append(TavilyEvidenceProvider(tavily_key))

    brave_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    if brave_key:
        from .brave_context import BraveContextEvidenceProvider

        providers.append(BraveContextEvidenceProvider(brave_key))

    if not providers:
        return controlled

    providers.append(controlled)
    return FallbackEvidenceProvider(providers)


class SourcechainPipeline:
    """End-to-end evidence pipeline with a pluggable acquisition boundary."""

    def __init__(self, provider: EvidenceProvider | None = None) -> None:
        self.provider = provider or provider_from_environment()

    def analyze(self, text: str, *, now: datetime | None = None) -> EvidenceBundle:
        analysis = analyze_post(text)
        return build_evidence_bundle(analysis, self.provider, now=now)
