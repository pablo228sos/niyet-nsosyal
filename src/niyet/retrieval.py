from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from .types import Intent, Responder


DEFAULT_TURKISH_EMBEDDER = "ytu-ce-cosmos/modernbert-tr-embed"


class Encoder(Protocol):
    def encode(self, sentences, **kwargs): ...


@dataclass(frozen=True)
class RetrievalHit:
    responder_id: str
    similarity: float


def responder_document(responder: Responder) -> str:
    topics = ", ".join(responder.topics)
    intents = ", ".join(intent.value for intent in responder.willing_intents)
    return f"Konular: {topics}. Yanıt türleri: {intents}."


def eligible_responders(intent: Intent, responders: list[Responder]) -> list[Responder]:
    return [
        responder
        for responder in responders
        if responder.active
        and responder.attention_budget > 0
        and intent.kind in responder.willing_intents
    ]


def rank_embeddings(
    query_embedding: np.ndarray,
    document_embeddings: np.ndarray,
    responder_ids: list[str],
    *,
    top_k: int,
) -> list[RetrievalHit]:
    if document_embeddings.shape[0] != len(responder_ids):
        raise ValueError("document embedding count does not match responder ids")
    if not responder_ids or top_k <= 0:
        return []

    query = np.asarray(query_embedding, dtype=float).reshape(-1)
    documents = np.asarray(document_embeddings, dtype=float)
    if documents.ndim != 2 or documents.shape[1] != query.shape[0]:
        raise ValueError("embedding dimensions do not match")

    query_norm = np.linalg.norm(query)
    document_norms = np.linalg.norm(documents, axis=1)
    denominator = document_norms * query_norm
    similarities = np.divide(
        documents @ query,
        denominator,
        out=np.zeros_like(document_norms, dtype=float),
        where=denominator != 0,
    )

    order = np.argsort(-similarities)[: min(top_k, len(responder_ids))]
    return [
        RetrievalHit(responder_ids[index], float(similarities[index]))
        for index in order
    ]


class TurkishEmbeddingRetriever:
    def __init__(
        self,
        model_name: str = DEFAULT_TURKISH_EMBEDDER,
        *,
        encoder: Encoder | None = None,
    ) -> None:
        if encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise RuntimeError(
                    "Install the `embeddings` extra to use TurkishEmbeddingRetriever"
                ) from exc
            encoder = SentenceTransformer(model_name)

        self.encoder = encoder
        self.model_name = model_name

    def retrieve(
        self,
        intent: Intent,
        responders: list[Responder],
        *,
        top_k: int = 20,
    ) -> list[RetrievalHit]:
        candidates = eligible_responders(intent, responders)
        if not candidates:
            return []

        documents = [responder_document(responder) for responder in candidates]
        query_embedding = self.encoder.encode(
            [intent.text],
            prompt_name="query",
            normalize_embeddings=True,
        )[0]
        document_embeddings = self.encoder.encode(
            documents,
            normalize_embeddings=True,
        )

        return rank_embeddings(
            np.asarray(query_embedding),
            np.asarray(document_embeddings),
            [responder.id for responder in candidates],
            top_k=top_k,
        )
