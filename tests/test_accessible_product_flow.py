from __future__ import annotations

from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
APP_JS = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
DESIGN_CSS = (ROOT / "web" / "design-system.css").read_text(encoding="utf-8")


def test_composer_accessibility_and_semantic_contracts():
    # Composer textarea must have explicit label and limits
    assert 'id="composerText"' in INDEX_HTML
    assert 'for="composerText"' in INDEX_HTML
    assert 'maxlength="1200"' in INDEX_HTML
    assert 'aria-describedby="composerHelp composerError"' in INDEX_HTML
    assert '<output id="characterCount">' in INDEX_HTML
    assert 'id="composerError" class="field-error" role="alert"' in INDEX_HTML


def test_response_needed_suggestion_and_intent_panel():
    # Intent suggestion panel must have polite live region and clear title
    assert 'id="intentPanel" aria-live="polite"' in INDEX_HTML
    assert 'data-i18n="intentTitle"' in INDEX_HTML
    assert 'data-i18n="intentSub"' in INDEX_HTML
    assert 'class="confidence"' in INDEX_HTML


def test_author_intent_confirmation_and_override_contracts():
    # All four canonical intent classes must have interactive toggle buttons
    for intent in ("ask", "feedback", "collaborate", "discuss"):
        button_tag = f'data-intent="{intent}"'
        assert button_tag in INDEX_HTML

    assert 'id="dismissIntent"' in INDEX_HTML
    assert 'id="routeIntent"' in INDEX_HTML

    # Check JS wires intent choice handling
    assert "intent-choice" in APP_JS
    assert "routeIntent" in APP_JS
    assert "dismissIntent" in APP_JS


def test_routed_request_card_and_match_reasons():
    # Match preview card must have structured type, status, and rationale
    assert 'id="matchState"' in INDEX_HTML
    assert 'id="matchType"' in INDEX_HTML
    assert 'id="matchStatus"' in INDEX_HTML
    assert 'id="matchPostText"' in INDEX_HTML
    assert 'id="matchReasons"' in INDEX_HTML
    assert 'id="explainMatch"' in INDEX_HTML


def test_responder_lifecycle_accept_skip_pause():
    # Accept, skip, and pause controls must exist and be accessible
    assert 'id="acceptMatch"' in INDEX_HTML
    assert 'id="skipMatch"' in INDEX_HTML
    assert 'id="routingSwitch"' in INDEX_HTML
    assert 'aria-label="Toggle NIYET routing"' in INDEX_HTML
    assert 'id="budgetCount"' in INDEX_HTML
    assert 'id="budgetFill"' in INDEX_HTML

    # Check JS handles responder actions
    assert "acceptMatch" in APP_JS
    assert "skipMatch" in APP_JS
    assert "routingSwitch" in APP_JS


def test_outcome_feedback_and_route_result():
    # Real-time feedback live region
    assert 'id="routeResult" aria-live="polite"' in INDEX_HTML
    assert "routeResult" in APP_JS


def test_wcag_keyboard_focus_touch_targets_and_reduced_motion():
    # Keyboard visible focus indicators
    assert ":focus-visible" in DESIGN_CSS
    assert "outline:" in DESIGN_CSS or "outline-color:" in DESIGN_CSS

    # Reduced motion media query
    assert "@media (prefers-reduced-motion: reduce)" in DESIGN_CSS

    # Semantic design tokens
    for token in ("--color-bg-canvas", "--color-sourcechain-accent", "--color-niyet-accent"):
        assert token in DESIGN_CSS
