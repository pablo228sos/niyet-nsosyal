from __future__ import annotations

import re

from .text import normalize


_ATTRIBUTION = re.compile(r"\b(WHO|NASA|TÜİK|TUİK|UNICEF|OECD|World Health Organization)\b", re.I)


def source_mismatch(claim: str, *, publisher: str | None) -> bool | None:
    """True/False for explicit attribution; None means attribution is unknown."""
    match = _ATTRIBUTION.search(claim)
    if not match or not publisher:
        return None
    attribution = normalize(match.group(1))
    publisher_value = normalize(publisher)
    aliases = {
        "who": ("who", "world health organization"),
        "world health organization": ("who", "world health organization"),
        "tuik": ("tuik", "türkiye istatistik kurumu"),
    }
    return not any(value in publisher_value for value in aliases.get(attribution, (attribution,)))
