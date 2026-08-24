from __future__ import annotations

import re

from sourcechain.schemas import (
    BundleStatus,
    DistortionType,
    EvidenceBundle,
    StatementType,
)

from .schemas import HumanEscalationRequest, ResolutionDecision, ResolutionPath


_NON_FACTUAL = {
    StatementType.OPINION,
    StatementType.PERSONAL_EXPERIENCE,
}


class ResolutionEngine:
    """Apply the explicit DRSK evidence/human resolution policy.

    Non-check-worthy speech needs no resolution. Sufficient, non-conflicting
    evidence stands on its own. Conflicts and low-confidence evidence combine
    evidence with human interpretation. Insufficient evidence is offered to a
    human when requested; otherwise the work is explicitly deferred.
    """

    def resolve(
        self,
        bundle: EvidenceBundle,
        *,
        ask_human: bool = False,
    ) -> ResolutionDecision:
        analysis = bundle.analysis
        if analysis.statement_type in _NON_FACTUAL or not analysis.check_worthy:
            return ResolutionDecision(
                path=ResolutionPath.NONE,
                reasons=("not_check_worthy",),
            )

        if bundle.status is BundleStatus.CONFLICTING:
            return ResolutionDecision(
                path=ResolutionPath.BOTH,
                reasons=("evidence_conflicting", "human_interpretation_required"),
                escalation=self._escalation(bundle, "resolve conflicting evidence"),
            )

        distortions = {
            distortion
            for evidence in bundle.evidence
            for distortion in evidence.distortions
        }
        if DistortionType.ATTRIBUTION_SHIFT in distortions:
            return ResolutionDecision(
                path=ResolutionPath.BOTH,
                reasons=("source_mismatch", "human_interpretation_required"),
                escalation=self._escalation(bundle, "interpret source attribution mismatch"),
            )

        material_distortions = distortions - {DistortionType.NONE}
        if material_distortions:
            return ResolutionDecision(
                path=ResolutionPath.BOTH,
                reasons=("evidence_distorted", "human_interpretation_required"),
                escalation=self._escalation(bundle, "interpret distorted evidence claim"),
            )

        if (
            bundle.status in {BundleStatus.SUPPORTED, BundleStatus.PARTIAL}
            and bundle.sufficient
        ):
            reason = (
                "evidence_supported"
                if bundle.status is BundleStatus.SUPPORTED
                else "evidence_partially_supported"
            )
            return ResolutionDecision(
                path=ResolutionPath.EVIDENCE,
                reasons=(reason,),
            )

        if bundle.status in {BundleStatus.SUPPORTED, BundleStatus.PARTIAL}:
            return ResolutionDecision(
                path=ResolutionPath.BOTH,
                reasons=("evidence_low_confidence", "human_interpretation_required"),
                escalation=self._escalation(bundle, "review low-confidence evidence"),
            )

        if ask_human:
            return ResolutionDecision(
                path=ResolutionPath.HUMAN,
                reasons=("evidence_insufficient", "human_resolution_requested"),
                escalation=self._escalation(bundle, "expert evidence review"),
            )

        return ResolutionDecision(
            path=ResolutionPath.DEFERRED,
            reasons=("evidence_insufficient", "human_resolution_available"),
        )

    @staticmethod
    def _escalation(
        bundle: EvidenceBundle,
        requested_resolution: str,
    ) -> HumanEscalationRequest:
        claims = bundle.analysis.claims
        claim_text = " ".join(claim.text.strip() for claim in claims if claim.text.strip())
        if not claim_text:
            claim_text = bundle.analysis.text.strip()
        distortions = tuple(
            sorted(
                {
                    distortion
                    for evidence in bundle.evidence
                    for distortion in evidence.distortions
                    if distortion is not DistortionType.NONE
                },
                key=lambda item: item.value,
            )
        )
        return HumanEscalationRequest(
            request_id=f"human-{bundle.bundle_id}",
            claim_text=claim_text,
            topic=_topic_from_claim(claim_text),
            evidence_status=bundle.status,
            distortion_types=distortions,
            requested_resolution=requested_resolution,
        )


def _topic_from_claim(claim_text: str) -> str:
    words = re.findall(r"[^\W_]+", claim_text.casefold(), flags=re.UNICODE)
    return " ".join(words[:6]) or "general"
