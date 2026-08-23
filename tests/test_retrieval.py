import numpy as np

from niyet.retrieval import (
    eligible_responders,
    rank_embeddings,
    responder_document,
)
from niyet.types import Intent, IntentType, Responder


def test_only_active_willing_responders_are_candidates():
    intent = Intent("i1", "u1", IntentType.ASK, "python", "Python sorum var")
    responders = [
        Responder("good", ("python",), (IntentType.ASK,), 1, True),
        Responder("paused", ("python",), (IntentType.ASK,), 1, False),
        Responder("full", ("python",), (IntentType.ASK,), 0, True),
        Responder("not-willing", ("python",), (IntentType.DISCUSS,), 1, True),
    ]

    result = eligible_responders(intent, responders)

    assert [responder.id for responder in result] == ["good"]


def test_embedding_ranking_uses_cosine_similarity():
    query = np.array([1.0, 0.0])
    documents = np.array(
        [
            [1.0, 0.0],
            [0.6, 0.8],
            [0.0, 1.0],
        ]
    )

    hits = rank_embeddings(query, documents, ["a", "b", "c"], top_k=2)

    assert [hit.responder_id for hit in hits] == ["a", "b"]
    assert hits[0].similarity == 1.0


def test_responder_document_contains_topics_and_intents():
    responder = Responder(
        "r1",
        ("robotics", "control"),
        (IntentType.ASK, IntentType.COLLABORATE),
        2,
    )

    text = responder_document(responder)

    assert "robotics" in text
    assert "control" in text
    assert "ask" in text
    assert "collaborate" in text
