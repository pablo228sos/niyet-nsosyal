from __future__ import annotations

from .passage_ranker import lexical_score
from .schemas import DistortionType, EvidenceRelation
from .structured_checks import detect_distortions, has_negation, numeric_values
from .text import normalize, tokens


_CONFLICT_TYPES = {DistortionType.NUMERIC_DISTORTION, DistortionType.TEMPORAL_SHIFT, DistortionType.CAUSALITY_SHIFT, DistortionType.CERTAINTY_SHIFT}


def align_claim(claim: str, passage: str) -> EvidenceRelation:
    claim_terms = set(tokens(claim, meaningful=True))
    evidence_terms = set(tokens(passage, meaningful=True))
    overlap = len(claim_terms & evidence_terms) / max(1, len(claim_terms))
    # Single-letter symbols are meaningful in scientific shorthand ("X causes
    # Y"), while ordinary stopwords must not manufacture a conflict between
    # unrelated sentences.
    claim_symbols = {token for token in tokens(claim) if len(token) == 1}
    evidence_symbols = {token for token in tokens(passage) if len(token) == 1}
    content_overlap = (claim_terms | claim_symbols) & (evidence_terms | evidence_symbols)
    shared_symbols = claim_symbols & evidence_symbols
    structured_overlap = overlap >= 0.5 or len(shared_symbols) >= 2
    distortions = set(detect_distortions(claim, passage))
    polarity_conflict = has_negation(claim) != has_negation(passage)
    if content_overlap and structured_overlap and (
        distortions & _CONFLICT_TYPES or polarity_conflict
    ):
        return EvidenceRelation.CONFLICTING
    if overlap < 0.25:
        return EvidenceRelation.INSUFFICIENT
    if normalize(claim).rstrip(".!") == normalize(passage).rstrip(".!"):
        return EvidenceRelation.SUPPORTED
    if numeric_values(claim) and not numeric_values(passage):
        return EvidenceRelation.PARTIALLY_SUPPORTED
    if lexical_score(claim, passage) >= 0.65 and overlap >= 0.6:
        return EvidenceRelation.SUPPORTED
    return EvidenceRelation.PARTIALLY_SUPPORTED
