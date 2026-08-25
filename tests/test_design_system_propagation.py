from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
INDEX = (WEB / "index.html").read_text(encoding="utf-8")
LAB = (WEB / "lab.html").read_text(encoding="utf-8")
SYSTEM = (WEB / "design-system.css").read_text(encoding="utf-8")
APP = (WEB / "app.js").read_text(encoding="utf-8")
MAIN = (WEB / "main.js").read_text(encoding="utf-8")
LAB_JS = (WEB / "lab.js").read_text(encoding="utf-8")
LOCAL_SERVER = (ROOT / "scripts" / "serve_local.py").read_text(encoding="utf-8")


def test_shared_design_system_is_loaded_by_every_real_route():
    assert "/design-system.css?v=drsk-system-1" in INDEX
    assert "/design-system.css?v=drsk-system-1" in LAB
    assert "--color-bg-canvas: #000" in SYSTEM
    assert "--color-sourcechain-accent" in SYSTEM
    assert "--color-niyet-accent" in SYSTEM


def test_csp_safe_ui_does_not_depend_on_inline_styles():
    for path in WEB.glob("*"):
        if path.suffix in {".html", ".js"}:
            source = path.read_text(encoding="utf-8")
            assert "style=" not in source
            assert "createElement('style')" not in source
            assert 'createElement("style")' not in source


def test_shared_shell_preserves_product_evidence_and_lab_navigation():
    for label in ("Feed", "Evidence", "Lab"):
        assert label in INDEX
        assert label in LAB
    assert 'href="/#product"' in LAB
    assert 'href="/?open=evidence"' in LAB
    assert "window.location.search" in MAIN
    assert "query.get('open') === 'evidence'" in MAIN
    assert "window.__drskAppReady" in MAIN
    assert "drsk-app-ready" in MAIN
    assert "window.__drskAppReady = true" in APP
    assert "new CustomEvent('drsk-app-ready')" in APP


def test_technical_dialog_has_keyboard_and_focus_contracts():
    assert 'aria-hidden="true"' in INDEX
    assert "function openExplainSheet" in APP
    assert "function closeExplainSheet" in APP
    assert "sheetReturnFocus" in APP
    assert "event.key === 'Tab'" in APP
    assert "event.key === 'Escape'" in APP


def test_lab_supports_english_turkish_and_escaped_dynamic_content():
    assert "const LAB_COPY" in LAB_JS
    assert "en:" in LAB_JS
    assert "tr:" in LAB_JS
    assert "drsk-language" in LAB_JS
    assert "escapeHtml" in LAB_JS
    assert 'data-lab-lang="en"' in LAB
    assert 'data-lab-lang="tr"' in LAB
    assert 'data-lab-aria="comparison"' in LAB


def test_local_qa_server_exposes_the_same_lab_routes_as_deployment():
    assert 'route == "/lab"' in LOCAL_SERVER
    assert 'route == "/api/experiment"' in LOCAL_SERVER
    assert "ExperimentHandler.do_GET(self)" in LOCAL_SERVER


def test_system_covers_operational_surfaces_and_responsive_states():
    for selector in (
        ".app-shell",
        ".evidence-card",
        ".distortion-lens",
        ".evidence-lineage",
        ".right-rail",
        ".explain-sheet",
        ".lab-shell",
        ".mobile-inbox-fab",
    ):
        assert selector in SYSTEM
    assert "@media (max-width: 1024px)" in SYSTEM
    assert "@media (max-width: 760px)" in SYSTEM
    assert "@media (prefers-reduced-motion: reduce)" in SYSTEM
