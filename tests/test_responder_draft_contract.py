from pathlib import Path


ROOT = Path(__file__).parents[1]
MOTION = (ROOT / "web" / "live-motion.js").read_text(encoding="utf-8")
LIVE = (ROOT / "web" / "live.js").read_text(encoding="utf-8")


def test_responder_polling_skips_unchanged_dom_and_preserves_drafts():
    # Polling must not rebuild the card DOM when the server snapshot is
    # unchanged. This is the primary anti-flicker contract.
    assert "const snapshot = JSON.stringify(requests)" in LIVE
    assert "if (!force && snapshot === inboxSnapshot) return" in LIVE
    assert "window.setTimeout(() => runInboxPoll(generation), 1800)" in LIVE
    assert "setInterval(refreshBackendAndInbox" not in LIVE

    # Draft preservation remains a second line of defence when a real state
    # transition legitimately replaces a request card.
    assert "const responderDrafts = new Map()" in MOTION
    assert "requestIdFor" in MOTION
    assert "saveResponderDraft" in MOTION
    assert "restoreResponderDrafts" in MOTION
    assert "inboxObserver.observe(inbox, { childList: true })" in MOTION
    assert "textarea.value = draft.value" in MOTION


def test_responder_polling_restores_focus_and_selection_for_active_draft():
    assert "focusedDraftRequestId" in MOTION
    assert "textarea.focus({ preventScroll: true })" in MOTION
    assert "textarea.setSelectionRange(start, end)" in MOTION


def test_responder_metadata_only_rerenders_when_capacity_changes():
    assert "const nextSnapshot = JSON.stringify(nextResponders)" in LIVE
    assert "if (nextSnapshot !== responderSnapshot)" in LIVE
    assert "inboxPollCycle % 5 === 0" in LIVE
