from __future__ import annotations

import re

from .claim_extractor import extract_claims
from .schemas import PostAnalysis, StatementType
from .text import normalize


_OPINION = re.compile(r"\b(bence|bana göre|sanırım|fikrimce|düşünüyorum|i think|in my opinion)\b", re.I)
_SUBJECTIVE_COMPARISON = re.compile(
    r"(?:\b(?:looks?|feels?|tastes?|sounds?|seems?)\s+(?:much\s+)?(?:better|worse|nicer|prettier|uglier)\b"
    r"|\b(?:is|are)\s+(?:much\s+)?(?:better|worse|nicer|prettier|uglier)\s+than\b"
    r"|\b(?:daha|çok|en)\s+(?:iyi|kötü|güzel|çirkin|hoş)\s+(?:görünüyor|duruyor|hissettiriyor|geliyor)\b)",
    re.I,
)
_EXPERIENCE = re.compile(r"\b(ben|benim|bende|yaşadım|hissettim|başım|kolum|ağrıdı|gördüm|i experienced|my)\b", re.I)
_PREDICTION = re.compile(r"\b(muhtemelen|gelecekte|olacak|bekleniyor|tahmin|will|likely)\b", re.I)
_FACT_SIGNAL = re.compile(
    r"\b(rapor|araştırma|çalışma|açıkladı|bildirdi|kanıtladı|ispatladı|oran|yüzde|%|according|research|study|report|proves|showed|found|increased|decreased)\b",
    re.I,
)
_SENTENCE = re.compile(r"[^.!?\n]+[.!?]?", re.MULTILINE)


def _has_factual_signal(value: str) -> bool:
    return bool(_FACT_SIGNAL.search(normalize(value))) or bool(re.search(r"\d", value))


def _has_declarative_factual_segment(value: str) -> bool:
    """Keep a factual statement check-worthy when a user adds a follow-up question.

    A pure question such as ``Bu doğru mu?`` remains a QUESTION. A social post such
    as ``Study X proves Y. Can someone explain this?`` is MIXED so SOURCECHAIN can
    inspect the exact declarative claim while NIYET can still handle the response need.
    """

    for match in _SENTENCE.finditer(value):
        segment = match.group(0).strip()
        if not segment or segment.endswith("?"):
            continue
        if _has_factual_signal(segment):
            return True
    return False


def classify_statement(text: str) -> StatementType:
    value = text.strip()
    if not value:
        return StatementType.OPINION

    opinion = bool(_OPINION.search(value) or _SUBJECTIVE_COMPARISON.search(value))
    experience = bool(_EXPERIENCE.search(value))
    prediction = bool(_PREDICTION.search(value))
    factual = _has_factual_signal(value)

    if value.endswith("?"):
        return (
            StatementType.MIXED
            if _has_declarative_factual_segment(value)
            else StatementType.QUESTION
        )

    if sum((opinion or experience, prediction, factual)) > 1:
        return StatementType.MIXED
    if experience:
        return StatementType.PERSONAL_EXPERIENCE
    if opinion:
        return StatementType.OPINION
    if prediction:
        return StatementType.PREDICTION
    return StatementType.FACTUAL_CLAIM


def analyze_post(text: str, *, max_claims: int = 5) -> PostAnalysis:
    statement_type = classify_statement(text)
    check_worthy = statement_type in {StatementType.FACTUAL_CLAIM, StatementType.MIXED}
    claims = extract_claims(text, max_claims=max_claims) if check_worthy else ()
    return PostAnalysis(text=text, statement_type=statement_type, check_worthy=check_worthy, claims=claims)
