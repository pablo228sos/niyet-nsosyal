from __future__ import annotations

import re

from .claim_extractor import extract_claims
from .schemas import PostAnalysis, StatementType
from .text import normalize


_OPINION = re.compile(r"\b(bence|bana göre|sanırım|fikrimce|i think|in my opinion)\b", re.I)
_EXPERIENCE = re.compile(r"\b(ben|benim|bende|yaşadım|hissettim|başım|gördüm|i experienced|my)\b", re.I)
_PREDICTION = re.compile(r"\b(muhtemelen|gelecekte|olacak|bekleniyor|tahmin|will|likely)\b", re.I)
_FACT_SIGNAL = re.compile(r"\b(rapor|araştırma|açıkladı|bildirdi|oran|yüzde|%|according|study|report|increased|decreased)\b", re.I)


def classify_statement(text: str) -> StatementType:
    value = text.strip()
    if not value:
        return StatementType.OPINION
    if value.endswith("?"):
        return StatementType.QUESTION
    opinion = bool(_OPINION.search(value))
    experience = bool(_EXPERIENCE.search(value))
    prediction = bool(_PREDICTION.search(value))
    factual = bool(_FACT_SIGNAL.search(normalize(value))) or bool(re.search(r"\d", value))
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
