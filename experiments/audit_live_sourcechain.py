from __future__ import annotations

import json
import os
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = os.getenv("DRSK_BASE_URL", "https://niyet-nsosyal.vercel.app").rstrip("/")
OUTPUT = Path(os.getenv("DRSK_AUDIT_OUTPUT", "live_sourcechain_audit.json"))

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


def post_json(payload: dict) -> tuple[int, dict, float]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{BASE_URL}/api",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "DRSK-Live-Audit/1.0",
        },
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=20.0) as response:  # noqa: S310 - fixed project URL
            status = int(response.status)
            value = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        status = int(exc.code)
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = {"raw": raw}
    except URLError as exc:
        return 0, {"error": type(exc.reason).__name__}, (time.perf_counter() - started) * 1000.0
    return status, value, (time.perf_counter() - started) * 1000.0


def summarize(case_id: str, text: str) -> dict:
    status, payload, latency_ms = post_json({"action": "analyze", "text": text})
    bundle = payload.get("evidence_bundle", {}) if isinstance(payload, dict) else {}
    analysis = bundle.get("analysis", {}) if isinstance(bundle, dict) else {}
    evidence = bundle.get("evidence", []) if isinstance(bundle, dict) else []
    rows = []
    for item in evidence[:3] if isinstance(evidence, list) else []:
        metadata = item.get("metadata", {}) if isinstance(item, dict) else {}
        rows.append(
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
    return {
        "case": case_id,
        "text": text,
        "http_status": status,
        "latency_ms": round(latency_ms, 1),
        "statement_type": analysis.get("statement_type"),
        "check_worthy": analysis.get("check_worthy"),
        "bundle_status": bundle.get("status") if isinstance(bundle, dict) else None,
        "sufficient": bundle.get("sufficient") if isinstance(bundle, dict) else None,
        "resolution": payload.get("resolution") if isinstance(payload, dict) else None,
        "evidence": rows,
        "error": payload.get("error") if isinstance(payload, dict) else "invalid_response",
    }


def main() -> int:
    results = []
    for case_id, text in CASES.items():
        row = summarize(case_id, text)
        results.append(row)
        providers = [item.get("provider") for item in row["evidence"]]
        print(
            f"{case_id}: http={row['http_status']} latency_ms={row['latency_ms']} "
            f"type={row['statement_type']} status={row['bundle_status']} providers={providers}"
        )

    live_hits = sum(
        1
        for row in results
        if any(item.get("provider") == "tavily_search" for item in row["evidence"])
    )
    payload = {
        "base_url": BASE_URL,
        "case_count": len(results),
        "tavily_case_count": live_hits,
        "results": results,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUTPUT}")
    print(f"tavily_case_count={live_hits}/{len(results)}")

    if any(row["http_status"] != 200 for row in results):
        return 2
    if live_hits == 0:
        print("ERROR: no case exposed tavily_search provenance; live provider is not proven active")
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
