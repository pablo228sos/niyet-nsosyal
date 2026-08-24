from __future__ import annotations

from datetime import datetime

from .corpus import demo_documents
from .evidence import build_evidence_bundle
from .retrieval import ControlledEvidenceProvider
from .schemas import EvidenceBundle
from .statement_classifier import analyze_post


class SourcechainPipeline:
    """End-to-end deterministic pipeline over an explicitly supplied corpus."""

    def __init__(self, provider: ControlledEvidenceProvider | None = None) -> None:
        self.provider = provider or ControlledEvidenceProvider(demo_documents())

    def analyze(self, text: str, *, now: datetime | None = None) -> EvidenceBundle:
        analysis = analyze_post(text)
        return build_evidence_bundle(analysis, self.provider, now=now)
