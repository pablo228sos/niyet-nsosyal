import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
BUILD = (ROOT / "scripts" / "build_site.py").read_text(encoding="utf-8")
WORKER = (ROOT / "scripts" / "site_worker.mjs").read_text(encoding="utf-8")
VERCEL = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))


def test_sites_bundle_contains_final_surface_assets():
    for asset in (
        "live.html",
        "live.css",
        "live-ux.css",
        "live-motion.css",
        "live.js",
        "live-motion.js",
    ):
        assert f'"{asset}"' in BUILD

    assert '"live.js", "live-motion.js"' in BUILD


def test_sites_root_and_live_route_to_final_surface():
    assert "url.pathname === '/'" in WORKER
    assert "['/live', '/live/'].includes(url.pathname)" in WORKER
    assert "? '/live.html'" in WORKER


def test_vercel_root_redirects_before_static_index_resolution():
    redirects = VERCEL.get("redirects", [])
    assert redirects == [
        {"source": "/", "destination": "/live", "permanent": False}
    ]
    assert "rewrites" not in VERCEL


def test_sites_proxy_includes_shared_human_help_api():
    assert "'/api/human-help'" in WORKER
    assert "API_PATHS.has(url.pathname)" in WORKER
    assert "experiment ? request.method === 'GET'" in WORKER
    assert "['GET', 'POST'].includes(request.method)" in WORKER


def test_sites_proxy_keeps_request_and_redirect_guards():
    assert "Request too large" in WORKER
    assert "backend_redirect" in WORKER
    assert "backend_unavailable" in WORKER
    assert "redirect: 'manual'" in WORKER
    assert "Cache-Control': 'no-store'" in WORKER
