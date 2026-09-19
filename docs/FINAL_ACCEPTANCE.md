
# Final acceptance snapshot

Date: **2026-09-19**

This page records the final pre-jury verification state of the current public build. It separates what was directly observed in browser acceptance from what remains dependent on an authenticated real NSosyal session.

## Release state

- current acceptance merge: `cc9c9915187abda66ee98f9018a1b955091efe46`
- Production: <https://niyet-nsosyal.vercel.app/live>
- GitHub Actions run **#591**: PASS
- Vercel Production for the acceptance merge: **READY**
- extension package: Manifest V3, version **0.5.0**, Production backend origin

## Directly observed `/live` acceptance

The controlled Production/Preview flow was exercised across separate browser contexts.

| Scenario | Result |
| --- | --- |
| Prepare demo restores canonical state and responder budgets | PASS |
| Coffee private Check creates no human request | PASS |
| Check preserves responder capacity | PASS |
| Coffee exposes `CONFLICTING` + `CAUSALITY_SHIFT` | PASS |
| Explicit Ask creates one request | PASS |
| Canonical route selects Research Reviewer | PASS |
| Separate responder link opens the same request/backend | PASS |
| Accept consumes capacity exactly once | PASS |
| Duplicate Accept is rejected without second capacity spend | PASS |
| Answer persists and Author reaches `Resolved` | PASS |
| Resolved answer survives reload | PASS |
| Author budget refreshes to the current backend value | PASS |
| NONE opinion path | PASS |
| HUMAN PID path without fake evidence failure | PASS |
| EVIDENCE WHO path | PASS |
| Arbitrary English/Turkish checks | PASS |
| Safe weak-evidence / `INSUFFICIENT` behavior | PASS |
| EN/TR controls and dark/light contracts | PASS |
| 760 / 750 / 700 / 600 / 390 responsive checks | PASS |

The final acceptance fix addressed a UI telemetry mismatch only: backend capacity was already correct after Accept, while the Author card could display the routing-time value until reload. PR #32 refreshes responder state when the request status changes.

## Software verification

- targeted final contracts: **73 passed**
- full suite: **284 passed**
- JavaScript syntax: PASS
- Python compileall: PASS
- site build: PASS, 25 assets
- extension package: PASS
- matching evaluation: PASS
- SOURCECHAIN development evaluation: PASS with the documented 3/4 alignment baseline
- annotation validation: PASS
- SOURCEBENCH-TR validation: PASS

The tracked summary is kept in [`../results/test_summary.json`](../results/test_summary.json).

## NSosyal concept adapter

The extension contract is covered by automated package/API/storage/publish-consent/regression tests and was manually exercised on authenticated NSosyal during development.

The final automated acceptance environment could not certify the real host DOM because `https://nsosyal.com/home` redirected to the login page. We therefore do **not** present that run as authenticated real-host proof.

Before using the full extension-first jury scenario, presentation hardware should confirm:

1. one safe composer-bound DRSK action;
2. private draft Check;
3. no automatic publication or human request;
4. native NSosyal publication;
5. exact published-text detection;
6. explicit human opt-in;
7. responder handoff;
8. answer restore;
9. no storage/CORS/runtime errors;
10. narrow-screen non-overlap.

If the final host pass is not clean, the approved fallback is to use the real overlay only for the integration/consent boundary and complete the two-device lifecycle on `/live`.

## Boundaries preserved by acceptance

- no universal truth score;
- no automatic human contact after Check;
- no claim that synthetic responders are production users;
- no claim that ModernBERT-TR runs in the lightweight live path;
- no claim that the extension is an official NSosyal integration;
- no forced evidence result when the safe outcome is `INSUFFICIENT`.

The acceptance standard is deliberately stricter than “the happy path renders.” A visible state is considered final only when the backend state, user-facing semantics and lifecycle agree.
