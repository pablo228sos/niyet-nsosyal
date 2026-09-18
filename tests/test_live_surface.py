import json
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
        "openResponderDevice",
        "copyResponderLink",
        "attentionBudget",
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
    assert "openAuthorRequest('inspect')" in script
    assert "openAuthorRequest('resolve')" in script
    assert "callApi({ action: mode, text: value })" in script

    assert "action: 'status'" in script
    assert "action: 'accept'" in script
    assert "action: 'answer'" in script

    # Explainability is generic: typed distortions come from the API while the
    # UI compares the actual claim with the actual stored evidence passage.
    assert "item.claim_text" in script
    assert "item.passage" in script
    assert "item.distortions" in script
    assert "appendDistortionComparison" in script


def test_public_live_surface_is_product_facing_not_jury_prep():
    html = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")
    combined = f"{html}\n{script}"

    assert "exampleScenario" in script
    assert "Load example" in combined
    assert "Örneği yükle" in script
    assert "juryScenario" not in combined
    assert "Load jury scenario" not in combined
    assert "Jüri senaryosunu" not in combined


def test_final_integrated_surface_is_the_default_entrypoint():
    config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    local_server = (ROOT / "scripts" / "serve_local.py").read_text(encoding="utf-8")

    # Vercel serves static index.html before rewrites, so the final surface must
    # use a redirect that runs before filesystem resolution.
    assert {
        "source": "/",
        "destination": "/live",
        "permanent": False,
    } in config.get("redirects", [])
    assert "rewrites" not in config

    assert 'if route in {"", "/live"}:' in local_server
    assert 'self.path = "/live.html"' in local_server


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


def test_successful_author_restore_hides_the_accessible_restore_control():
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")
    refresh_author = script.split("async function refreshAuthor(", 1)[1].split(
        "function startAuthorPoll()", 1
    )[0]

    assert "$('#restoreAuthor').hidden = true" in refresh_author
    assert refresh_author.index("$('#restoreAuthor').hidden = true") < refresh_author.index(
        "renderAuthorRequest(currentAuthor.request)"
    )


def test_no_request_result_stops_stale_author_poll_before_rendering():
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")
    no_request = script.split("if (!result.request) {", 1)[1].split(
        "persistAuthor(result.request)", 1
    )[0]

    assert "stopAuthorPoll();" in no_request
    assert no_request.index("stopAuthorPoll();") < no_request.index(
        "currentAuthor = null"
    )

    assert "let authorPollGeneration = 0" in script
    assert "generation !== authorPollGeneration" in script
    assert "const generation = ++authorPollGeneration" in script
    assert "runAuthorPoll(generation)" in script


def test_none_resolution_does_not_render_a_stale_evidence_card():
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")
    no_request = script.split("if (!result.request) {", 1)[1].split(
        "persistAuthor(result.request)", 1
    )[0]

    assert "const path = result.resolution?.path" in no_request
    assert "if (path)" in no_request
    assert "status: path" in no_request
    assert "evidence_context: path === 'NONE' ? null" in no_request
    assert no_request.index("$('#requestCard').hidden = true") < no_request.index(
        "if (path)"
    )


def test_responder_handoff_and_loading_copy_match_actual_behavior():
    html = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    assert "demoDevice: 'Demo device'" in script
    assert "authorTab: 'Author'" in script
    assert "responderSide: 'DRSK Requests'" in script
    assert "routeHuman: 'Ask a relevant person'" in script
    assert "routeHuman: 'İlgili bir kişiye sor'" in script
    assert "openResponder: 'Open responder device'" in script
    assert "copyResponder: 'Copy responder link'" in script
    assert "Attention budget remaining" in script
    assert "no eligible responder is available right now" in script
    assert 'id="openResponderDevice"' in html
    assert 'id="copyResponderLink"' in html
    assert "window.open(link, '_blank', 'noopener,noreferrer')" in script
    assert "await navigator.clipboard.writeText(link)" in script
    assert "checking: 'Checking evidence and routing…'" in script
    assert "checking: 'Kanıt ve yönlendirme kontrol ediliyor…'" in script


def test_live_curated_state_feed_is_small_static_and_truthful():
    html = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    assert "Four resolution states" in html
    assert html.count("resolution-chip") == 4
    for state in ("EVIDENCE", "HUMAN", "BOTH", "NONE"):
        assert f">{state}<" in html
    assert "They are not injected into real NSosyal posts." in script
    assert "stateEvidenceText" in script
    assert "stateHumanText" in script
    assert "stateBothText" in script
    assert "stateNoneText" in script


def test_desktop_demo_controls_are_visible_and_prepare_is_one_action():
    html = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")
    css = (ROOT / "web" / "live-nsosyal.css").read_text(encoding="utf-8")

    assert 'id="prepareDemo"' in html
    assert "data-language-toggle" in html
    assert "data-reset-demo" in html
    assert "async function prepareDemo()" in script
    prepare = script.split("async function prepareDemo()", 1)[1].split("$$('[data-language-toggle]')", 1)[0]
    assert "action: 'reset'" in prepare
    assert "clearLocalDemoState()" in prepare
    assert "setRole('author')" in prepare
    assert "exampleScenario[language]" in prepare
    assert ".desktop-demo-controls" in css


def test_curated_state_feed_inherits_dark_theme_instead_of_forcing_white_cards():
    css = (ROOT / "web" / "live-nsosyal.css").read_text(encoding="utf-8")

    assert ".state-post {" in css
    assert "background: var(--ns-panel)" in css
    assert ".state-post p { color: var(--ns-text); }" in css
    assert ".state-post > small { color: var(--ns-muted); }" in css


def test_load_example_has_identical_canonical_outcome_in_en_and_tr_ui():
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    assert "const canonicalExampleScenario =" in script
    assert "en: canonicalExampleScenario" in script
    assert "tr: canonicalExampleScenario" in script
    assert "Research proves coffee consumption causes lower mortality." in script


def test_live_check_is_stateless_and_human_routing_requires_a_separate_action():
    html = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    assert "Check with DRSK" in html
    assert "postWithDrsk: 'Check with DRSK'" in script
    assert "postWithDrsk: 'DRSK ile kontrol et'" in script
    assert "$('#resolveEvidence').addEventListener('click', () => openAuthorRequest('inspect'))" in script
    assert "$('#routeHuman').addEventListener('click', () => openAuthorRequest('resolve'))" in script
    assert "humanOptional: 'Evidence checked. Human context is available only if you choose Ask a relevant person.'" in script


def test_multi_control_bindings_use_query_selector_all_helper():
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    assert "$$('[data-language-toggle]').forEach" in script
    assert "$$('[data-reset-demo]').forEach" in script
    assert "\n  $('[data-language-toggle]').forEach" not in script
    assert "\n  $('[data-reset-demo]').forEach" not in script


def test_live_check_renders_every_resolution_path_without_opening_a_request():
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")
    no_request = script.split("if (!result.request) {", 1)[1].split("persistAuthor(result.request)", 1)[0]

    assert "const path = result.resolution?.path" in no_request
    assert "if (path)" in no_request
    assert "status: path" in no_request
    assert "assigned_responder: null" in no_request


def test_live_explains_that_checks_repeat_without_opening_human_requests():
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    assert "Check as many posts as you want." in script
    assert "A human request opens only when you choose Ask a relevant person." in script
    assert "İstediğin kadar gönderiyi kontrol et." in script


def test_author_and_responder_are_device_views_over_one_shared_feed():
    html = (ROOT / "web" / "live.html").read_text(encoding="utf-8")
    script = (ROOT / "web" / "live.js").read_text(encoding="utf-8")

    assert 'id="sharedFeed"' in html
    assert html.index('id="sharedFeed"') > html.index('id="responderView"')
    assert html.index('id="requestCard"') > html.index('id="sharedFeed"')
    assert html.index('resolution-state-feed') > html.index('id="sharedFeed"')
    assert "$('#sharedFeed').hidden" not in script
    assert "$('#authorView').hidden = responder" in script
    assert "$('#responderView').hidden = !responder" in script
