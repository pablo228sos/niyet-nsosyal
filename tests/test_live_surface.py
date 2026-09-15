from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).parents[1]


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])


def test_live_surface_exposes_every_javascript_contract():
    html = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
    parser = IdCollector()
    parser.feed(html)

    required = {
        "connectionBadge",
        "languageToggle",
        "resetDemo",
        "authorTab",
        "responderTab",
        "authorView",
        "responderView",
        "requestText",
        "charCount",
        "loadScenario",
        "routeHuman",
        "resolveEvidence",
        "authorMessage",
        "restoreAuthor",
        "requestCard",
        "requestStatus",
        "requestTextPreview",
        "matchBlock",
        "matchedResponder",
        "matchReasons",
        "copyResponderLink",
        "evidenceBlock",
        "evidenceStatus",
        "evidenceItems",
        "answerBlock",
        "humanAnswer",
        "responderSelect",
        "availabilityToggle",
        "responderMeta",
        "inboxMessage",
        "inbox",
        "inboxRequestTemplate",
        "stagePost",
        "stageEvidence",
        "stageHuman",
        "stageResolved",
    }
    assert required <= parser.ids


def test_live_surface_keeps_resolution_story_and_honest_boundaries():
    html = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    assert "0 followers" in html
    assert "Bounded evidence, not a truth score." in html
    assert "Need" in html and "Evidence" in html and "Human" in html and "Resolved" in html
    assert "Research proves coffee consumption causes lower mortality" in script

    # The evidence button must select resolve mode, and the request function must
    # forward that mode as the API action. Keep this contract independent of
    # whether the action is written as a literal or passed through a variable.
    assert "openAuthorRequest('resolve')" in script
    assert "callApi({ action: mode, text: value })" in script

    assert "action: 'status'" in script
    assert "action: 'accept'" in script
    assert "action: 'answer'" in script
    assert "CAUSALITY_SHIFT" in script
