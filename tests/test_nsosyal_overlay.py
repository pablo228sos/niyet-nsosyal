import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
OVERLAY = ROOT / "demo" / "nsosyal-overlay"
MANIFEST = json.loads((OVERLAY / "manifest.json").read_text(encoding="utf-8"))
BACKGROUND = (OVERLAY / "background.js").read_text(encoding="utf-8")
CONTENT = (OVERLAY / "content-v2.js").read_text(encoding="utf-8")
CSS = (OVERLAY / "overlay.css").read_text(encoding="utf-8")
README = (OVERLAY / "README.md").read_text(encoding="utf-8")


def test_overlay_requests_only_the_hosts_it_needs():
    assert MANIFEST["manifest_version"] == 3
    assert MANIFEST.get("permissions", []) == []
    assert MANIFEST["host_permissions"] == ["https://niyet-nsosyal.vercel.app/*"]
    assert "action" not in MANIFEST

    script = MANIFEST["content_scripts"][0]
    assert script["matches"] == ["https://nsosyal.com/*", "https://www.nsosyal.com/*"]
    assert script["js"] == ["content-v2.js"]
    assert "css" not in script
    assert script["run_at"] == "document_idle"

    resources = MANIFEST["web_accessible_resources"]
    assert resources == [{
        "resources": ["overlay.css"],
        "matches": ["https://nsosyal.com/*", "https://www.nsosyal.com/*"],
    }]


def test_background_is_a_fixed_backend_proxy_not_an_arbitrary_fetch_bridge():
    assert "https://niyet-nsosyal.vercel.app/api/human_help" in BACKGROUND
    assert "https://niyet-nsosyal.vercel.app/api/human-help" in BACKGROUND
    assert "API_URLS" in BACKGROUND
    assert "ALLOWED_ACTIONS" in BACKGROUND
    assert "'resolve'" in BACKGROUND and "'status'" in BACKGROUND
    assert "message.url" not in BACKGROUND
    assert "credentials: 'omit'" in BACKGROUND
    assert "redirect: 'error'" in BACKGROUND
    assert "cache: 'no-store'" in BACKGROUND
    assert "trustedSender" in BACKGROUND
    assert "text.length > 1200" in BACKGROUND


def test_backend_errors_are_always_renderable_strings():
    assert "function errorText" in BACKGROUND
    assert "typeof value === 'object'" in BACKGROUND
    assert "JSON.stringify(value)" in BACKGROUND
    assert "data?.error ?? data?.message" in BACKGROUND


def test_overlay_is_css_isolated_and_does_not_mutate_nsosyal_actions():
    assert "attachShadow({ mode: 'closed' })" in CONTENT
    assert "chrome.runtime.getURL('overlay.css')" in CONTENT
    assert "panel.innerHTML" not in CONTENT
    assert "document.cookie" not in CONTENT
    assert ".click()" not in CONTENT
    assert "fetch(" not in CONTENT
    assert "requestAnimationFrame" in CONTENT
    assert "MutationObserver" in CONTENT
    assert ":host" in CSS


def test_live_composer_detection_handles_rich_text_editors_and_nsosyal_send_action():
    assert "[contenteditable]:not([contenteditable=\"false\"])" in CONTENT
    assert "[data-lexical-editor]" in CONTENT
    assert "[data-slate-editor]" in CONTENT
    assert ".ProseMirror" in CONTENT
    assert "'gönder'" in CONTENT
    assert "findSendButtonNear" in CONTENT
    assert "state.lastEditable" in CONTENT
    assert "document.addEventListener('focusin'" in CONTENT
    assert "document.addEventListener('input'" in CONTENT
    assert "editableText(node)" in CONTENT


def test_composer_helper_stays_compact_and_clear_of_native_toolbar():
    assert "trigger.style.setProperty('right', 'auto')" in CONTENT
    assert "trigger.style.setProperty('right', '24px')" in CONTENT
    assert "sendRect.left - 82" in CONTENT
    assert "trigger.dataset.fallback = 'false'" in CONTENT
    assert "trigger.dataset.fallback = 'true'" in CONTENT
    assert 'min-width:58px' in CSS
    assert 'height:32px' in CSS
    assert '.drsk-overlay-trigger[data-fallback="false"]{margin-top:-42px}' in CSS


def test_overlay_is_explicitly_a_concept_integration():
    assert "concept integration" in CONTENT.lower()
    assert "does not post to NSosyal or alter your account" in CONTENT
    assert "does **not** publish, edit, or delete NSosyal content" in README
    assert "standalone `/live` prototype remains the fallback" in README
