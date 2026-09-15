import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "web" / "live.js").read_text(encoding="utf-8")
UX = (ROOT / "web" / "live-ux.css").read_text(encoding="utf-8")
MOTION_SCRIPT = (ROOT / "web" / "live-motion.js").read_text(encoding="utf-8")
MOTION_CSS = (ROOT / "web" / "live-motion.css").read_text(encoding="utf-8")


def test_final_surface_loads_the_product_design_layer():
    assert 'href="/live-ux.css"' in HTML
    assert 'href="/live-motion.css"' in HTML
    assert 'src="/live-motion.js"' in HTML
    assert "DRSK × NSosyal — Resolution Layer" in HTML
    assert "DRSK integration" in HTML


def test_final_surface_contains_only_real_product_controls():
    # The final surface should not imitate a full social network with dead controls.
    assert "Discover" not in HTML
    assert "Communities" not in HTML
    assert "Messages" not in HTML
    assert "Profile</b>" not in HTML
    assert 'class="social-actions"' not in HTML

    # Pitch-only proof metrics belong in the presentation, not in the product UI.
    assert 'class="context-card proof-card"' not in HTML
    assert "followers required" not in HTML
    assert "evidence + human layers" not in HTML
    assert "shared outcome" not in HTML


def test_touch_focus_and_small_screen_layout_contracts_are_explicit():
    assert "min-height: 44px" in UX
    assert ":focus-visible" in UX
    assert "overflow-wrap: anywhere" in UX
    assert "@media (max-width: 640px)" in UX
    assert "@media (max-width: 480px)" in UX
    assert ".responder-controls select" in UX and "min-width: 0" in UX
    assert "prefers-reduced-motion" in UX


def test_visual_system_is_restrained_and_semantic():
    assert "--canvas: #f6f8fb" in UX.lower()
    assert "--blue: #155eef" in UX.lower()
    assert "--violet: #6941c6" in UX.lower()
    assert ".evidence-card" not in UX or ".drsk-card::before" in UX
    assert ".niyet-card::before" in UX
    assert ".answer-block" in UX
    assert "surface-in" in UX


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

    # The source link must remain available on both author and responder sides.
    assert "if (href)" in SCRIPT
    assert "if (href && target.id === 'evidenceItems')" not in SCRIPT
    assert ".inbox-evidence-item a" in UX


def test_async_actions_expose_plain_language_progress_and_busy_semantics():
    assert "Checking available evidence…" in MOTION_SCRIPT
    assert "Finding someone who can help…" in MOTION_SCRIPT
    assert "Sending answer…" in MOTION_SCRIPT
    assert "Mevcut kanıt kontrol ediliyor…" in MOTION_SCRIPT
    assert "aria-busy" in MOTION_SCRIPT
    assert "MutationObserver" in MOTION_SCRIPT
    assert "accept-request" in MOTION_SCRIPT
    assert "skip-request" in MOTION_SCRIPT
    assert "send-answer" in MOTION_SCRIPT


def test_product_state_motion_is_restrained_and_accessible():
    assert "drsk-state-in" in MOTION_CSS
    assert "drsk-progress" in MOTION_CSS
    assert "button[aria-busy=\"true\"]" in MOTION_CSS
    assert "prefers-reduced-motion: reduce" in MOTION_CSS
    assert "animation: none !important" in MOTION_CSS
    assert "AI" not in MOTION_CSS
