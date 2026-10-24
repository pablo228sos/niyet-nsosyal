from __future__ import annotations

import hashlib
import html
import http.client
import ipaddress
import re
import socket
import ssl
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from .passage_ranker import PassageCandidate, rank_passages, split_passages
from .retrieval import RetrievalHit, SourceDocument

# Standard SSRF-blocked metadata addresses
BLOCKED_METADATA_IPS: frozenset[str] = frozenset(
    {
        "169.254.169.254",  # AWS, GCP, Azure, OpenStack metadata
        "169.254.169.253",  # AWS link-local DNS
        "169.254.169.123",  # AWS time sync
        "100.100.100.200",  # Alibaba Cloud metadata
    }
)

BLOCKED_HOSTNAMES: frozenset[str] = frozenset(
    {
        "localhost",
        "metadata.google.internal",
        "metadata",
        "instance-data",
    }
)

# RFC 6598 Shared Address Space / CGNAT (100.64.0.0/10)
CGNAT_NET = ipaddress.ip_network("100.64.0.0/10")
# RFC 2544 Benchmarking (198.18.0.0/15)
BENCHMARK_NET = ipaddress.ip_network("198.18.0.0/15")
# RFC 1122 'This host on this network' (0.0.0.0/8)
THIS_HOST_NET = ipaddress.ip_network("0.0.0.0/8")


class SafeWebError(Exception):
    """Base exception for safe web evidence retrieval errors."""


class SSRFProtectionError(SafeWebError):
    """Raised when an address resolves to a restricted or private destination."""


class InvalidUrlError(SafeWebError):
    """Raised when an input URL is malformed or uses an unsupported scheme."""


class TooManyRedirectsError(SafeWebError):
    """Raised when the maximum number of redirects is exceeded."""


class RedirectLoopError(SafeWebError):
    """Raised when a circular redirect is detected."""


class ContentTooLargeError(SafeWebError):
    """Raised when HTTP response body exceeds allowed size bounds."""


class InvalidContentTypeError(SafeWebError):
    """Raised when HTTP response MIME type is not permitted."""


class DecompressionBombError(SafeWebError):
    """Raised when decompressed content size exceeds safety thresholds."""


class FetchTimeoutError(SafeWebError):
    """Raised when socket or transport timeout is reached."""


def is_ip_allowed(ip_str: str) -> bool:
    """Validate whether an IP address is safe for outbound retrieval.

    Blocks loopback, private RFC 1918, link-local, multicast, cloud metadata,
    unspecified, carrier-grade NAT, and IPv4-mapped IPv6 variants of blocked IPs.
    """
    clean_ip = ip_str.strip().strip("[]")
    if clean_ip in BLOCKED_METADATA_IPS:
        return False

    try:
        ip = ipaddress.ip_address(clean_ip)
    except ValueError:
        return False

    # Unpack IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped

    if (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return False

    return not (
        isinstance(ip, ipaddress.IPv4Address)
        and (ip in CGNAT_NET or ip in BENCHMARK_NET or ip in THIS_HOST_NET)
    )


def validate_ip_address(ip_str: str) -> None:
    """Validate that the given IP is safe; raise SSRFProtectionError otherwise."""
    if not is_ip_allowed(ip_str):
        raise SSRFProtectionError(
            f"IP address '{ip_str}' is blocked by SSRF protection"
        )


def default_dns_resolver(hostname: str, port: int) -> list[str]:
    """Resolve hostname to a list of IP addresses using socket.getaddrinfo."""
    try:
        addrinfo = socket.getaddrinfo(
            hostname, port, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM
        )
    except socket.gaierror as exc:
        raise SSRFProtectionError(
            f"DNS resolution failed for '{hostname}': {exc}"
        ) from exc

    ips = list({info[4][0] for info in addrinfo})
    if not ips:
        raise SSRFProtectionError(f"No IP addresses resolved for '{hostname}'")
    return ips


class _SafeHTMLTextExtractor(HTMLParser):
    """Streaming HTML parser that extracts clean text, title and canonical URL.

    Strips script, style, head, noscript, svg, iframe, and other non-content tags.
    """

    SKIPPED_TAGS = frozenset(
        {
            "script",
            "style",
            "noscript",
            "svg",
            "canvas",
            "iframe",
            "object",
            "embed",
            "template",
        }
    )

    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._text_chunks: list[str] = []
        self._title_chunks: list[str] = []
        self._in_title = False
        self.canonical_url: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in self.SKIPPED_TAGS:
            self._skip_depth += 1
        elif tag_lower == "title" and self._skip_depth == 0:
            self._in_title = True
        elif tag_lower == "link":
            attr_dict = {k.lower(): v for k, v in attrs if v is not None}
            if attr_dict.get("rel", "").lower() == "canonical" and "href" in attr_dict:
                self.canonical_url = attr_dict["href"].strip()

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in self.SKIPPED_TAGS:
            if self._skip_depth > 0:
                self._skip_depth -= 1
        elif tag_lower == "title":
            self._in_title = False
        elif (
            tag_lower
            in {
                "p",
                "div",
                "br",
                "li",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "tr",
                "section",
                "article",
            }
            and self._skip_depth == 0
        ):
            self._text_chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        if self._in_title:
            self._title_chunks.append(data)
        else:
            self._text_chunks.append(data)

    def get_title(self) -> str | None:
        raw = "".join(self._title_chunks).strip()
        if not raw:
            return None
        return " ".join(html.unescape(raw).split())

    def get_cleaned_text(self) -> str:
        raw = "".join(self._text_chunks)
        unescaped = html.unescape(raw)
        # Normalize whitespace while preserving paragraphs
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in unescaped.split("\n")]
        return "\n".join(line for line in lines if line)


@dataclass(frozen=True)
class SafeFetchResult:
    """Immutable result of a safe web retrieval."""

    initial_url: str
    final_url: str
    status_code: int
    content_type: str
    raw_bytes: bytes
    text: str
    title: str | None
    canonical_url: str | None
    retrieved_at: datetime
    sha256_hash: str
    redirect_history: tuple[str, ...]


class SafeUrlFetcher:
    """Production-hardened HTTP(S) fetcher protecting against SSRF, redirects and resource exhaustion."""

    DEFAULT_ALLOWED_CONTENT_TYPES = frozenset(
        {
            "text/html",
            "text/plain",
            "text/xml",
            "application/xhtml+xml",
            "application/json",
            "application/xml",
        }
    )

    def __init__(
        self,
        *,
        max_bytes: int = 2 * 1024 * 1024,  # 2 MB limit
        max_decompressed_bytes: int = 10 * 1024 * 1024,  # 10 MB decompression bound
        max_redirects: int = 5,
        timeout: float = 8.0,
        allowed_schemes: tuple[str, ...] = ("http", "https"),
        allowed_content_types: frozenset[str] | None = None,
        dns_resolver: Callable[[str, int], list[str]] | None = None,
    ) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        if max_decompressed_bytes < max_bytes:
            raise ValueError("max_decompressed_bytes cannot be smaller than max_bytes")
        if max_redirects < 0:
            raise ValueError("max_redirects cannot be negative")
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        self.max_bytes = max_bytes
        self.max_decompressed_bytes = max_decompressed_bytes
        self.max_redirects = max_redirects
        self.timeout = timeout
        self.allowed_schemes = frozenset(allowed_schemes)
        self.allowed_content_types = (
            allowed_content_types or self.DEFAULT_ALLOWED_CONTENT_TYPES
        )
        self.dns_resolver = dns_resolver or default_dns_resolver

    def validate_url(self, url: str) -> tuple[str, str, int, str]:
        """Validate URL syntax, scheme and hostname before network activity."""
        if not url or not isinstance(url, str):
            raise InvalidUrlError("URL must be a non-empty string")

        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme not in self.allowed_schemes:
            raise InvalidUrlError(
                f"Scheme '{parsed.scheme}' is not allowed (must be {sorted(self.allowed_schemes)})"
            )

        hostname = parsed.hostname
        if not hostname:
            raise InvalidUrlError(f"URL '{url}' is missing a valid hostname")

        hostname_lower = hostname.lower().strip(".")
        if hostname_lower in BLOCKED_HOSTNAMES:
            raise SSRFProtectionError(
                f"Hostname '{hostname}' is blocked by SSRF protection"
            )

        # Check if hostname itself is a raw IP literal
        try:
            ip = ipaddress.ip_address(hostname_lower)
            validate_ip_address(str(ip))
        except ValueError:
            pass  # Standard domain name

        port = parsed.port or (443 if scheme == "https" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        return scheme, hostname_lower, port, path

    def _resolve_and_validate(self, hostname: str, port: int) -> list[str]:
        """Resolve DNS and verify that ALL returned IPs are safe from SSRF."""
        ips = self.dns_resolver(hostname, port)
        for ip in ips:
            validate_ip_address(ip)
        return ips

    def _safe_decompress(self, raw_bytes: bytes, encoding: str) -> bytes:
        """Decompress body with strict memory and decompression bomb bounds."""
        encoding = encoding.lower().strip()
        if not encoding or encoding == "identity":
            return raw_bytes

        if encoding in {"gzip", "x-gzip"}:
            try:
                # Decompress with bound check
                d = zlib.decompressobj(16 + zlib.MAX_WBITS)
                chunk_size = 64 * 1024
                decompressed = bytearray()
                offset = 0
                while offset < len(raw_bytes):
                    chunk = d.decompress(raw_bytes[offset : offset + chunk_size])
                    decompressed.extend(chunk)
                    if len(decompressed) > self.max_decompressed_bytes:
                        raise DecompressionBombError(
                            f"Decompressed content exceeds limit of {self.max_decompressed_bytes} bytes"
                        )
                    offset += chunk_size
                decompressed.extend(d.flush())
                if len(decompressed) > self.max_decompressed_bytes:
                    raise DecompressionBombError(
                        f"Decompressed content exceeds limit of {self.max_decompressed_bytes} bytes"
                    )
                return bytes(decompressed)
            except zlib.error as exc:
                raise SafeWebError(f"Gzip decompression error: {exc}") from exc

        if encoding == "deflate":
            try:
                d = zlib.decompressobj(-zlib.MAX_WBITS)
                try:
                    decompressed = d.decompress(raw_bytes) + d.flush()
                except zlib.error:
                    # Some servers emit standard zlib headers instead of raw deflate
                    decompressed = zlib.decompress(raw_bytes)
                if len(decompressed) > self.max_decompressed_bytes:
                    raise DecompressionBombError(
                        f"Decompressed content exceeds limit of {self.max_decompressed_bytes} bytes"
                    )
                return decompressed
            except zlib.error as exc:
                raise SafeWebError(f"Deflate decompression error: {exc}") from exc

        raise SafeWebError(f"Unsupported content-encoding: '{encoding}'")

    def fetch(self, url: str) -> SafeFetchResult:
        """Execute a safe, SSRF-guarded fetch following redirects up to the configured limit."""
        current_url = url
        redirect_history: list[str] = []

        while True:
            scheme, hostname, port, path = self.validate_url(current_url)
            redirect_history.append(current_url)

            # DNS check: resolve and validate all target IPs
            safe_ips = self._resolve_and_validate(hostname, port)
            target_ip = safe_ips[0]

            # Connect socket directly to target_ip to defeat DNS rebinding attacks
            sock = None
            try:
                sock = socket.create_connection((target_ip, port), timeout=self.timeout)

                # Re-verify peer address on the live socket
                peer_ip = sock.getpeername()[0]
                validate_ip_address(peer_ip)

                if scheme == "https":
                    context = ssl.create_default_context()
                    # Server hostname must match original domain for SNI and certificate verification
                    sock = context.wrap_socket(sock, server_hostname=hostname)

                conn = http.client.HTTPConnection(
                    hostname, port=port, timeout=self.timeout
                )
                conn.sock = sock

                headers = {
                    "Host": hostname if port in {80, 443} else f"{hostname}:{port}",
                    "User-Agent": "SafeWebRetriever/1.0 (SOURCECHAIN; +https://github.com/pablo228sos/niyet-nsosyal)",
                    "Accept": "text/html,text/plain,application/xhtml+xml,application/json;q=0.9,*/*;q=0.1",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "close",
                }

                conn.request("GET", path, headers=headers)
                response = conn.getresponse()

                status = response.status

                # Handle HTTP redirects (301, 302, 303, 307, 308)
                if status in {301, 302, 303, 307, 308}:
                    location = response.getheader("Location")
                    if not location:
                        raise SafeWebError(
                            f"Redirect status {status} missing Location header"
                        )

                    next_url = urljoin(current_url, location.strip())
                    if next_url in redirect_history:
                        raise RedirectLoopError(
                            f"Circular redirect detected: '{next_url}'"
                        )

                    if len(redirect_history) > self.max_redirects:
                        raise TooManyRedirectsError(
                            f"Exceeded maximum redirect limit of {self.max_redirects} for '{url}'"
                        )

                    current_url = next_url
                    continue

                if status < 200 or status >= 400:
                    raise SafeWebError(
                        f"HTTP request to '{current_url}' failed with status {status}"
                    )

                # Check Content-Type
                raw_content_type = response.getheader("Content-Type", "")
                mime_type = (
                    raw_content_type.split(";")[0].strip().lower() or "text/plain"
                )
                if mime_type not in self.allowed_content_types:
                    raise InvalidContentTypeError(
                        f"Content-Type '{raw_content_type}' ({mime_type}) is not allowed"
                    )

                # Check Content-Length header if provided
                raw_length = response.getheader("Content-Length")
                if (
                    raw_length
                    and raw_length.isdigit()
                    and int(raw_length) > self.max_bytes
                ):
                    raise ContentTooLargeError(
                        f"Content-Length {raw_length} exceeds limit of {self.max_bytes} bytes"
                    )

                # Stream read body with strict size bounds
                accumulated = bytearray()
                chunk_size = 8192
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    accumulated.extend(chunk)
                    if len(accumulated) > self.max_bytes:
                        raise ContentTooLargeError(
                            f"Response body exceeded maximum allowed limit of {self.max_bytes} bytes"
                        )

                raw_bytes = bytes(accumulated)
                content_encoding = response.getheader("Content-Encoding", "")
                decompressed_bytes = self._safe_decompress(raw_bytes, content_encoding)

                # Extract character encoding or default to UTF-8
                charset = "utf-8"
                if "charset=" in raw_content_type.lower():
                    try:
                        charset = (
                            raw_content_type.lower()
                            .split("charset=")[-1]
                            .split(";")[0]
                            .strip()
                        )
                    except (IndexError, ValueError):
                        charset = "utf-8"

                try:
                    text = decompressed_bytes.decode(charset, errors="replace")
                except (LookupError, UnicodeDecodeError):
                    text = decompressed_bytes.decode("utf-8", errors="replace")

                title = None
                canonical_url = None
                clean_text = text

                if mime_type in {"text/html", "application/xhtml+xml"}:
                    parser = _SafeHTMLTextExtractor()
                    parser.feed(text)
                    parser.close()
                    title = parser.get_title()
                    canonical_url = parser.canonical_url
                    clean_text = parser.get_cleaned_text()

                retrieved_at = datetime.now(UTC)
                sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

                return SafeFetchResult(
                    initial_url=url,
                    final_url=current_url,
                    status_code=status,
                    content_type=raw_content_type,
                    raw_bytes=raw_bytes,
                    text=clean_text,
                    title=title,
                    canonical_url=canonical_url,
                    retrieved_at=retrieved_at,
                    sha256_hash=sha256_hash,
                    redirect_history=tuple(redirect_history),
                )

            except socket.gaierror as exc:
                raise FetchTimeoutError(
                    f"Socket error or timeout for '{current_url}': {exc}"
                ) from exc
            except TimeoutError as exc:
                raise FetchTimeoutError(
                    f"Connection timed out for '{current_url}': {exc}"
                ) from exc
            finally:
                if sock is not None:
                    try:
                        sock.close()
                    except OSError:
                        pass


class SafeWebEvidenceProvider:
    """EvidenceProvider implementation that retrieves and ranks passages from safe live web sources.

    Complies with SOURCECHAIN deterministic alignment while providing live web retrieval.
    Guarantees SSRF defense, redirect bounds, extraction sanitization, and provenance hashing.
    """

    def __init__(
        self,
        candidate_urls: tuple[str, ...] | list[str] | None = None,
        *,
        fetcher: SafeUrlFetcher | None = None,
        max_passages_per_document: int = 8,
        provider_name: str = "safe_web",
        url_searcher: Callable[[str, int], list[str]] | None = None,
    ) -> None:
        self.candidate_urls = tuple(candidate_urls or ())
        self.fetcher = fetcher or SafeUrlFetcher()
        self.max_passages_per_document = max_passages_per_document
        self.provider_name = provider_name
        self.url_searcher = url_searcher
        self._document_cache: dict[str, SourceDocument] = {}

    def fetch_document(self, url: str) -> SourceDocument | None:
        """Safely fetch a URL and return a provenanced SourceDocument, or None on failure."""
        if url in self._document_cache:
            return self._document_cache[url]

        try:
            result = self.fetcher.fetch(url)
            parsed = urlparse(result.final_url)
            hostname = parsed.hostname or "unknown"

            doc = SourceDocument(
                source_url=result.final_url,
                canonical_url=result.canonical_url or result.final_url,
                title=result.title or hostname,
                publisher=hostname,
                publication_date=result.retrieved_at.strftime("%Y-%m-%d"),
                text=result.text,
                retrieved_at=result.retrieved_at,
                origin_cluster_id=f"web:{hostname}",
            )
            self._document_cache[url] = doc
            return doc
        except SafeWebError:
            return None

    def retrieve(self, query: str, *, limit: int = 5) -> tuple[RetrievalHit, ...]:
        """Fetch candidate documents safely, split and rank passages, and return RetrievalHit tuple."""
        if limit < 1:
            return ()

        target_urls = list(self.candidate_urls)
        if self.url_searcher is not None:
            try:
                discovered = self.url_searcher(query, limit)
                for u in discovered:
                    if u not in target_urls:
                        target_urls.append(u)
            except (SafeWebError, RuntimeError, ValueError):
                pass

        documents: list[SourceDocument] = []
        for url in target_urls:
            doc = self.fetch_document(url)
            if doc is not None and doc.text.strip():
                documents.append(doc)

        if not documents:
            return ()

        candidates: list[PassageCandidate] = []
        for doc_index, document in enumerate(documents):
            for passage_index, passage in enumerate(
                split_passages(document.text, self.max_passages_per_document)
            ):
                candidates.append(PassageCandidate(doc_index, passage_index, passage))

        ranked = rank_passages(query, candidates, limit=min(limit, len(candidates)))
        return tuple(
            RetrievalHit(
                document=documents[item.document_index],
                passage=item.text,
                passage_location=f"passage:{item.passage_index + 1}",
                score=score,
                provider=self.provider_name,
            )
            for item, score in ranked
            if score > 0.0
        )
