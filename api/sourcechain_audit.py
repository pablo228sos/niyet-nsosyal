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

from sourcechain.pipeline import SourcechainPipeline  # noqa: E402


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


def _provider_chain(provider) -> list[str]:
    providers = getattr(provider, "providers", None)
    if providers is None:
        return [provider.__class__.__name__]
    return [item.__class__.__name__ for item in providers]


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
                    "purpose": "fixed SOURCECHAIN Tavily advanced A/B audit",
                    "cases": sorted(CASES),
                    "arbitrary_input": False,
                },
            )
            return
        if case_id not in CASES:
            self._json(404, {"error": "unknown_case"})
            return

        pipeline = SourcechainPipeline()
        started = time.perf_counter()
        try:
            bundle = pipeline.analyze(CASES[case_id])
        except Exception as exc:
            self._json(
                500,
                {
                    "status": "error",
                    "case": case_id,
                    "provider_chain": _provider_chain(pipeline.provider),
                    "error_type": type(exc).__name__,
                },
            )
            return

        elapsed_ms = round((time.perf_counter() - started) * 1000.0, 1)
        result = bundle.to_dict()
        evidence = result.get("evidence", [])
        provider_values = []
        for item in evidence:
            metadata = item.get("metadata", {}) if isinstance(item, dict) else {}
            provider_values.append(metadata.get("provider"))

        self._json(
            200,
            {
                "status": "ok",
                "case": case_id,
                "text": CASES[case_id],
                "provider_chain": _provider_chain(pipeline.provider),
                "evidence_providers": provider_values,
                "latency_ms": elapsed_ms,
                "bundle": result,
            },
        )
