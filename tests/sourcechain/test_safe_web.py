from __future__ import annotations

import gzip
import io
import socket
from unittest.mock import MagicMock, patch

import pytest
from sourcechain.safe_web import (
    ContentTooLargeError,
    DecompressionBombError,
    InvalidContentTypeError,
    InvalidUrlError,
    RedirectLoopError,
    SafeUrlFetcher,
    SafeWebEvidenceProvider,
    SSRFProtectionError,
    TooManyRedirectsError,
    is_ip_allowed,
    validate_ip_address,
)


def test_ip_validator_blocks_loopback_and_special_addresses():
    assert not is_ip_allowed("127.0.0.1")
    assert not is_ip_allowed("127.0.0.2")
    assert not is_ip_allowed("::1")
    assert not is_ip_allowed("0.0.0.0")
    assert not is_ip_allowed("::")


def test_ip_validator_blocks_private_rfc1918_addresses():
    assert not is_ip_allowed("10.0.0.1")
    assert not is_ip_allowed("10.254.254.254")
    assert not is_ip_allowed("172.16.0.1")
    assert not is_ip_allowed("172.31.255.255")
    assert not is_ip_allowed("192.168.1.1")
    assert not is_ip_allowed("192.168.0.254")
    assert not is_ip_allowed("fc00::1")
    assert not is_ip_allowed("fd12:3456:789a::1")


def test_ip_validator_blocks_link_local_and_cloud_metadata():
    assert not is_ip_allowed("169.254.169.254")  # AWS/GCP/Azure metadata
    assert not is_ip_allowed("169.254.169.253")  # AWS link-local DNS
    assert not is_ip_allowed("169.254.1.1")
    assert not is_ip_allowed("fe80::1")  # IPv6 link-local
    assert not is_ip_allowed("100.100.100.200")  # Alibaba Cloud metadata


def test_ip_validator_blocks_ipv4_mapped_ipv6_addresses():
    # IPv4-mapped IPv6 for loopback or private ranges
    assert not is_ip_allowed("::ffff:127.0.0.1")
    assert not is_ip_allowed("::ffff:10.0.0.1")
    assert not is_ip_allowed("::ffff:169.254.169.254")


def test_ip_validator_allows_public_ip_addresses():
    assert is_ip_allowed("8.8.8.8")
    assert is_ip_allowed("1.1.1.1")
    assert is_ip_allowed("93.184.216.34")  # example.com
    assert is_ip_allowed("2606:4700:4700::1111")


def test_validate_ip_address_raises_for_blocked_ips():
    with pytest.raises(SSRFProtectionError):
        validate_ip_address("127.0.0.1")
    with pytest.raises(SSRFProtectionError):
        validate_ip_address("169.254.169.254")


def test_validate_url_syntax_and_schemes():
    fetcher = SafeUrlFetcher()

    with pytest.raises(InvalidUrlError):
        fetcher.validate_url("ftp://example.org/resource")

    with pytest.raises(InvalidUrlError):
        fetcher.validate_url("file:///etc/passwd")

    with pytest.raises(InvalidUrlError):
        fetcher.validate_url("gopher://example.org")

    with pytest.raises(InvalidUrlError):
        fetcher.validate_url("not a url")

    with pytest.raises(SSRFProtectionError):
        fetcher.validate_url("http://metadata.google.internal/computeMetadata/v1/")

    with pytest.raises(SSRFProtectionError):
        fetcher.validate_url("http://localhost:8080/admin")

    with pytest.raises(SSRFProtectionError):
        fetcher.validate_url("http://127.0.0.1:8000/secret")

    scheme, host, port, path = fetcher.validate_url("https://example.org:8443/test?q=1")
    assert scheme == "https"
    assert host == "example.org"
    assert port == 8443
    assert path == "/test?q=1"


def _make_mock_socket(response_bytes: bytes, peer_ip: str = "93.184.216.34"):
    """Create a mock socket that emits the specified HTTP response bytes."""
    mock_sock = MagicMock(spec=socket.socket)
    mock_sock.getpeername.return_value = (peer_ip, 80)
    buffer = io.BytesIO(response_bytes)

    def recv_into(b):
        chunk = buffer.read(len(b))
        n = len(chunk)
        b[:n] = chunk
        return n

    def recv(bufsize, flags=0):
        return buffer.read(bufsize)

    mock_sock.recv_into.side_effect = recv_into
    mock_sock.recv.side_effect = recv
    mock_sock.makefile.return_value = buffer
    return mock_sock


def test_fetch_succeeds_on_valid_html_page():
    html_body = (
        b"<!DOCTYPE html><html><head><title>Research Findings</title>"
        b'<link rel="canonical" href="https://example.org/canonical-study">'
        b"<script>alert(1);</script><style>body { color: red; }</style></head>"
        b"<body><h1>Main Headline</h1><p>Study proves regular walking improves cardiac health.</p></body></html>"
    )
    raw_response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n"
        b"Content-Length: " + str(len(html_body)).encode("ascii") + b"\r\n"
        b"Connection: close\r\n\r\n" + html_body
    )

    mock_sock = _make_mock_socket(raw_response)
    fetcher = SafeUrlFetcher(dns_resolver=lambda host, port: ["93.184.216.34"])

    with patch("socket.create_connection", return_value=mock_sock):
        result = fetcher.fetch("http://example.org/study")

    assert result.status_code == 200
    assert result.title == "Research Findings"
    assert result.canonical_url == "https://example.org/canonical-study"
    assert "alert(1)" not in result.text
    assert "color: red" not in result.text
    assert "Study proves regular walking improves cardiac health." in result.text
    assert result.sha256_hash


def test_fetch_blocks_dns_resolving_to_private_ip():
    fetcher = SafeUrlFetcher(dns_resolver=lambda host, port: ["10.0.0.5"])

    with pytest.raises(SSRFProtectionError):
        fetcher.fetch("http://intranet.company.internal/secret")


def test_fetch_blocks_dns_rebinding_at_socket_peer_verification():
    # DNS pre-check returns public IP, but socket peer reveals internal IP
    fetcher = SafeUrlFetcher(dns_resolver=lambda host, port: ["93.184.216.34"])
    rebound_sock = _make_mock_socket(b"HTTP/1.1 200 OK\r\n\r\n", peer_ip="127.0.0.1")

    with (
        patch("socket.create_connection", return_value=rebound_sock),
        pytest.raises(SSRFProtectionError),
    ):
        fetcher.fetch("http://attacker-controlled-rebinding.com/")


def test_fetch_follows_safe_redirects_and_revalidates_target():
    first_response = b"HTTP/1.1 301 Moved Permanently\r\nLocation: https://example.org/final-location\r\nContent-Length: 0\r\n\r\n"
    second_body = b"<html><head><title>Final Page</title></head><body><p>Final content</p></body></html>"
    second_response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/html\r\n"
        b"Content-Length: "
        + str(len(second_body)).encode("ascii")
        + b"\r\n\r\n"
        + second_body
    )

    sock1 = _make_mock_socket(first_response)
    sock2 = _make_mock_socket(second_response)

    fetcher = SafeUrlFetcher(dns_resolver=lambda host, port: ["93.184.216.34"])

    with (
        patch("socket.create_connection", side_effect=[sock1, sock2]),
        patch("ssl.create_default_context") as mock_ssl,
    ):
        mock_ssl.return_value.wrap_socket.side_effect = lambda s, server_hostname: s
        result = fetcher.fetch("http://example.org/initial")

    assert result.status_code == 200
    assert result.final_url == "https://example.org/final-location"
    assert "Final content" in result.text
    assert len(result.redirect_history) == 2


def test_fetch_blocks_redirect_to_internal_metadata_service():
    redirect_response = b"HTTP/1.1 302 Found\r\nLocation: http://169.254.169.254/latest/meta-data/\r\nContent-Length: 0\r\n\r\n"
    sock1 = _make_mock_socket(redirect_response)
    fetcher = SafeUrlFetcher(dns_resolver=lambda host, port: ["93.184.216.34"])

    with (
        patch("socket.create_connection", return_value=sock1),
        pytest.raises(SSRFProtectionError),
    ):
        fetcher.fetch("http://example.org/bad-redirect")


def test_fetch_detects_redirect_loops():
    loop_response = b"HTTP/1.1 302 Found\r\nLocation: http://example.org/loop\r\nContent-Length: 0\r\n\r\n"
    sock1 = _make_mock_socket(loop_response)
    fetcher = SafeUrlFetcher(dns_resolver=lambda host, port: ["93.184.216.34"])

    with (
        patch("socket.create_connection", return_value=sock1),
        pytest.raises(RedirectLoopError),
    ):
        fetcher.fetch("http://example.org/loop")


def test_fetch_enforces_maximum_redirect_limit():
    responses = [
        b"HTTP/1.1 302 Found\r\nLocation: http://example.org/step"
        + str(i + 1).encode("ascii")
        + b"\r\n\r\n"
        for i in range(4)
    ]
    socks = [_make_mock_socket(r) for r in responses]
    fetcher = SafeUrlFetcher(
        max_redirects=2, dns_resolver=lambda host, port: ["93.184.216.34"]
    )

    with (
        patch("socket.create_connection", side_effect=socks),
        pytest.raises(TooManyRedirectsError),
    ):
        fetcher.fetch("http://example.org/step0")


def test_fetch_rejects_unpermitted_content_type():
    response = b"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: 10\r\n\r\n0123456789"
    sock = _make_mock_socket(response)
    fetcher = SafeUrlFetcher(dns_resolver=lambda host, port: ["93.184.216.34"])

    with (
        patch("socket.create_connection", return_value=sock),
        pytest.raises(InvalidContentTypeError),
    ):
        fetcher.fetch("http://example.org/download.bin")


def test_fetch_enforces_content_length_and_streamed_size_limits():
    # 1. Content-Length header is too large
    oversized_header_resp = (
        b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: 5000000\r\n\r\n"
    )
    sock1 = _make_mock_socket(oversized_header_resp)
    fetcher = SafeUrlFetcher(
        max_bytes=1024, dns_resolver=lambda host, port: ["93.184.216.34"]
    )

    with (
        patch("socket.create_connection", return_value=sock1),
        pytest.raises(ContentTooLargeError),
    ):
        fetcher.fetch("http://example.org/huge")

    # 2. Body streams more than max_bytes without Content-Length
    streaming_body = b"A" * 2048
    stream_resp = (
        b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n" + streaming_body
    )
    sock2 = _make_mock_socket(stream_resp)

    with (
        patch("socket.create_connection", return_value=sock2),
        pytest.raises(ContentTooLargeError),
    ):
        fetcher.fetch("http://example.org/stream")


def test_fetch_decompresses_gzip_safely_and_guards_against_zip_bombs():
    # 1. Safe gzip decompression
    original_text = b"Gzip compressed test payload repeated content for testing."
    compressed = gzip.compress(original_text)
    gzip_resp = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/plain\r\n"
        b"Content-Encoding: gzip\r\n"
        b"Content-Length: "
        + str(len(compressed)).encode("ascii")
        + b"\r\n\r\n"
        + compressed
    )
    sock = _make_mock_socket(gzip_resp)
    fetcher = SafeUrlFetcher(dns_resolver=lambda host, port: ["93.184.216.34"])

    with patch("socket.create_connection", return_value=sock):
        result = fetcher.fetch("http://example.org/gzip-page")

    assert result.text == original_text.decode("utf-8")

    # 2. Decompression bomb exceeding max_decompressed_bytes
    bomb_payload = gzip.compress(b"0" * 50000)
    bomb_resp = (
        b"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Encoding: gzip\r\n\r\n"
        + bomb_payload
    )
    bomb_sock = _make_mock_socket(bomb_resp)
    small_bound_fetcher = SafeUrlFetcher(
        max_bytes=10000,
        max_decompressed_bytes=20000,
        dns_resolver=lambda host, port: ["93.184.216.34"],
    )

    with (
        patch("socket.create_connection", return_value=bomb_sock),
        pytest.raises(DecompressionBombError),
    ):
        small_bound_fetcher.fetch("http://example.org/bomb")


def test_safe_web_evidence_provider_retrieves_and_ranks_passages():
    html_page = (
        b"<!DOCTYPE html><html><head><title>Health Study</title></head>"
        b"<body><p>Drinking tea daily reduces vascular inflammation.</p>"
        b"<p>Observational analysis tracked five thousand participants over ten years.</p></body></html>"
    )
    resp = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/html\r\n"
        b"Content-Length: "
        + str(len(html_page)).encode("ascii")
        + b"\r\n\r\n"
        + html_page
    )
    mock_sock = _make_mock_socket(resp)
    fetcher = SafeUrlFetcher(dns_resolver=lambda host, port: ["93.184.216.34"])

    with patch("socket.create_connection", return_value=mock_sock):
        provider = SafeWebEvidenceProvider(
            candidate_urls=["http://example.org/tea-study"],
            fetcher=fetcher,
        )
        hits = provider.retrieve("tea reduces vascular inflammation", limit=3)

    assert len(hits) > 0
    top_hit = hits[0]
    assert top_hit.provider == "safe_web"
    assert top_hit.document.source_url == "http://example.org/tea-study"
    assert top_hit.document.title == "Health Study"
    assert top_hit.document.origin_cluster_id == "web:example.org"
    assert "tea daily reduces vascular inflammation" in top_hit.passage
    assert top_hit.score > 0.0
