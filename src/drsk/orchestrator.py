from __future__ import annotations

from typing import Any, Protocol

from niyet.runtime import NiyetRuntime
from sourcechain.schemas import EvidenceBundle

from .adapter import NiyetEscalationAdapter
from .resolution import ResolutionEngine


class EvidencePipeline(Protocol):
    def analyze(self, text: str) -> EvidenceBundle: ...


class DrskOrchestrator:
    """Run SOURCECHAIN, resolve its bundle, then route human work through NIYET."""

    def __init__(
        self,
        sourcechain: EvidencePipeline | None = None,
        niyet_runtime: NiyetRuntime | None = None,
        resolution_engine: ResolutionEngine | None = None,
    ) -> None:
        self.sourcechain = (
            sourcechain if sourcechain is not None else _default_sourcechain()
        )
        self.resolution_engine = (
            resolution_engine if resolution_engine is not None else ResolutionEngine()
        )
        self.niyet_adapter = NiyetEscalationAdapter(niyet_runtime)

    def analyze(
        self,
        text: str,
        ask_human: bool = False,
        responder_state: dict | None = None,
    ) -> dict[str, Any]:
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("text_required")

        bundle = self.sourcechain.analyze(clean_text)
        decision = self.resolution_engine.resolve(bundle, ask_human=ask_human)
        human_routing = None
        if decision.escalation is not None:
            human_routing = self.niyet_adapter.route(
                decision.escalation,
                responder_state=responder_state,
            )

        return {
            "evidence_bundle": bundle.to_dict(),
            "resolution": decision.to_dict(),
            "human_routing": human_routing,
        }


def _default_sourcechain() -> EvidencePipeline:
    # Kept local so schemas and tests remain importable while optional pipeline
    # dependencies are being assembled.
    from sourcechain.pipeline import SourcechainPipeline

    return SourcechainPipeline()
