# NIYET global asset integration and polish

This pass builds on commit `f5f691e` and preserves the Python NIYET, SOURCECHAIN and Resolution Engine. The real routes remain `/` and `/lab`, with Feed, Explore, Communities, Messages and Profile sections and the existing evidence deep link.

## Changes

- Integrated the supplied NIYET wordmark/mark into both headers, sidebar and favicon. Replaced the previous DRSK-facing browser title with NIYET while retaining DRSK internals.
- Created a dark default identity, explicit persistent light option, bounded hero wave, selective focus background and softly masked laboratory illumination.
- Added a five-step SOURCECHAIN explanation and a result trail driven by real evidence data. Supplied icons use `currentColor`; no source credibility score or certification was invented.
- Presented EVIDENCE, HUMAN, BOTH, NONE and DEFERRED through consistent icons, plain-language labels and next-step explanations.
- Moved repeated claim/passage comparison behind disclosure. Exposed real publication date, passage location, origin cluster and document hash. Original API explanations remain available under Analysis notes.
- Corrected comparison association to use the evidence item's claim ID when available, rather than always selecting the first claim.
- Added analysis progress, stale-progress cleanup, retry after unavailable analysis, clear-search recovery and a return action in empty Messages.
- Styled laboratory loading skeletons, prevented duplicate retry clicks, removed raw HTTP exception text from user-facing result areas.
- Added visible mobile navigation labels; retained keyboard traps, focus return, inline validation, history navigation, author overrides and all allocation actions.

## Asset accounting

All 29 supplied files were reviewed and assigned a purpose. See `ASSET_INVENTORY.md` for the file-by-file mapping. Only selected optimized derivatives ship to the browser. Original assets stay in the design directory for reproducibility. No moodboard or composition screenshot is embedded as an interface.

## Verification

- Production Worker build and JavaScript syntax validation pass. The Worker contains 16 resources and is approximately 390 KB before transfer compression.
- Python suite: 135 passed.
- Main Playwright suite: 47 checks pass against the actual API through the production Worker adapter.
- Regression suite: 13 checks pass, including acceptance/skip recovery, stale evidence, reset branches, offline behavior, dialog focus and 200% text sizing.
- Asset/polish suite: 47 checks pass, including source provenance, appearance persistence, loading/retry, every section at 375/768/1366/1440/1920 px, reduced motion and empty-state recovery.
- No uncaught JavaScript errors or asset 404s in the polish suite. Intentional 503 responses are used only for error-state testing.
- Local production-adapter Lighthouse: Performance 98, Accessibility 100, Best Practices 100; LCP 2.1 s, CLS 0.061. These are lab measurements, not production field statistics.
- Axe WCAG A/AA and 2.1 AA: six routes in both explicit themes, zero violations in the audited states. This is automated coverage, not a full accessibility certification.
- Screenshots cover all six routes on mobile and laptop plus evidence, SOURCECHAIN and light-theme laboratory. Side-by-side visual review found and corrected a hard gradient edge; desktop and mobile remain real layouts.

## Vercel guideline audit

Reviewed semantic structure, theme consistency, visible focus, real form labels, error recovery, disclosure controls, source link safety, URL state, reduced motion, fixed mobile navigation, overflow, loading and asset requests. Dense evidence/results use solid surfaces; decorative assets are limited to introductions and empty/explanatory areas. Full hashes wrap rather than overflow. Native details retain keyboard support.

## Remaining boundaries

The interface is polished, but the underlying product still has its documented research limitations: controlled evidence corpus, a Turkish development intent model, sample responder/community/profile data, browser-session capacity/posts, and no live messaging or authenticated multi-user backend. The site clearly describes those limits. Sites continues to call the existing Vercel Python API; availability and latency depend on it. QA ran in Chromium, not every browser engine or assistive technology. Private Sites access still requires the owner's ChatGPT login; this task does not change the audience.

## Reproduce

1. With Pillow available, run `python scripts/prepare_brand_assets.py` only if regenerating assets.
2. Run `python scripts/build_site.py` and `node scripts/preview_worker.mjs`.
3. Use Playwright Agent CLI `run-code --filename` with `scripts/browser_qa.js`, `scripts/browser_regression.js`, and `scripts/polish_qa.js`.
4. Generate the axe callback with `scripts/prepare_accessibility_qa.py PATH_TO_AXE_MIN_JS`.

QA files and screenshots are in ignored `output/qa/`. Design rules are in `DESIGN.md`.
