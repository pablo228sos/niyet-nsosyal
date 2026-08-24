from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
STYLES = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")


def test_first_visit_uses_english_without_persisting_an_implicit_choice():
    assert "localStorage.getItem('drsk-language') || 'en'" in APP
    assert "applyLanguage(language, false)" in APP
    assert "function applyLanguage(nextLanguage, persist = true)" in APP


def test_ui_exposes_drsk_product_navigation_and_evidence_visuals():
    assert 'class="product-nav"' in INDEX
    assert 'class="product-wordmark"' in INDEX
    assert "distortion-lens" in APP
    assert "evidence-lineage" in APP


def test_ui_has_semantic_tokens_focus_and_reduced_motion_contracts():
    for token in (
        "--color-bg-canvas",
        "--color-sourcechain-accent",
        "--color-niyet-accent",
        "--color-drsk-accent",
    ):
        assert token in STYLES
    assert ":focus-visible" in STYLES
    assert "@media (prefers-reduced-motion: reduce)" in STYLES
