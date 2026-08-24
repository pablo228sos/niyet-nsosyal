from __future__ import annotations

from .passage_ranker import lexical_score
from .schemas import DistortionType, EvidenceRelation
from .structured_checks import detect_distortions, numeric_values
from .text import normalize, tokens


_CONFLICT_TYPES = {DistortionType.NUMERIC_DISTORTION, DistortionType.TEMPORAL_SHIFT, DistortionType.CAUSALITY_SHIFT, DistortionType.CERTAINTY_SHIFT}


def align_claim(claim: str, passage: str) -> EvidenceRelation:
    claim_terms = set(tokens(claim, meaningful=True))
    evidence_terms = set(tokens(passage, meaningful=True))
    overlap = len(claim_terms & evidence_terms) / max(1, len(claim_terms))
    if overlap < 0.25:
        return EvidenceRelation.INSUFFICIENT
    if set(detect_distortions(claim, passage)) & _CONFLICT_TYPES:
        return EvidenceRelation.CONFLICTING
    if normalize(claim).rstrip(".!") == normalize(passage).rstrip(".!"):
        return EvidenceRelation.SUPPORTED
    if numeric_values(claim) and not numeric_values(passage):
        return EvidenceRelation.PARTIALLY_SUPPORTED
    if lexical_score(claim, passage) >= 0.65 and overlap >= 0.6:
        return EvidenceRelation.SUPPORTED
    return EvidenceRelation.PARTIALLY_SUPPORTED
