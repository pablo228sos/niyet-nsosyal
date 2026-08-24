from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
STYLES = (ROOT / "web" / "styles.css").read_text(encoding="utf-8")
MAIN = ROOT / "web" / "main.js"
VERCEL = (ROOT / "vercel.json").read_text(encoding="utf-8")


def test_full_bleed_video_landing_shell_is_present():
    assert "<title>Intelligence Designed To Evolve</title>" in INDEX
    assert 'class="landing-page"' in INDEX
    assert 'class="bg-video"' in INDEX
    assert "hf_20260809_012548_ef22562c-c0ae-4816-ad9d-f8922af4e6a7.mp4" in INDEX
    assert 'class="landing-headline"' in INDEX
    assert 'class="landing-stats"' in INDEX


def test_existing_drsk_product_is_preserved_as_an_accessible_experience():
    assert 'id="productExperience"' in INDEX
    assert 'class="app-shell"' in INDEX
    assert 'id="composerText"' in INDEX
    assert 'id="evidenceCard"' in INDEX
    assert 'id="matchState"' in INDEX


def test_landing_interactions_and_motion_contracts_exist():
    assert MAIN.exists()
    source = MAIN.read_text(encoding="utf-8")
    assert "IntersectionObserver" in source
    assert "openExperience" in source
    assert "prefers-reduced-motion" in source
    assert "aria-expanded" in source
    assert "overflow: hidden" in STYLES
    assert ".bg-video" in STYLES
    assert "@media (prefers-reduced-motion: reduce)" in STYLES


def test_deployment_policy_allows_the_declared_video_and_font_sources():
    assert "media-src 'self' https://d8j0ntlcm91z4.cloudfront.net" in VERCEL
    assert "https://fonts.googleapis.com" in VERCEL
    assert "https://db.onlinewebfonts.com" in VERCEL
