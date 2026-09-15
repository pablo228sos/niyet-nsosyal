import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
EXT = ROOT / "demo" / "nsosyal-overlay"


def test_overlay_manifest_is_scoped_and_transparent():
    manifest = json.loads((EXT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["manifest_version"] == 3
    assert manifest["permissions"] == ["storage"]
    assert "https://nsosyal.com/*" in manifest["host_permissions"]
    assert "https://niyet-nsosyal.vercel.app/*" in manifest["host_permissions"]
    assert manifest["content_scripts"][0]["run_at"] == "document_idle"
    assert "tabs" not in manifest["permissions"]
    assert "cookies" not in manifest["permissions"]


def test_overlay_uses_real_drsk_backend_without_forwarding_account_credentials():
    background = (EXT / "background.js").read_text(encoding="utf-8")
    content = (EXT / "content.js").read_text(encoding="utf-8")

    assert "https://niyet-nsosyal.vercel.app/api/human-help" in background
    assert "credentials: 'omit'" in background
    assert "action: 'resolve'" in content
    assert "action: 'status'" in content
    assert "request_id" in content and "author_token" in content


def test_overlay_never_claims_to_be_an_official_nsosyal_build():
    content = (EXT / "content.js").read_text(encoding="utf-8")
    readme = (EXT / "README.md").read_text(encoding="utf-8")

    assert "DRSK concept integration" in content
    assert "does not post to NSosyal" in content
    assert "without pretending the prototype is an official NSosyal build" in readme


def test_overlay_has_safe_dom_fallback_and_mobile_surface():
    content = (EXT / "content.js").read_text(encoding="utf-8")
    css = (EXT / "overlay.css").read_text(encoding="utf-8")

    assert "findComposer" in content
    assert "data-fallback" in css
    assert "MutationObserver" in content
    assert "@media(max-width:700px)" in css.replace(" ", "")
    assert "prefers-reduced-motion" in css
