from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from urllib.parse import urlparse

from .passage_ranker import PassageCandidate, rank_passages, split_passages


@dataclass(frozen=True)
class SourceDocument:
    source_url: str
    canonical_url: str
    title: str | None
    publisher: str | None
    publication_date: str | None
    text: str
    retrieved_at: datetime
    origin_cluster_id: str

    def __post_init__(self) -> None:
        for url in (self.source_url, self.canonical_url):
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("controlled document URL must use http or https")
        if not self.text.strip() or not self.origin_cluster_id:
            raise ValueError("controlled document text and origin are required")

    @property
    def document_hash(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RetrievalHit:
    document: SourceDocument
    passage: str
    passage_location: str
    score: float
    provider: str = "controlled"


class EvidenceProvider(Protocol):
    def retrieve(self, query: str, *, limit: int = 5) -> tuple[RetrievalHit, ...]: ...


class ControlledEvidenceProvider:
    """In-memory allowlisted corpus. This class performs no network or filesystem I/O."""

    def __init__(
        self,
        documents: tuple[SourceDocument, ...] | list[SourceDocument],
        *,
        max_documents: int = 20,
        max_passages_per_document: int = 8,
        provider_name: str = "controlled",
    ) -> None:
        if max_documents < 1 or max_passages_per_document < 1:
            raise ValueError("retrieval bounds must be positive")
        if not provider_name.strip():
            raise ValueError("provider_name is required")
        self._documents = tuple(documents[:max_documents])
        self.max_documents = max_documents
        self.max_passages_per_document = max_passages_per_document
        self.provider_name = provider_name.strip()

    def retrieve(self, query: str, *, limit: int = 5) -> tuple[RetrievalHit, ...]:
        if limit < 1:
            return ()
        candidates: list[PassageCandidate] = []
        for doc_index, document in enumerate(self._documents):
            for passage_index, passage in enumerate(split_passages(document.text, self.max_passages_per_document)):
                candidates.append(PassageCandidate(doc_index, passage_index, passage))
        ranked = rank_passages(query, candidates, limit=min(limit, self.max_documents * self.max_passages_per_document))
        return tuple(
            RetrievalHit(
                document=self._documents[item.document_index],
                passage=item.text,
                passage_location=f"passage:{item.passage_index + 1}",
                score=score,
                provider=self.provider_name,
            )
            for item, score in ranked
            if score > 0.0
        )


class FallbackEvidenceProvider:
    """Try providers in order and fail closed if every provider is unavailable or empty."""

    def __init__(self, providers: tuple[EvidenceProvider, ...] | list[EvidenceProvider]) -> None:
        self.providers = tuple(providers)
        if not self.providers:
            raise ValueError("at least one evidence provider is required")

    def retrieve(self, query: str, *, limit: int = 5) -> tuple[RetrievalHit, ...]:
        for provider in self.providers:
            try:
                hits = provider.retrieve(query, limit=limit)
            except Exception:
                # Evidence acquisition must never turn a transient network/provider
                # failure into invented evidence. The next bounded provider may
                # still satisfy the request; otherwise the bundle stays insufficient.
                continue
            if hits:
                return hits
        return ()
