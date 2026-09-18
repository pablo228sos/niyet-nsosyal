# DRSK final 2-hour execution handoff

This is a focused handoff for the final pre-submission window. Do not rediscover the whole project. Work from branch `fix/judge-ux-stabilization`, PR #31, current head `e9eba638f65ff2bc3b2642111e87127b1d15ed9b` unless a newer commit already exists.

## Current product truth

DRSK is a resolution layer for NSosyal-like social content. It is not a generic truth oracle and not an automatic censorship/filtering gate.

The product split is intentional:

1. Real NSosyal extension: optional author-side private draft check, exact published-post detection, explicit human routing after user consent.
2. `/live`: stable judge-safe product surface for repeated checks, four resolution states, two device views, responder handoff.

Core paths:

- `Check with DRSK` -> stateless `inspect` -> may show `EVIDENCE / HUMAN / BOTH / NONE` -> must not consume responder capacity.
- `Ask a relevant person` -> stateful `resolve` -> opens a NIYET request only when a human path is appropriate.
- Responder accepts and answers -> author sees `Resolved` and the answer in the same post context.

## What just happened in physical QA

Observed by manual browser testing:

1. `/live` repeated checks work visually for coffee, PID, opinion, and random factual claims.
2. The coffee case correctly shows SOURCECHAIN conflict/causality shift and then NIYET can route to Research Reviewer.
3. When switching to Responder manually, the dropdown may still be on the wrong identity, e.g. `Control Systems Volunteer`, so the inbox says empty even though the author card is routed to `Research Reviewer`.
4. Clicking `Open responder device` correctly opens the assigned responder context, but judges may naturally press the top `Responder` toggle instead. That must be smooth.
5. The latest extension build fixed MV3 storage access by exposing session storage and falling back to local storage. Keep that.
6. The shared-feed framing is better: Author and Responder should feel like two devices over the same social feed, not two different products.

## Codex mission, strict scope

Goal: make `/live` and the extension demo feel boring and judge-safe. Do not add new models, new architecture, Firebase, reader-side arbitrary DOM injection, new benchmarks, or redesign.

### P0 task A: auto-select the assigned responder on same-page device switch

Problem: After Author routes a request to `Research Reviewer`, pressing the top `Responder` toggle can show an empty inbox if the dropdown is currently on another responder.

Expected behavior:

- If there is a current author request with `assigned_responder.id`, switching to Responder from the same page should auto-select that responder unless the URL already explicitly requested a different responder.
- The Responder inbox should immediately show the routed request.
- The user should not need to click `Open responder device` for the ordinary in-page demo.
- `Open responder device` remains useful for a true second browser context.

Likely area:

- `web/live.js`
- functions around `setRole`, `renderAuthorRequest`, `refreshInbox`, responder dropdown initialization.

Suggested implementation shape:

```js
function assignedResponderId() {
  return currentAuthor?.request?.assigned_responder?.id || null;
}

function selectAssignedResponderForDemo() {
  const assigned = assignedResponderId();
  if (!assigned) return false;
  const select = $('#responderSelect');
  if (![...select.options].some((option) => option.value === assigned)) return false;
  select.value = assigned;
  return true;
}
```

Inside `setRole('responder')`, before `refreshInbox(true)` or `startInboxPoll()`, call the helper. Respect explicit URL param on initial load if it exists. Keep this tiny.

Regression tests:

- add/extend `tests/test_live_surface.py` to assert same-page responder switching uses assigned responder when available.
- test the specific contract, not implementation trivia.

Manual check:

1. `/live` -> Prepare demo.
2. Coffee -> Check with DRSK -> Ask a relevant person.
3. Press top `Responder` toggle, not Open responder device.
4. Dropdown should be `Research Reviewer` and inbox should show the coffee request with Accept.

### P0 task B: answer must resolve when using same-page responder toggle

Problem: If the user accepts/answers from the same page after switching to Responder, switching back to Author must update to `Resolved` without requiring a full reload.

Expected behavior:

- Responder -> Accept -> answer -> Send answer.
- Switch Author -> author card becomes `Resolved` and shows the answer.
- If needed, force one `status` refresh when entering Author and there is a current request with author token.

Likely area:

- `web/live.js`: `sendAnswer`, `startAuthorPoll`, `restoreAuthor`, `setRole('author')`.

Regression:

- add a test that `setRole('author')` triggers author refresh/poll when current author request exists.
- Do not mock a huge workflow unless the repo already has a helper. String/contract tests are acceptable for this final pass.

### P0 task C: keep extension stable, do not expand it

Do not try to make the extension attach buttons under every feed post. Extension scope remains:

- private draft inspect,
- exact published text detection,
- explicit human routing,
- latest resolved answer recovery.

Only touch extension if P0 regression fails.

Storage bug to preserve:

- `background.js` must keep `chrome.storage.session.setAccessLevel({ accessLevel: 'TRUSTED_AND_UNTRUSTED_CONTEXTS' })`.
- `content-v2.js` must keep safe `storageGet/storageSet/storageRemove` wrappers with `storage.local` fallback.

### P1 task D: final screenshot set

Prepare screenshot names in `docs/screenshots/` or provide a checklist if assets are captured manually. Use dark mode for `/live`, light/real mode for NSosyal extension.

Required screenshots:

1. `01_live_author_check_coffee.png` — `/live` Author after coffee `Check with DRSK`, SOURCECHAIN conflict visible.
2. `02_live_author_route_research_reviewer.png` — author after `Ask a relevant person`, NIYET card shows Research Reviewer + attention budget + Open responder device.
3. `03_live_responder_inbox_accept.png` — same `/live` switched to Responder, dropdown auto-selected Research Reviewer, request visible with Accept.
4. `04_live_resolved_answer.png` — Author shows Resolved + human answer.
5. `05_live_four_states.png` — EVIDENCE/HUMAN/BOTH/NONE compact feed visible.
6. `06_nsosyal_private_check.png` — real NSosyal extension showing private draft check and no request yet.
7. `07_nsosyal_published_detected.png` — real NSosyal extension showing published post detected and explicit human action.
8. `08_nsosyal_mobile_bottom_sheet.png` — mobile/narrow extension result, no overlap with native publish/nav.

Use these in README and presentation. Do not over-shoot dozens of images.

### P1 task E: README polish after code freeze

Do not rewrite the whole repo. Add/update only final landing parts:

- one hero paragraph: `Evidence first. Human context by choice.`
- four states: `EVIDENCE / HUMAN / BOTH / NONE`.
- short demo flow.
- architecture diagram or bullets: SOURCECHAIN, NIYET, Resolution Engine, NSosyal extension, `/live`.
- honest limitations:
  - extension is concept integration, not official NSosyal integration;
  - arbitrary reader-side injection is product target, not stable final scope;
  - ModernBERT is offline evaluation / retrieval research support, not every live runtime call;
  - SOURCECHAIN is bounded evidence, not a truth oracle;
  - synthetic responder profiles are demo/prototype state.

## Presentation teammate mission

The submitted deck must follow the official TEKNOFEST structure. Do not make it a generic startup pitch.

Use the current team deck as base, but make these content fixes:

1. Cover: keep project name `DRSK - Hibrit Sosyal Zekâ Katmanı`, thematic area `Sosyal Yapay Zeka`, team `BEYMAX`, Team ID `#917878`, Application ID `#5394657`.
2. Problem: keep the strong framing `source exists != source supports the claim` and the human-context gap. Make stats readable, not tiny.
3. Solution: show the Resolution Engine four states visually:
   - EVIDENCE: evidence enough,
   - HUMAN: no factual claim, human context needed,
   - BOTH: evidence exposes gap and human can interpret,
   - NONE: opinion/no action.
4. Method: be truthful. ModernBERT-TR is evaluation/retrieval research support; do not say the live demo depends on a heavy deployed model unless verified.
5. Prototype slide: replace generic text with real screenshots from the final screenshot set above.
6. Impact slide: phrase as `DRSK = not only verifying information, but routing the user to the right evidence and, when needed, the right person`.
7. Q&A backup: prepare answers for:
   - Why not just fact-checking?
   - What if evidence is insufficient?
   - Why human routing?
   - How do you prevent spam/overload?
   - Is this an official NSosyal integration?
   - What is synthetic vs production-ready?

Do not overclaim:

- no official NSosyal integration;
- no universal truth score;
- no fully finished arbitrary reader-side integration;
- no real production users behind responder profiles;
- no Firebase dependency for the demo core.

## Final demo script

1. Open `/live`.
2. Press `Prepare demo` once.
3. Author: coffee example -> `Check with DRSK`.
4. Explain: `The source says associated with lower mortality. The post says proves/causes. DRSK exposes that semantic shift.`
5. Press `Ask a relevant person`.
6. Explain: `Only now a human request is created. Repeated checks did not spend attention budget.`
7. Switch `Responder`.
8. Confirm dropdown is Research Reviewer and request appears. Accept, answer.
9. Switch `Author`. Show Resolved.
10. Point at four-state feed: `The same engine also handles pure evidence, pure human context, opinion, and mixed cases.`
11. Optional: show real NSosyal extension as proof of concept integration, not as the only demo surface.

## What Codex must report back

At the end, return exactly this summary:

```md
## Final Codex Report

Branch:
Head SHA:
Commits made:

### Fixed
- ...

### Tests run
- ...

### Manual checks performed
- ...

### Remaining risk
- ...

### Files/screenshots added
- ...

### Exact preview URL tested
- ...
```

If something fails, do not hide it. State the smallest safe workaround for judge demo.
