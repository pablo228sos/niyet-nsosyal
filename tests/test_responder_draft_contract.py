from pathlib import Path


ROOT = Path(__file__).parents[1]
MOTION = (ROOT / "web" / "live-motion.js").read_text(encoding="utf-8")
LIVE = (ROOT / "web" / "live.js").read_text(encoding="utf-8")


def test_responder_polling_preserves_unsent_answer_drafts():
    # live.js still refreshes the inbox frequently and replaces its card DOM.
    assert "inbox.replaceChildren()" in LIVE
    assert "window.setInterval(refreshBackendAndInbox, 1300)" in LIVE

    # The UX layer must therefore persist drafts by stable request id and restore
    # them after each inbox child-list replacement.
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
