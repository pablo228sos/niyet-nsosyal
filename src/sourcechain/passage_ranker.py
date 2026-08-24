from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from .text import tokens


@dataclass(frozen=True)
class PassageCandidate:
    document_index: int
    passage_index: int
    text: str


def split_passages(text: str, limit: int) -> tuple[str, ...]:
    parts = [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", text) if item.strip()]
    return tuple(parts[:limit])


def lexical_score(query: str, passage: str) -> float:
    query_tokens = Counter(tokens(query, meaningful=True))
    passage_tokens = Counter(tokens(passage, meaningful=True))
    if not query_tokens or not passage_tokens:
        return 0.0
    overlap = sum(min(count, passage_tokens[token]) for token, count in query_tokens.items())
    coverage = overlap / sum(query_tokens.values())
    precision = overlap / sum(passage_tokens.values())
    return (2 * coverage * precision / (coverage + precision)) if coverage + precision else 0.0


def rank_passages(query: str, candidates: list[PassageCandidate], *, limit: int) -> tuple[tuple[PassageCandidate, float], ...]:
    scored = ((candidate, lexical_score(query, candidate.text)) for candidate in candidates)
    return tuple(sorted(scored, key=lambda pair: (-pair[1], pair[0].document_index, pair[0].passage_index))[:limit])
