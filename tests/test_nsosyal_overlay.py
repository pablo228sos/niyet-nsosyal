import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
OVERLAY = ROOT / "demo" / "nsosyal-overlay"
MANIFEST = json.loads((OVERLAY / "manifest.json").read_text(encoding="utf-8"))
BACKGROUND = (OVERLAY / "background.js").read_text(encoding="utf-8")
CONTENT = (OVERLAY / "content.js").read_text(encoding="utf-8")
CSS = (OVERLAY / "overlay.css").read_text(encoding="utf-8")
README = (OVERLAY / "README.md").read_text(encoding="utf-8")


def test_overlay_requests_only_the_hosts_it_needs():
    assert MANIFEST["manifest_version"] == 3
    assert MANIFEST.get("permissions", []) == []
    assert MANIFEST["host_permissions"] == ["https://niyet-nsosyal.vercel.app/*"]

    script = MANIFEST["content_scripts"][0]
    assert script["matches"] == ["https://nsosyal.com/*", "https://www.nsosyal.com/*"]
    assert script["js"] == ["content.js"]
    assert "css" not in script
    assert script["run_at"] == "document_idle"

    resources = MANIFEST["web_accessible_resources"]
    assert resources == [{
        "resources": ["overlay.css"],
        "matches": ["https://nsosyal.com/*", "https://www.nsosyal.com/*"],
    }]


def test_background_is_a_fixed_backend_proxy_not_an_arbitrary_fetch_bridge():
    assert "https://niyet-nsosyal.vercel.app/api/human-help" in BACKGROUND
    assert "ALLOWED_ACTIONS" in BACKGROUND
    assert "'resolve'" in BACKGROUND and "'status'" in BACKGROUND
    assert "message.url" not in BACKGROUND
    assert "credentials: 'omit'" in BACKGROUND
    assert "redirect: 'error'" in BACKGROUND
    assert "cache: 'no-store'" in BACKGROUND
    assert "trustedSender" in BACKGROUND
    assert "text.length > 1200" in BACKGROUND


def test_overlay_is_css_isolated_and_does_not_mutate_nsosyal_actions():
    assert "attachShadow({ mode: 'closed' })" in CONTENT
    assert "chrome.runtime.getURL('overlay.css')" in CONTENT
    assert "panel.innerHTML" not in CONTENT
    assert "document.cookie" not in CONTENT
    assert ".click()" not in CONTENT
    assert "fetch(" not in CONTENT
    assert "score < 6" in CONTENT
    assert "requestAnimationFrame" in CONTENT
    assert "MutationObserver" in CONTENT
    assert ":host" in CSS


def test_overlay_is_explicitly_a_concept_integration():
    assert "concept integration" in CONTENT.lower()
    assert "does not post to NSosyal or alter your account" in CONTENT
    assert "does **not** publish, edit, or delete NSosyal content" in README
    assert "standalone `/live` prototype remains the fallback" in README
