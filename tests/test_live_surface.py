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


def test_public_live_surface_is_product_facing_not_jury_prep():
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    assert "exampleScenario" in script
    assert "Load example" in script
    assert "Örneği yükle" in script
    assert "juryScenario" not in script
    assert "Load jury scenario" not in script
    assert "Jüri senaryosunu" not in script


def test_live_surface_recovers_from_shared_state_changes():
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    # Domain 404s must not be replayed against the alternate endpoint. A bare
    # deployment-level 404 may still select the alternate filename.
    assert "error.code = data.error || null" in script
    assert "error.status !== 404 || error.code" in script

    # Capacity-aware reallocation is expected while requests are still pending.
    # A responder acting on stale UI should get a fresh queue, not a raw code.
    assert "isStaleRoutingError" in script
    assert "recoverInboxConflict" in script
    assert "request_not_assigned" in script
    assert "responder_capacity_exhausted" in script
    assert "state_temporarily_unavailable" in script
    assert "await refreshBackendAndInbox()" in script


def test_live_surface_does_not_overclaim_state_durability():
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    assert "data.state_durable ? 'backendDurable' : 'backendMemory'" in script
    assert "durable shared state live" in script
    assert "prototype state live" in script
    assert "server-process demo state" not in script
