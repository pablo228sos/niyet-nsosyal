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

    The verified in-repo corpus remains the deterministic fallback. Live web
    evidence activates only when BRAVE_SEARCH_API_KEY is present in the server
    environment, so local/tests and offline demo behavior stay reproducible.
    """

    controlled = ControlledEvidenceProvider(demo_documents())
    api_key = os.getenv("BRAVE_SEARCH_API_KEY", "").strip()
    if not api_key:
        return controlled

    from .brave_context import BraveContextEvidenceProvider

    live = BraveContextEvidenceProvider(api_key)
    return FallbackEvidenceProvider((live, controlled))


class SourcechainPipeline:
    """End-to-end evidence pipeline with a pluggable acquisition boundary."""

    def __init__(self, provider: EvidenceProvider | None = None) -> None:
        self.provider = provider or provider_from_environment()

    def analyze(self, text: str, *, now: datetime | None = None) -> EvidenceBundle:
        analysis = analyze_post(text)
        return build_evidence_bundle(analysis, self.provider, now=now)
