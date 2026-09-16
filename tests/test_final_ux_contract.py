import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
SCRIPT = (ROOT / "web" / "live.js").read_text(encoding="utf-8")
UX = (ROOT / "web" / "live-ux.css").read_text(encoding="utf-8")
MOTION_SCRIPT = (ROOT / "web" / "live-motion.js").read_text(encoding="utf-8")
MOTION_CSS = (ROOT / "web" / "live-motion.css").read_text(encoding="utf-8")
SHELL = (ROOT / "web" / "live-nsosyal.css").read_text(encoding="utf-8")
THEME = (ROOT / "web" / "live-theme.js").read_text(encoding="utf-8")


def test_final_surface_loads_the_product_design_layers():
    assert 'href="/live-published.css"' in HTML
    assert 'href="/live-ux.css"' in HTML
    assert 'href="/live-motion.css"' in HTML
    assert 'href="/live-nsosyal.css"' in HTML
    assert 'src="/live-motion.js"' in HTML
    assert 'src="/live-theme.js"' in HTML
    assert "DRSK × NSosyal — Resolution Layer" in HTML
    assert "DRSK integration" in HTML


def test_published_nsosyal_context_returns_with_the_request():
    assert "buildPublishedContext" in SCRIPT
    assert "request.social_context" in SCRIPT
    assert "publishedContext" in SCRIPT


def test_host_shell_is_context_not_a_fake_social_network():
    # Current NSosyal context is present, but non-demo destinations are inert shell
    # labels rather than dead links/buttons pretending to be implemented features.
    assert "Notifications" in HTML
    assert "Messages" in HTML
    assert "Discover" in HTML
    assert "Communities" in HTML
    assert HTML.count('class="nav-item shell-only"') >= 7
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

    # Mobile must not reserve a whole empty viewport before the resolution rail.
    assert "@media (max-width: 640px)" in MOTION_CSS
    assert ".feed-column" in MOTION_CSS
    assert "min-height: 0" in MOTION_CSS
    assert "@media (max-width: 640px)" in SHELL
    assert ".feed-column" in SHELL


def test_nsosyal_shell_supports_light_dark_without_ai_spectacle():
    assert "--ns-accent-a: #11c9de" in SHELL.lower()
    assert "--ns-accent-b: #3658ff" in SHELL.lower()
    assert 'html[data-theme="dark"]' in SHELL
    assert ".rail-logo" in SHELL
    assert ".trends-card" in SHELL
    assert ".drsk-composer-chip" in SHELL
    assert "gradient" in SHELL
    assert "glassmorphism" not in SHELL.lower()
    assert "ai orb" not in SHELL.lower()

    assert "drsk-live-theme" in THEME
    assert "prefers-color-scheme: dark" in THEME
    assert "data-theme-toggle" in HTML
    assert "metaTheme.content" in THEME


def test_hidden_state_cannot_be_overridden_by_component_display_rules():
    # Regression: .answer-block { display:grid } once overrode the browser's
    # [hidden] rule, exposing an empty Resolved card while the request was OPEN.
    assert "[hidden] { display: none !important; }" in SHELL
    assert 'id="answerBlock" class="answer-block" hidden' in HTML
    assert 'id="requestCard" class="post-card" hidden' in HTML
    assert 'id="evidenceBlock" class="drsk-card evidence-card" hidden' in HTML
    assert 'id="matchBlock" class="drsk-card niyet-card" hidden' in HTML


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
