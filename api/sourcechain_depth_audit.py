from __future__ import annotations

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from sourcechain.evidence import build_evidence_bundle  # noqa: E402
from sourcechain.statement_classifier import analyze_post  # noqa: E402
from sourcechain.tavily_search import TavilyEvidenceProvider  # noqa: E402


CASES = {
    "eiffel_numeric": "The Eiffel Tower is 330 metres tall.",
    "microplastic_certainty_tr": (
        "Araştırmalar, mikroplastiklerin insanlarda kalp krizine kesin olarak "
        "yol açtığını kanıtladı."
    ),
    "fabricated_obscure_tr": (
        "Kırgızistan'ın Ak-Terek köyünde 2025 yılında dünyanın ilk hidrojenle "
        "çalışan okul otobüsü hizmete girdi."
    ),
    "python_reply_tr": (
        "Hayır, Python 3.13 GIL'i varsayılan olarak tamamen kaldırmadı; "
        "free-threaded build isteğe bağlıdır."
    ),
    "recent_turksat_tr": "Türksat 6A, 21 Nisan 2025 tarihinde hizmete alındı.",
}


def _run(text: str, api_key: str, search_depth: str) -> dict:
    provider = TavilyEvidenceProvider(api_key, search_depth=search_depth)
    usage: dict = {}
    transport = provider._http_transport

    def capture_usage(query: str, timeout: float) -> dict:
        payload = transport(query, timeout)
        raw_usage = payload.get("usage")
        if isinstance(raw_usage, dict):
            usage.update(raw_usage)
        return payload

    provider._transport = capture_usage
    started = time.perf_counter()
    bundle = build_evidence_bundle(analyze_post(text), provider)
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 1)
    result = bundle.to_dict()
    rows = []
    for item in result.get("evidence", [])[:3]:
        metadata = item.get("metadata", {}) if isinstance(item, dict) else {}
        rows.append(
            {
                "provider": metadata.get("provider"),
                "title": item.get("title"),
                "source_url": item.get("source_url"),
                "relation": item.get("relation"),
                "distortions": item.get("distortions", []),
                "lexical_score": metadata.get("lexical_score"),
                "passage": (item.get("passage") or "")[:700],
            }
        )
    return {
        "latency_ms": elapsed_ms,
        "usage": usage,
        "status": result.get("status"),
        "sufficient": result.get("sufficient"),
        "evidence": rows,
    }


class handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        params = parse_qs(urlparse(self.path).query)
        case_id = (params.get("case") or [""])[0]
        if not case_id:
            self._json(
                200,
                {
                    "status": "ok",
                    "purpose": "fixed Tavily basic-vs-advanced evidence audit",
                    "cases": sorted(CASES),
                    "arbitrary_input": False,
                },
            )
            return
        if case_id not in CASES:
            self._json(404, {"error": "unknown_case"})
            return

        api_key = os.getenv("TAVILY_API_KEY", "").strip()
        if not api_key:
            self._json(503, {"error": "tavily_not_configured"})
            return

        text = CASES[case_id]
        try:
            basic = _run(text, api_key, "basic")
            advanced = _run(text, api_key, "advanced")
        except Exception as exc:
            self._json(500, {"error": "audit_failed", "error_type": type(exc).__name__})
            return

        self._json(
            200,
            {
                "status": "ok",
                "case": case_id,
                "text": text,
                "basic": basic,
                "advanced": advanced,
            },
        )
