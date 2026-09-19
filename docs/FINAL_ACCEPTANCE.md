# Final acceptance snapshot

Date: **2026-09-19**

This page records the final pre-jury verification state of the current public build.

## Release state

- runtime-tested code snapshot: `20276ccc9ad44c07c39c00d8c5c8f7bd4a8b47f5`
- later main changes through PR #35 are documentation/product-thesis only and do not change the verified runtime contracts
- Production: <https://niyet-nsosyal.vercel.app/live>
- runtime acceptance GitHub Actions run **#601**: PASS
- latest `main` CI: PASS
- current Production deployment: **READY**
- extension package: Manifest V3, version **0.5.0**, Production backend origin

## Directly observed `/live` acceptance

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

## Authenticated real-NSosyal hardware pass

A manual pass on an authenticated real NSosyal session reached the complete product handoff:

```text
real NSosyal composer
-> private DRSK evidence check
-> native NSosyal publish
-> exact published-post detection
-> explicit Ask a relevant person
-> Research Reviewer
-> responder device
-> Accept
-> Answer
-> answer returned to the real NSosyal DRSK overlay
```

That pass also exposed one persistence edge case: after a resolved request, reloading NSosyal and explicitly checking the same non-empty text could restore the historical ANSWERED request instead of starting a fresh private inspect. PR #34 fixed the boundary while preserving answer recovery. The same fix also stopped presenting routing-time capacity as if it were current after the request left OPEN state.

The post-fix behavior is covered by regression tests in the final main suite.

The authenticated real-host sequence is preserved visually in **[Real NSosyal acceptance](REAL_NSOSYAL_ACCEPTANCE.md)**.

## Software verification

- targeted final contracts: **75 passed**
- full suite: **286 passed**
- JavaScript syntax: PASS
- Python compileall: PASS
- site build: PASS
- extension package: PASS
- matching evaluation: PASS
- SOURCECHAIN development evaluation: PASS
- annotation validation: PASS
- SOURCEBENCH-TR validation: PASS
- runtime acceptance GitHub Actions #601: PASS
- latest `main` CI: PASS
- current Production deployment: READY

The tracked summary is kept in [`../results/test_summary.json`](../results/test_summary.json).

## Product truth preserved by acceptance

- no universal truth score;
- no automatic human contact after Check;
- no claim that synthetic responders are production users;
- no claim that ModernBERT-TR runs in the lightweight live path;
- no claim that the extension is an official NSosyal integration;
- no forced verdict when the safe outcome is `INSUFFICIENT`;
- human answers remain human context rather than verified evidence;
- arbitrary reader-side injection under every foreign NSosyal post remains native-integration scope, not a claimed current extension feature.

The acceptance standard is stricter than “the happy path renders.” A state is final only when backend state, user-facing semantics and lifecycle agree.