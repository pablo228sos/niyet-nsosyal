from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class IntentType(StrEnum):
    ASK = "ask"
    FEEDBACK = "feedback"
    COLLABORATE = "collaborate"
    DISCUSS = "discuss"


@dataclass(frozen=True)
class Intent:
    id: str
    author_id: str
    kind: IntentType
    topic: str
    text: str


@dataclass(frozen=True)
class Responder:
    id: str
    topics: tuple[str, ...]
    willing_intents: tuple[IntentType, ...]
    attention_budget: int = 1


@dataclass(frozen=True)
class CandidateMatch:
    intent_id: str
    responder_id: str
    topic_relevance: float
    willingness: float
    response_probability: float
