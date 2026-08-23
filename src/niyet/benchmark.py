from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .types import CandidateMatch, Intent, IntentType, Responder


@dataclass(frozen=True)
class LabeledMatch:
    match: CandidateMatch
    gold_relevance: int


@dataclass(frozen=True)
class Benchmark:
    intents: tuple[Intent, ...]
    responders: tuple[Responder, ...]
    matches: tuple[LabeledMatch, ...]


def load_benchmark(path: str | Path) -> Benchmark:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))

    intents = tuple(
        Intent(
            id=item["id"],
            author_id=item["author_id"],
            kind=IntentType(item["kind"]),
            topic=item["topic"],
            text=item["text"],
        )
        for item in raw["intents"]
    )
    responders = tuple(
        Responder(
            id=item["id"],
            topics=tuple(item["topics"]),
            willing_intents=tuple(IntentType(kind) for kind in item["willing_intents"]),
            attention_budget=item.get("attention_budget", 1),
            active=item.get("active", True),
        )
        for item in raw["responders"]
    )

    matches = []
    for item in raw["matches"]:
        gold_relevance = int(item["gold_relevance"])
        if gold_relevance < 0 or gold_relevance > 3:
            raise ValueError("gold_relevance must be between 0 and 3")
        matches.append(
            LabeledMatch(
                match=CandidateMatch(
                    intent_id=item["intent_id"],
                    responder_id=item["responder_id"],
                    topic_relevance=float(item["topic_relevance"]),
                    willingness=float(item["willingness"]),
                    availability=float(item["availability"]),
                    eligible=bool(item.get("eligible", True)),
                ),
                gold_relevance=gold_relevance,
            )
        )

    return Benchmark(
        intents=intents,
        responders=responders,
        matches=tuple(matches),
    )
