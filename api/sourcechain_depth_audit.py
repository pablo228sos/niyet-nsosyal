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
    "en_supported": "Regular physical activity is associated with a lower risk of cardiovascular disease.",
    "en_causality": "Research proves that drinking coffee causes people to live longer.",
    "tr_supported": "Düzenli fiziksel aktivite daha düşük kalp hastalığı riski ile ilişkilidir.",
    "tr_causality": "Araştırmalar kahve içmenin insanların daha uzun yaşamasına neden olduğunu kanıtlıyor.",
    "tr_certainty": "Yeni tedavi bütün hastalarda kesin iyileşme sağlıyor.",
    "conflicting": "Eating eggs definitely increases cardiovascular mortality in everyone.",
    "obscure": "The 2026 Karakol municipal sensor pilot reduced winter PM2.5 by exactly 37 percent.",
    "subjective": "I think dark mode looks much better than light mode.",
}


def _run(text: str, api_key: str, search_depth: str) -> dict:
    provider = TavilyEvidenceProvider(api_key, search_depth=search_depth)
    analysis = analyze_post(text)
    started = time.perf_counter()
    bundle = build_evidence_bundle(analysis, provider)
    elapsed_ms = round((time.perf_counter() - started) * 1000.0, 1)
    result = bundle.to_dict()
    rows = []
    for item in result.get("evidence", [])[:3]:
        metadata = item.get("metadata", {}) if isinstance(item, dict) else {}
        passage = item.get("passage") or ""
        rows.append(
            {
                "provider": metadata.get("provider"),
                "title": item.get("title"),
                "source_url": item.get("source_url"),
                "relation": item.get("relation"),
                "distortions": item.get("distortions", []),
                "lexical_score": metadata.get("lexical_score"),
                "passage_chars": len(passage),
                "passage": passage[:700],
            }
        )
    return {
        "latency_ms": elapsed_ms,
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
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
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
