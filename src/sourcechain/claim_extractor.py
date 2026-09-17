from __future__ import annotations

import re

from .schemas import AtomicClaim


_SENTENCE_BOUNDARY_RE = re.compile(r"\n|[!?]+|(?<!\d)\.|(?<=\d)\.(?!\d)")


def _sentence_spans(text: str):
    """Yield sentence spans without splitting versions or grouped numbers."""
    start = 0
    for boundary in _SENTENCE_BOUNDARY_RE.finditer(text):
        end = boundary.end()
        yield start, end
        start = end
    if start < len(text):
        yield start, len(text)


def extract_claims(text: str, *, max_claims: int = 5, max_claim_chars: int = 500) -> tuple[AtomicClaim, ...]:
    """Extract bounded, exact sentence spans; it does not invent or rewrite claim text."""
    if max_claims < 0 or max_claim_chars < 1:
        raise ValueError("claim bounds must be positive")
    claims: list[AtomicClaim] = []
    for start, end in _sentence_spans(text):
        while start < end and text[start].isspace():
            start += 1
        while end > start and text[end - 1].isspace():
            end -= 1
        claim_text = text[start:end]
        if not claim_text or claim_text.endswith("?"):
            continue
        if len(claim_text) > max_claim_chars:
            end = start + max_claim_chars
            claim_text = text[start:end].rstrip()
            end = start + len(claim_text)
        claims.append(AtomicClaim(f"claim-{len(claims) + 1}", claim_text, start, end))
        if len(claims) >= max_claims:
            break
    return tuple(claims)
