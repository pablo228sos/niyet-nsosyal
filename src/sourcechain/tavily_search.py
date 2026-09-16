from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .retrieval import ControlledEvidenceProvider, RetrievalHit, SourceDocument
from .text import tokens


TAVILY_SEARCH_URL = "https://api.tavily.com/search"
MIN_LIVE_LEXICAL_SCORE = 0.30
MIN_LIVE_TEXTUAL_ANCHORS = 2
MIN_LIVE_TEXTUAL_COVERAGE = 0.25
Transport = Callable[[str, float], dict[str, Any]]


def _clean(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.split()).strip()
    return text or None


def _textual_anchor_coverage(query: str, passage: str) -> tuple[int, float]:
    query_terms = {token for token in tokens(query, meaningful=True) if token.isalpha()}
    passage_terms = {token for token in tokens(passage, meaningful=True) if token.isalpha()}
    if not query_terms:
        return 0, 0.0
    shared = query_terms & passage_terms
    return len(shared), len(shared) / len(query_terms)


class TavilyEvidenceProvider:
    """Acquire live web passages through Tavily without delegating truth decisions.

    Tavily supplies candidate URLs and extracted text. SOURCECHAIN still owns
    passage ranking, claim/evidence relation labels, typed distortion checks and
    the decision to defer when evidence is insufficient.
    """

    def __init__(
        self,
        api_key: str,
        *,
        max_results: int = 8,
        timeout: float = 8.0,
        search_depth: str = "basic",
        transport: Transport | None = None,
    ) -> None:
        api_key = api_key.strip()
        if not api_key:
            raise ValueError("Tavily API key is required")
        if not 1 <= max_results <= 20:
            raise ValueError("max_results must be between 1 and 20")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if search_depth not in {"basic", "advanced"}:
            raise ValueError("search_depth must be 'basic' or 'advanced'")
        self._api_key = api_key
        self.max_results = max_results
        self.timeout = timeout
        self.search_depth = search_depth
        self._transport = transport or self._http_transport

    def _http_transport(self, query: str, timeout: float) -> dict[str, Any]:
        payload = json.dumps(
            {
                "query": query[:600],
                "search_depth": self.search_depth,
                "max_results": self.max_results,
                "topic": "general",
                "include_answer": False,
                "include_raw_content": False,
                "include_images": False,
                "include_usage": True,
                "safe_search": True,
            }
        ).encode("utf-8")
        request = Request(
            TAVILY_SEARCH_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "DRSK-SOURCECHAIN/1.0",
            },
            method="POST",
        )
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS endpoint
            raw = response.read(2_000_000)
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Tavily response must be a JSON object")
        return value

    @staticmethod
    def _documents(payload: dict[str, Any]) -> tuple[SourceDocument, ...]:
        results = payload.get("results")
        if not isinstance(results, list):
            return ()

        now = datetime.now(UTC)
        documents: list[SourceDocument] = []
        seen_urls: set[str] = set()

        for item in results:
            if not isinstance(item, dict):
                continue
            url = _clean(item.get("url"))
            title = _clean(item.get("title"))
            content = _clean(item.get("content"))
            if not url or not content or url in seen_urls:
                continue
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                continue
            hostname = (parsed.hostname or "unknown").lower()
            documents.append(
                SourceDocument(
                    source_url=url,
                    canonical_url=url,
                    title=title,
                    publisher=hostname,
                    publication_date=None,
                    text=content,
                    retrieved_at=now,
                    origin_cluster_id=f"web:{hostname}",
                )
            )
            seen_urls.add(url)

        return tuple(documents)

    def retrieve(self, query: str, *, limit: int = 5) -> tuple[RetrievalHit, ...]:
        clean_query = " ".join(query.split()).strip()
        if not clean_query or limit < 1:
            return ()
        payload = self._transport(clean_query, self.timeout)
        documents = self._documents(payload)
        if not documents:
            return ()
        provider = ControlledEvidenceProvider(
            documents,
            max_documents=min(self.max_results, len(documents)),
            max_passages_per_document=8,
            provider_name="tavily_search",
        )
        hits = provider.retrieve(clean_query, limit=limit)

        # Live search is broader than the verified local corpus. A numeric match
        # (for example only "37") must not turn an unrelated web page into
        # evidence. Until a semantic reranker is reproducibly validated, require
        # both a conservative lexical score and shared textual anchors.
        accepted: list[RetrievalHit] = []
        for hit in hits:
            anchor_count, anchor_coverage = _textual_anchor_coverage(clean_query, hit.passage)
            if (
                hit.score >= MIN_LIVE_LEXICAL_SCORE
                and anchor_count >= MIN_LIVE_TEXTUAL_ANCHORS
                and anchor_coverage >= MIN_LIVE_TEXTUAL_COVERAGE
            ):
                accepted.append(hit)
        return tuple(accepted)
