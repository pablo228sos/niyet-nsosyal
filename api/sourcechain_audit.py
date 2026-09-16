from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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


def _run_case(case_id: str) -> dict:
    pipeline = SourcechainPipeline()
    started = time.perf_counter()
    try:
        bundle = pipeline.analyze(CASES[case_id])
    except Exception as exc:
        return {
            "status": "error",
            "case": case_id,
            "text": CASES[case_id],
            "provider_chain": _provider_chain(pipeline.provider),
            "latency_ms": round((time.perf_counter() - started) * 1000.0, 1),
            "error_type": type(exc).__name__,
        }

    latency_ms = round((time.perf_counter() - started) * 1000.0, 1)
    result = bundle.to_dict()
    evidence_rows = []
    for item in result.get("evidence", [])[:3]:
        metadata = item.get("metadata", {}) if isinstance(item, dict) else {}
        evidence_rows.append(
            {
                "provider": metadata.get("provider"),
                "title": item.get("title"),
                "source_url": item.get("source_url"),
                "passage": item.get("passage"),
                "relation": item.get("relation"),
                "distortions": item.get("distortions", []),
                "lexical_score": metadata.get("lexical_score"),
            }
        )

    analysis = result.get("analysis", {})
    return {
        "status": "ok",
        "case": case_id,
        "text": CASES[case_id],
        "provider_chain": _provider_chain(pipeline.provider),
        "latency_ms": latency_ms,
        "statement_type": analysis.get("statement_type"),
        "check_worthy": analysis.get("check_worthy"),
        "bundle_status": result.get("status"),
        "sufficient": result.get("sufficient"),
        "evidence": evidence_rows,
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
                    "purpose": "fixed SOURCECHAIN live-evidence audit",
                    "cases": sorted(CASES),
                    "arbitrary_input": False,
                    "all_cases": "?case=all",
                },
            )
            return

        if case_id == "all":
            started = time.perf_counter()
            rows: dict[str, dict] = {}
            with ThreadPoolExecutor(max_workers=4) as pool:
                futures = {pool.submit(_run_case, key): key for key in CASES}
                for future in as_completed(futures):
                    key = futures[future]
                    try:
                        rows[key] = future.result()
                    except Exception as exc:
                        rows[key] = {
                            "status": "error",
                            "case": key,
                            "error_type": type(exc).__name__,
                        }
            self._json(
                200,
                {
                    "status": "ok",
                    "purpose": "fixed SOURCECHAIN live-evidence audit",
                    "total_latency_ms": round((time.perf_counter() - started) * 1000.0, 1),
                    "results": [rows[key] for key in CASES],
                },
            )
            return

        if case_id not in CASES:
            self._json(404, {"error": "unknown_case"})
            return

        row = _run_case(case_id)
        self._json(200 if row["status"] == "ok" else 500, row)
