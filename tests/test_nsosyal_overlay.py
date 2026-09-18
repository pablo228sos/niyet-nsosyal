import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
OVERLAY = ROOT / "demo" / "nsosyal-overlay"
MANIFEST = json.loads((OVERLAY / "manifest.json").read_text(encoding="utf-8"))
BACKGROUND = (OVERLAY / "background.js").read_text(encoding="utf-8")
CONTENT = (OVERLAY / "content-v2.js").read_text(encoding="utf-8")
CSS = (OVERLAY / "overlay.css").read_text(encoding="utf-8")
PUBLISHED_CSS = (OVERLAY / "published-flow.css").read_text(encoding="utf-8")
README = (OVERLAY / "README.md").read_text(encoding="utf-8")


def test_overlay_requests_only_the_hosts_it_needs():
    assert MANIFEST["manifest_version"] == 3
    assert MANIFEST.get("permissions", []) == ["storage"]
    assert MANIFEST["host_permissions"] == ["https://niyet-nsosyal.vercel.app/*"]
    assert "action" not in MANIFEST

    script = MANIFEST["content_scripts"][0]
    assert script["matches"] == ["https://nsosyal.com/*", "https://www.nsosyal.com/*"]
    assert script["js"] == ["content-v2.js"]
    assert "css" not in script
    assert script["run_at"] == "document_idle"

    resources = MANIFEST["web_accessible_resources"]
    assert resources == [{
        "resources": ["overlay.css", "published-flow.css"],
        "matches": ["https://nsosyal.com/*", "https://www.nsosyal.com/*"],
    }]


def test_background_is_a_fixed_backend_proxy_not_an_arbitrary_fetch_bridge():
    assert "https://niyet-nsosyal.vercel.app/api/human_help" in BACKGROUND
    assert "https://niyet-nsosyal.vercel.app/api/human-help" in BACKGROUND
    assert "API_URLS" in BACKGROUND
    assert "ALLOWED_ACTIONS" in BACKGROUND
    assert "'inspect'" in BACKGROUND and "'resolve'" in BACKGROUND and "'status'" in BACKGROUND
    assert "message.url" not in BACKGROUND
    assert "credentials: 'omit'" in BACKGROUND
    assert "redirect: 'error'" in BACKGROUND
    assert "cache: 'no-store'" in BACKGROUND
    assert "trustedSender" in BACKGROUND
    assert "text.length > 1200" in BACKGROUND


def test_backend_errors_are_always_renderable_strings():
    assert "function errorText" in BACKGROUND
    assert "typeof value === 'object'" in BACKGROUND
    assert "JSON.stringify(value)" in BACKGROUND
    assert "data?.error ?? data?.message" in BACKGROUND
    assert "const domainError" in BACKGROUND
    assert "&& !domainError" in BACKGROUND


def test_overlay_is_css_isolated_and_does_not_mutate_nsosyal_actions():
    assert "attachShadow({ mode: 'closed' })" in CONTENT
    assert "chrome.runtime.getURL('overlay.css')" in CONTENT
    assert "chrome.runtime.getURL('published-flow.css')" in CONTENT
    assert "panel.innerHTML" not in CONTENT
    assert "document.cookie" not in CONTENT
    assert ".click()" not in CONTENT
    assert "fetch(" not in CONTENT
    assert "requestAnimationFrame" in CONTENT
    assert "MutationObserver" in CONTENT
    assert ":host" in CSS


def test_live_composer_detection_handles_rich_text_editors_and_nsosyal_send_action():
    assert "[contenteditable]:not([contenteditable=\"false\"])" in CONTENT
    assert "[data-lexical-editor]" in CONTENT
    assert "[data-slate-editor]" in CONTENT
    assert ".ProseMirror" in CONTENT
    assert "'gönder'" in CONTENT
    assert "findSendButtonNear" in CONTENT
    assert "state.lastEditable" in CONTENT
    assert "document.addEventListener('focusin'" in CONTENT
    assert "document.addEventListener('input'" in CONTENT
    assert "editableText(node)" in CONTENT


def test_composer_helper_stays_compact_and_clear_of_native_toolbar():
    assert "trigger.style.setProperty('right', 'auto')" in CONTENT
    assert "trigger.style.setProperty('right', narrow ? 'auto' : '24px')" in CONTENT
    assert "sendRect.left - 82" in CONTENT
    assert "trigger.dataset.fallback = 'false'" in CONTENT
    assert "trigger.dataset.fallback = 'true'" in CONTENT
    assert "trigger.dataset.entrypoint = 'composer'" in CONTENT
    assert "trigger.dataset.entrypoint = 'floating'" in CONTENT
    assert 'min-width:58px' in CSS
    assert 'height:32px' in CSS
    assert '.drsk-overlay-trigger[data-fallback="false"]{margin-top:-42px}' in CSS


def test_mobile_entrypoint_never_competes_with_nsosyal_floating_or_publish_controls():
    compact_css = CSS.replace(" ", "")

    assert '@media(max-width:760px)' in compact_css
    assert '.drsk-overlay-trigger[data-entrypoint="composer"]{margin-top:0!important;height:30px;min-width:54px;padding:09px}' in compact_css
    assert '.drsk-overlay-trigger[data-entrypoint="floating"]{display:none!important}' in compact_css
    assert "const narrow = innerWidth <= 760" in CONTENT
    assert "rect.right - 142" in CONTENT
    assert "rect.top - 38" in CONTENT
    assert "trigger.style.setProperty('right', narrow ? 'auto' : '24px')" in CONTENT
    assert '.drsk-overlay-panel{top:auto;left:0;right:0;bottom:0;width:100vw;max-height:min(78dvh,680px);border-radius:18px18px00;border-bottom:0}' in compact_css


def test_overlay_is_explicitly_a_concept_integration():
    assert "concept integration" in CONTENT.lower()
    assert "does not post to NSosyal or alter your account" in CONTENT
    assert "does **not** publish, edit, or delete NSosyal content" in README
    assert "standalone `/live` prototype remains the fallback" in README


def test_overlay_separates_evidence_inspection_from_human_consent():
    assert "action: 'inspect'" in CONTENT
    assert "action: 'resolve'" in CONTENT
    assert "askPerson" in CONTENT
    assert "human_recommended" in CONTENT
    assert "human_available" in CONTENT
    assert "chrome.storage.session" in CONTENT
    assert "Evidence was sufficient for this path" not in CONTENT


def test_human_routing_unlocks_only_after_the_post_is_visible():
    assert "findPublishedPost" in CONTENT
    assert "confirmPublishedPost" in CONTENT
    assert "watchForPublishedPost" in CONTENT
    assert "publicationRequired" in CONTENT
    assert "post_url: inspection.postUrl" in CONTENT
    assert "publishedCandidates" in CONTENT
    assert ".drsk-overlay-lifecycle" in PUBLISHED_CSS
    assert ".drsk-overlay-publish-gate" in PUBLISHED_CSS


def test_background_accepts_only_nsosyal_publication_urls():
    assert "function trustedPostUrl" in BACKGROUND
    assert "NSOSYAL_HOSTS.has(url.hostname)" in BACKGROUND
    assert "invalid_post_url" in BACKGROUND

def test_preview_packaging_keeps_backend_url_and_host_permission_in_sync():
    from scripts.package_nsosyal_overlay import build_runtime_files

    origin = "https://niyet-nsosyal-preview-test.vercel.app"
    runtime = build_runtime_files(origin)
    manifest = json.loads(runtime["manifest.json"].decode("utf-8"))
    background = runtime["background.js"].decode("utf-8")
    content = runtime["content-v2.js"].decode("utf-8")

    assert manifest["host_permissions"] == [f"{origin}/*"]
    assert f"{origin}/api/human_help" in background
    assert f"{origin}/api/human-help" in background
    assert f"{origin}/live" in content
    assert "https://niyet-nsosyal.vercel.app/api/human_help" not in background
    assert "https://niyet-nsosyal.vercel.app/live" not in content

def test_draft_inspection_is_explicitly_optional_and_private():
    assert "privateInspect: 'Private draft check only. Nothing has been posted or sent to a person.'" in CONTENT
    assert "If you want human context, publish this text normally first." in CONTENT
    assert "privateInspect: 'Bu yalnızca özel taslak kontrolüdür." in CONTENT
    assert "İnsan bağlamı istiyorsan bu metni normal şekilde yayınla." in CONTENT
    assert "if (!published && !request)" in CONTENT
    assert ".drsk-overlay-private-note" in PUBLISHED_CSS


def test_native_publish_detection_never_creates_a_human_request_by_itself():
    publish_listener = CONTENT.split("document.addEventListener('click', (event) => {", 1)[1].split("trigger.addEventListener('click'", 1)[0]
    escalate = CONTENT.split("async function escalateToHuman(text) {", 1)[1].split("async function resolveCurrentPost()", 1)[0]

    assert "watchForPublishedPost(text)" in publish_listener
    assert "action: 'resolve'" not in publish_listener
    assert "inspection?.published" in escalate
    assert "post_url: inspection.postUrl" in escalate
    assert "action: 'resolve'" in escalate



def test_extension_responder_handoff_matches_truthful_availability_copy():
    assert "LIVE_URL = 'https://niyet-nsosyal.vercel.app/live'" in CONTENT
    assert "no eligible responder is available right now." in CONTENT
    assert "Copy responder link" in CONTENT
    assert "navigator.clipboard.writeText(url.href)" in CONTENT
    assert "drsk-overlay-handoff-actions" in CONTENT


def test_extension_responder_handoff_actions_stay_mobile_safe():
    compact_css = CSS.replace(" ", "")
    assert ".drsk-overlay-handoff-actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center}" in compact_css
    assert "@media(max-width:760px){.drsk-overlay-handoff-actions,.drsk-overlay-handoff-actions.drsk-overlay-secondary{width:100%}}" in compact_css


def test_extension_keeps_latest_answer_available_after_the_composer_is_cleared():
    assert "RESOLVED_STORAGE_KEY = 'drsk-latest-resolved-v1'" in CONTENT
    assert "async function storeResolved(" in CONTENT
    assert "async function showLatestResolved()" in CONTENT
    assert "if (latest.status === 'ANSWERED') await storeResolved(latest, author.text)" in CONTENT
    assert "if (await showLatestResolved()) return;" in CONTENT


def test_final_demo_profiles_start_with_their_full_attention_budget():
    import json

    profiles = json.loads((ROOT / "data" / "responder_profiles_final_v2.json").read_text(encoding="utf-8"))
    assert profiles
    assert all(item["remaining_slots"] == item["daily_budget"] for item in profiles)
