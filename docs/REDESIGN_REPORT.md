# NIYET / NSosyal frontend rebuild — 2026-09-05

## Changed

Rebuilt both server routes (`/`, `/lab`) and all five feed sections around a shared design system. The initial video and modal gate have been replaced by the working composer and feed. Removed unused legacy styles only after checking references. Kept plain JavaScript and the existing Python engines; no framework migration or backend rewrite.

## Product map and functionality preserved

| Existing capability | New interaction and verification |
| --- | --- |
| Response gate and four NIYET intents | Inline analysis, author correction, manual override and dismissal |
| Shared-window allocation | Real API results, current request queue and capacity context |
| Responder acceptance, skipping, pausing | Accessible response panel; retryable failures; same-person resume |
| SOURCECHAIN claims and provenance | Expandable real passages, source URLs, relation and distortion details |
| Insufficient evidence escalation | Ask a person creates an actionable NIYET request |
| Post composition | Validation, character count, browser-session draft and post persistence |
| Feed and social sections | Feed, searchable Explore, sample Communities/Profile, explicit unconnected Messages state |
| Allocation experiments | `/lab`, all four batches, method comparison, threshold in URL and retry |
| English and Turkish | Shared language preference across feed and laboratory |
| Technical diagnostics | Keyboard-accessible modal, available without blocking first use |

Decorative media/poll/location controls had no underlying feature and were removed. Demo social actions operate on browser-session content; this is not a live social network.

## UX improvements

The first screen explains evidence and human help and provides example prompts. Primary creation stays in the center, responder controls sit alongside it, and diagnostics are disclosed on demand. Mobile uses bottom navigation and a focus-managed response drawer. Sections support direct URLs, refresh, and browser back/forward. Empty and failed results explain their meaning without fabricated success.

## Design system

See `DESIGN.md` and `web/design-system.css`: native system typography, restrained cobalt actions, teal evidence, flat surfaces, consistent spacing, shared controls, automatic dark mode and reduced motion. Desktop has three functional columns; tablet/mobile use one main content column and a responder drawer. No external fonts, video gate, decorative gradients or nested card stacks.

Taste Skill informed hierarchy, density and restrained surfaces. A generated working-screen reference informed composition before implementation; its invented content was not used. Awesome Design MD's Intercom reference informed conversational clarity. These references were adapted to the existing research product.

## Bugs fixed

- Editing a post invalidates old evidence and asynchronous analysis; new posts cannot inherit an older claim's evidence.
- Example prompts now use the same input-state lifecycle as typed text, including draft persistence and validation cleanup.
- Confirmed match state is separate from subsequent composer analysis.
- Failed accept and skip actions remain recoverable; successful acceptance cannot be skipped again.
- Resume applies to the responder who was paused even if allocation changes.
- Evidence escalation creates a real pending request with working responder actions.
- Offline state cannot fabricate a responder. Opinion results do not invite factual verification.
- Dialogs trap focus, make background content inert and return focus; Escape closes the active overlay.
- Lab failures expose a working retry action. Hash navigation survives reload and browser history.

## Playwright QA

Used Playwright Agent CLI against the production Worker adapter on port 8767, with the actual Vercel API upstream. `scripts/browser_qa.js` covers 47 assertions: first visit, validation, intent correction, routing, acceptance failure/retry, pause/resume, local posts and refresh, all five sections, search, history, source disclosure, human escalation, EN/TR, all four lab batches, threshold URLs, error/retry, and overflow checks at 360, 430, 768, 1280 and 1440 pixels.

`scripts/browser_regression.js` passed 13 additional assertions covering skip/reallocation, missed-intent override, stale evidence prevention, opinion handling, reverse keyboard focus, modal inertness, 200% text size, reset cancellation/confirmation, offline behavior and 404 recovery. Reset return values are stubbed to exercise both application branches. Screenshots of desktop evidence, mobile feed, laboratory and dark mode were visually inspected. Intentional 503 responses are injected only for failure-state tests; the main run recorded zero uncaught page errors.

## Accessibility and Vercel guideline audit

Audited semantic headings, labels, inline errors, visible focus, keyboard controls, dialogs, touch targets, contrast, reduced motion, source links, URL state, and loading/empty/error/disabled states against the Vercel Web Interface Guidelines. Fixed invisible/offscreen skip-link capture, background focus leakage and missing secondary-view page headings. Axe WCAG 2 A/AA and 2.1 AA checks cover six routes in both color schemes. Automated checks do not replace testing with assistive technology or establish full WCAG certification.

## Performance

Removed first-visit video work, external font requests and three unused stylesheet layers. The Sites build embeds seven necessary assets in an approximately 189 KB Worker with no frontend runtime dependencies. Local Lighthouse measured Performance 99, Accessibility 100, Best Practices 100; LCP 1.8 s and CLS 0.057. These are local lab measurements, not production field statistics; API latency remains external.

## Remaining issues

- The Python backend remains on `niyet-nsosyal.vercel.app`; Sites serves the rebuilt frontend and proxies only the two fixed API paths. Backend downtime affects analysis and experiments.
- SOURCECHAIN uses a small controlled corpus and deterministic baseline. Missing evidence is not proof of falsity. The report's planned capabilities remain planned.
- NIYET uses a Turkish development model and sample responder profiles. English intent classification can miss requests; author override is available and tested.
- Capacity, posts and draft data are browser-session state. No authenticated multi-user persistence or live messaging was added.
- Browser automation ran in Chromium. Cross-engine and real screen-reader/device testing remain future validation.

## Verification and reproduction

`python scripts/build_site.py` validates JavaScript syntax and produces `dist/server/index.js`. `pytest -q`: 135 passed. Start `node scripts/preview_worker.mjs`, open a Playwright CLI session, then run the two browser scripts with `run-code --filename ... --raw`. For accessibility, pass an installed `axe-core/axe.min.js` path to `scripts/prepare_accessibility_qa.py`, then execute the generated `output/qa/accessibility.js` in that browser session. QA output and screenshots remain under ignored `output/qa/`.

## References

- https://github.com/vercel-labs/web-interface-guidelines/blob/main/command.md
- https://www.tasteskill.dev/
- https://github.com/voltagent/awesome-design-md
- https://getdesign.md/intercom/design-md
- https://github.com/Leonxlnx/taste-skill
- https://playwright.dev/agent-cli/introduction
