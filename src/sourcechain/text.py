from __future__ import annotations

import re


_TOKEN_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)?", re.UNICODE)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "on", "or", "that", "the", "to", "was", "were", "with",
    "ama", "bir", "bu", "da", "de", "gibi", "göre", "ile", "ise", "ve", "veya", "için", "olarak", "olduğunu",
}


def normalize(text: str) -> str:
    return " ".join(text.casefold().replace("ı", "i").split())


def tokens(text: str, *, meaningful: bool = False) -> tuple[str, ...]:
    result = tuple(normalize(match.group(0)) for match in _TOKEN_RE.finditer(text))
    if meaningful:
        return tuple(token for token in result if token not in _STOPWORDS and len(token) > 1)
    return result

