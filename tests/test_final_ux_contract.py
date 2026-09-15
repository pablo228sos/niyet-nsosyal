import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "web" / "live.js").read_text(encoding="utf-8")
UX = (ROOT / "web" / "live-ux.css").read_text(encoding="utf-8")


def test_final_surface_loads_the_ux_hardening_layer():
    assert 'href="/live-ux.css"' in HTML


def test_final_surface_hides_controls_that_have_no_product_action():
    assert ".main-nav button.nav-item" in UX
    assert ".social-actions" in UX
    assert "display: none" in UX


def test_touch_focus_and_small_screen_layout_contracts_are_explicit():
    assert "min-height: 44px" in UX
    assert ":focus-visible" in UX
    assert "overflow-wrap: anywhere" in UX
    assert "@media (max-width: 640px)" in UX
    assert "@media (max-width: 480px)" in UX
    assert ".limit-card" in UX and "display: block" in UX
    assert ".responder-controls select" in UX and "min-width: 0" in UX


def test_final_surface_does_not_depend_on_inline_css_blocked_by_csp():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    csp = next(
        header["value"]
        for rule in config["headers"]
        for header in rule["headers"]
        if header["key"] == "Content-Security-Policy"
    )

    assert "<style" not in HTML.lower()
    assert "style-src 'self'" in csp
    assert "'unsafe-inline'" not in csp
    assert ".wording-compare" in UX


def test_distortion_explanation_uses_real_claim_and_passage_not_hardcoded_words():
    assert "item.claim_text" in SCRIPT
    assert "item.passage" in SCRIPT
    assert "claimWording: 'Post claim'" in SCRIPT
    assert "sourceWording: 'Source passage'" in SCRIPT
    assert "claimText.textContent = item.claim_text" in SCRIPT
    assert "sourceText.textContent = item.passage" in SCRIPT
    assert "causalityShift" not in SCRIPT
    assert "association:" not in SCRIPT


def test_responder_evidence_keeps_context_and_can_open_the_source():
    # Regression: buildInboxEvidence used to append a title and immediately lose
    # it when renderEvidence() called replaceChildren() on the same wrapper.
    assert "wrap.append(title, items)" in SCRIPT
    assert "renderEvidence(context, items)" in SCRIPT

    # The source link used to be author-only. The current renderer creates it
    # whenever a validated HTTP(S) provenance URL exists.
    assert "if (href)" in SCRIPT
    assert "if (href && target.id === 'evidenceItems')" not in SCRIPT
    assert ".inbox-evidence-item a" in UX
