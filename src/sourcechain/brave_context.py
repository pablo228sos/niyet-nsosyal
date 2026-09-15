from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Callable
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from .retrieval import ControlledEvidenceProvider, RetrievalHit, SourceDocument


BRAVE_CONTEXT_URL = "https://api.search.brave.com/res/v1/llm/context"
Transport = Callable[[str, float], dict[str, Any]]


def _clean(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.split()).strip()
    return text or None


def _publication_date(metadata: dict[str, Any]) -> str | None:
    value = metadata.get("age")
    if isinstance(value, str):
        return value[:10] if len(value) >= 10 else value
    if isinstance(value, list):
        # Brave source metadata may expose multiple age representations. Prefer
        # the ISO-like value when present and otherwise leave the field unset.
        for item in reversed(value):
            if isinstance(item, str) and len(item) >= 10 and item[4:5] == "-":
                return item[:10]
    return None


class BraveContextEvidenceProvider:
    """Retrieve grounded web snippets from Brave's LLM Context endpoint.

    The API performs live search and page-content extraction. SOURCECHAIN still
    owns claim/passage alignment and typed distortion checks; Brave is only an
    evidence acquisition layer and never supplies a truth verdict.
    """

    def __init__(
        self,
        api_key: str,
        *,
        count: int = 8,
        token_budget: int = 3200,
        timeout: float = 8.0,
        transport: Transport | None = None,
    ) -> None:
        api_key = api_key.strip()
        if not api_key:
            raise ValueError("Brave API key is required")
        if not 1 <= count <= 20:
            raise ValueError("count must be between 1 and 20")
        if token_budget < 256:
            raise ValueError("token_budget is too small")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self._api_key = api_key
        self.count = count
        self.token_budget = token_budget
        self.timeout = timeout
        self._transport = transport or self._http_transport

    def _http_transport(self, query: str, timeout: float) -> dict[str, Any]:
        params = urlencode(
            {
                "q": query[:600],
                "count": self.count,
                "maximum_number_of_tokens": self.token_budget,
                "context_threshold_mode": "strict",
                "enable_source_metadata": "true",
                "safesearch": "strict",
            }
        )
        request = Request(
            f"{BRAVE_CONTEXT_URL}?{params}",
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": self._api_key,
                "User-Agent": "DRSK-SOURCECHAIN/1.0",
            },
            method="GET",
        )
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS endpoint
            raw = response.read(2_000_000)
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Brave response must be a JSON object")
        return value

    @staticmethod
    def _documents(payload: dict[str, Any]) -> tuple[SourceDocument, ...]:
        grounding = payload.get("grounding")
        generic = grounding.get("generic") if isinstance(grounding, dict) else None
        sources = payload.get("sources") if isinstance(payload.get("sources"), dict) else {}
        if not isinstance(generic, list):
            return ()

        now = datetime.now(UTC)
        documents: list[SourceDocument] = []
        seen_urls: set[str] = set()

        for item in generic:
            if not isinstance(item, dict):
                continue
            url = _clean(item.get("url"))
            title = _clean(item.get("title"))
            snippets = item.get("snippets")
            if not url or url in seen_urls or not isinstance(snippets, list):
                continue
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                continue

            clean_snippets = [_clean(value) for value in snippets]
            text = "\n".join(value for value in clean_snippets if value)
            if not text:
                continue

            metadata = sources.get(url) if isinstance(sources, dict) else None
            metadata = metadata if isinstance(metadata, dict) else {}
            publisher = _clean(metadata.get("site_name")) or _clean(metadata.get("hostname")) or parsed.hostname
            # Being conservative here: pages from one hostname count as the same
            # origin unless a future provider supplies explicit syndication lineage.
            origin_cluster_id = f"web:{(parsed.hostname or 'unknown').lower()}"

            documents.append(
                SourceDocument(
                    source_url=url,
                    canonical_url=url,
                    title=title,
                    publisher=publisher,
                    publication_date=_publication_date(metadata),
                    text=text,
                    retrieved_at=now,
                    origin_cluster_id=origin_cluster_id,
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
            max_documents=min(self.count, len(documents)),
            max_passages_per_document=8,
            provider_name="brave_llm_context",
        )
        return provider.retrieve(clean_query, limit=limit)
