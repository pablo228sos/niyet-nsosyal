# DRSK final judge build

Status: final judge-facing build merged to `main`, 2026-09-19.

## Product contract

DRSK is a resolution layer for social content.

- SOURCECHAIN provides bounded claim-to-evidence intelligence.
- NIYET provides capacity-aware human routing.
- The Resolution Engine exposes four user-facing paths: `EVIDENCE`, `HUMAN`, `BOTH`, `NONE`.
- A private Check is stateless and never consumes responder attention.
- A human request opens only after explicit user action.
- Weak evidence fails closed as `INSUFFICIENT`; the system does not manufacture a source or truth score.

## Final branch state

- stabilization PR [#31](https://github.com/pablo228sos/niyet-nsosyal/pull/31) merged the final product/UX build;
- acceptance PR [#32](https://github.com/pablo228sos/niyet-nsosyal/pull/32) fixed the final stale responder-capacity display and was merged after targeted, full-suite and Preview verification;
- current acceptance merge commit: `cc9c9915187abda66ee98f9018a1b955091efe46`;
- Production: <https://niyet-nsosyal.vercel.app/live>;
- GitHub Actions run #591: PASS;
- Vercel Production from the acceptance merge: READY.

Upstash Redis REST provides durable shared state when configured. `TAVILY_API_KEY` is the primary live evidence credential. Brave remains an optional provider when configured.

## Proved in the final build

- repeated `Check with DRSK` calls do not open human requests or consume capacity;
- `EVIDENCE`, `HUMAN`, `BOTH` and `NONE` have regression coverage;
- coffee produces `BOTH`, `CONFLICTING` and `CAUSALITY_SHIFT`;
- a PID/control question produces `HUMAN` without a fake insufficient-evidence card;
- an opinion produces `NONE`;
- arbitrary factual claims can safely end at supported, partial, conflicting or insufficient evidence;
- only explicit `Ask a relevant person` opens NIYET routing;
- relevance, willingness, active state and remaining attention budget are hard constraints;
- same-page Responder switching follows the assigned responder;
- a separate responder-device link works in an independent browser session;
- Accept consumes capacity once;
- Answer persists;
- returning to Author refreshes to `Resolved` and shows the human answer;
- Preview extension packaging keeps API origin, manifest permission and responder link on one backend;
- extension storage has guarded session access and a local fallback.

## Final verification

- targeted: **73 passed**
- full suite: **284 passed**
- live + extension JavaScript syntax: PASS
- site build: **25 assets**
- extension package: PASS
- repeated-check capacity invariant: PASS
- GitHub Actions run #591: PASS
- Vercel Production on `cc9c991`: READY

Five final `/live` screenshots are committed under [`docs/screenshots/`](screenshots/).

## Judge flow

Use **Prepare demo** once, then:

1. coffee claim → **Check with DRSK**;
2. show the source passage and `CAUSALITY_SHIFT`;
3. point out that the check contacted nobody;
4. press **Ask a relevant person**;
5. show **Research Reviewer** and attention budget;
6. switch to Responder or open the responder-device link;
7. Accept;
8. answer;
9. return to Author;
10. show **Resolved**.

For judge-supplied text, use Check repeatedly without reset. `INSUFFICIENT` is a valid safe outcome.

## Real NSosyal concept adapter

The extension was manually exercised on a real authenticated NSosyal page during final development.

~~~text
private draft inspect
-> no human request
-> native NSosyal publish
-> exact published text detected
-> explicit Ask a relevant person
-> NIYET request
-> responder
-> answer
-> resolved author state
~~~

The final automated acceptance environment could not enter an authenticated NSosyal session because the host redirected to login. Package, API, consent, storage and responsive contracts are covered by tests, but the final authenticated host-DOM visual pass remains a presentation-hardware gate. The `/live` flow is the fully observed judge-safe fallback.

## Deliberate boundaries

- concept integration, not official NSosyal integration;
- arbitrary reader-side analysis under every foreign feed post is future native scope;
- ModernBERT-TR remains offline evaluation;
- responder profiles are synthetic fixtures;
- Firebase is isolated production hardening, not judge-core dependency;
- SOURCEBENCH-TR is a development regression set;
- live search provides candidate evidence, not truth verification;
- production identity, abuse controls and rate limiting remain separate hardening work.

## Freeze rule

After this point accept only reproduced blockers: minimal diff, regression coverage, green checks and Preview verification. No new product scope before the final.
