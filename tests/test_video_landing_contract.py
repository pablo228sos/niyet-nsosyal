from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
STYLES = (ROOT / "web" / "design-system.css").read_text(encoding="utf-8")
MAIN = ROOT / "web" / "main.js"
VERCEL = (ROOT / "vercel.json").read_text(encoding="utf-8")


def test_product_is_available_without_a_video_or_modal_gate():
    assert "<title>NIYET · Evidence, context & human help</title>" in INDEX
    assert '<video' not in INDEX
    assert 'id="productExperience" aria-label="NIYET workspace"' in INDEX
    assert 'id="composerText" name="post" maxlength="1200"' in INDEX
    assert 'id="composerError"' in INDEX


def test_existing_drsk_product_is_preserved_as_an_accessible_experience():
    assert 'id="productExperience"' in INDEX
    assert 'class="app-shell"' in INDEX
    assert 'id="composerText"' in INDEX
    assert 'id="evidenceCard"' in INDEX
    assert 'id="matchState"' in INDEX


def test_evidence_entry_and_reduced_motion_contracts_exist():
    assert MAIN.exists()
    source = MAIN.read_text(encoding="utf-8")
    assert "openEvidence" in source
    assert "query.get('open') === 'evidence'" in source
    assert "aria-expanded" in INDEX
    assert "@media (prefers-reduced-motion: reduce)" in STYLES


def test_product_does_not_load_external_decorative_dependencies():
    assert "fonts.googleapis.com" not in INDEX
    assert "db.onlinewebfonts.com" not in INDEX
    assert "cloudfront.net" not in INDEX
