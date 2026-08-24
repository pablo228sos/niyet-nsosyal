from __future__ import annotations

import re

from .text import normalize


_KNOWN_ATTRIBUTION = re.compile(r"\b(WHO|NASA|TÜİK|TUİK|UNICEF|OECD|World Health Organization)\b", re.I)
_ACCORDING_TO = re.compile(r"\baccording\s+to\s+([^,.;:]{2,80})[,;:]", re.I)


def source_mismatch(claim: str, *, publisher: str | None) -> bool | None:
    """True/False for explicit attribution; None means attribution is unknown."""
    if not publisher:
        return None
    match = _ACCORDING_TO.search(claim) or _KNOWN_ATTRIBUTION.search(claim)
    if not match:
        return None
    attribution = normalize(match.group(1)).strip()
    publisher_value = normalize(publisher)
    aliases = {
        "who": ("who", "world health organization"),
        "world health organization": ("who", "world health organization"),
        "tuik": ("tuik", "türkiye istatistik kurumu"),
        "tüik": ("tüik", "türkiye istatistik kurumu"),
    }
    return not any(value in publisher_value for value in aliases.get(attribution, (attribution,)))
