# Engineering journey

DRSK reached its final prototype by removing attractive failure modes, not by adding features until the last minute.

This is the short evidence trail behind the final product contract.

## NIYET became capacity-aware

The earliest prototype focused on routing response-seeking posts to synthetic responder profiles. Relevance alone was not enough. A responder also had to be willing, active and have remaining attention budget.

The allocator therefore moved from independent recommendations to a bounded shared-capacity window where unmatched is a valid result.

The frozen reviewed matching set contains 32 requests × 8 responder profiles = 256 pairs. Two team reviewers agreed exactly on 243 pairs: 94.92%, quadratic weighted κ = 0.9756.

## SOURCECHAIN changed the evidence question

The evidence side was built around passage-level provenance rather than a generic trust score.

The canonical coffee case makes the problem visible:

- post: research **proves coffee causes** lower mortality;
- source: higher coffee consumption was **associated with** lower mortality.

The source is real. The claim/evidence relationship is still conflicting.

That pushed the prototype toward explicit causality, certainty, quantity, scope, attribution and temporal shifts.

## Live retrieval forced fail-closed behavior

A production audit with arbitrary Turkish and English inputs exposed a more dangerous problem than missing recall: irrelevant live pages could look superficially similar enough to be treated as evidence.

A fabricated Karakol PM2.5 claim could match pages through generic wording or numeric coincidence.

The fix was general rather than case-specific:

- strong verified-corpus matches keep the fast path;
- live evidence must clear quality and textual-anchor gates;
- numbers alone cannot qualify a passage;
- weak results remain `INSUFFICIENT`;
- Tavily basic is attempted before advanced search;
- the controlled corpus remains the deterministic fallback.

The lesson was simple: a system that safely refuses weak evidence is more trustworthy than one that always produces an answer.

## Consent became part of the architecture

PR [#27](https://github.com/pablo228sos/niyet-nsosyal/pull/27) separated private evidence inspection from explicit human routing.

PR [#28](https://github.com/pablo228sos/niyet-nsosyal/pull/28) anchored NIYET to a visible published NSosyal post. The adapter can inspect a draft, but no human request exists until the exact text is published and the author explicitly asks for a relevant person.

This became a product invariant, not a UI preference.

## Arbitrary-input evidence was hardened

PR [#29](https://github.com/pablo228sos/niyet-nsosyal/pull/29) closed failures found in arbitrary-input testing:

- dotted Turkish numbers/version identifiers were preserved;
- numeric coincidence stopped creating false conflicts;
- certainty shifts gained Turkish coverage;
- only `SUPPORTED` evidence became sufficient;
- weak/deictic claims and obvious user-generated sources fail closed;
- stale UI state stopped leaking between posts.

No benchmark-specific synonym rule was added just to turn one remaining SOURCEBENCH case green.

## Physical NSosyal testing changed the mobile contract

A floating DRSK action looked attractive in a mockup, but real NSosyal testing showed there was no consistently safe narrow-screen position. It competed with the host compose FAB, bottom navigation or publish controls.

PR [#31](https://github.com/pablo228sos/niyet-nsosyal/pull/31) made the mobile rule stricter:

- no standalone narrow-screen fallback while the composer is closed;
- one composer-attached DRSK action when the native composer opens;
- a full-width/bottom-sheet result on narrow screens;
- native publish and navigation remain untouched.

Reliability won over visual persistence.

## HUMAN and NONE stopped looking like SOURCECHAIN failures

A PID/control question should not show `SOURCECHAIN → INSUFFICIENT`. There is no factual claim to verify.

Likewise, “Dark mode looks better than light mode” is an opinion, not a failed evidence search.

The final classifier/UI keeps:

- pure contextual questions on `HUMAN`;
- subjective opinions on `NONE`;
- mixed posts split so subjective text does not enter evidence retrieval just because a factual sentence appears beside it.

## Evidence aggregation became claim-level

One claim can retrieve several candidate passages. An early reducer could downgrade an already-supported claim because another candidate was only partially supportive, which could trigger NIYET unnecessarily.

The final aggregation rule is claim-level:

- genuine conflict remains conflict;
- clean support closes that factual claim;
- extra partial candidates do not downgrade a closed claim;
- multi-claim posts remain partial until each factual claim is closed.

## Preview packaging exposed a real integration bug

A Preview extension build rewrote the API URL to a Vercel Preview deployment while its Manifest V3 host permission still pointed at Production. Chrome correctly blocked the request.

The packager now rewrites the backend URL, host permission and responder `/live` link together so one request cannot be split across Preview and Production state.

## Repeated checks were separated from human requests

The judge surface originally made stateful human requests too easy to create, which tied repeated checks to reset and responder capacity.

The final contract is:

- **Check with DRSK** = stateless `inspect`;
- checks do not consume human attention;
- **Ask a relevant person** = explicit `resolve`;
- `Prepare demo` exists only to restore canonical presentation state.

An API regression proves repeated private checks leave responder capacity unchanged.

## Real Chrome storage exposed another extension bug

A physical Chrome run produced:

`Access to storage is not allowed from this context.`

The extension now configures Manifest V3 session-storage access from the service worker and uses a local-storage fallback when session storage is unavailable. Returned answers can be restored rather than disappearing when the composer clears.

## The last two-device failure was view state

The Author card correctly routed coffee to Research Reviewer, but a same-page switch to Responder could leave a different demo identity selected. The inbox then looked empty.

The final stabilization follows the actual assigned responder before refreshing the inbox.

After an answer, switching back to Author also performs an immediate status refresh so the same post becomes `Resolved` with the exact human answer.

The accepted final round trip is:

~~~text
Prepare demo
-> coffee Check
-> BOTH / CONFLICTING / CAUSALITY_SHIFT
-> Ask a relevant person
-> Research Reviewer
-> Accept
-> Answer
-> Author Resolved
~~~

The separate responder-device link was verified in an independent browser session.

## Capacity telemetry had to follow request state

The last acceptance pass found one subtle mismatch after the core round trip was already working: accepting a request correctly reduced Research Reviewer capacity from 2 to 1 in the backend, but the Author card could continue displaying the pre-accept value until reload.

PR [#32](https://github.com/pablo228sos/niyet-nsosyal/pull/32) kept the state model unchanged and fixed only the view synchronization. When the polled request status changes, the Author surface refreshes responder state before rendering the new request state. Duplicate Accept still returns a guarded conflict and does not consume capacity twice.

The regression raised the final acceptance set to 73 targeted tests and 284 full-suite tests. Main CI and the merged Production deployment both passed.

## Final verification

- 73 targeted tests passed;
- 284 full-suite tests passed;
- JavaScript syntax checks passed;
- site build passed;
- extension package build passed;
- repeated-check capacity invariant passed;
- GitHub Actions passed;
- final Vercel Preview and merged Production deployment Ready.

The remaining presentation-hardware check is the authenticated real NSosyal desktop/mobile extension pass. The core `/live` flow is the judge-safe fallback.

## Deliberate non-features

Before the final we deliberately rejected:

- universal truth scores;
- hidden psychological/expertise profiling;
- automatic contact after a private check;
- browser buttons under every arbitrary foreign NSosyal post;
- heavy ModernBERT deployment only for appearance;
- a new chatbot/agent layer;
- allocator rewrites for cosmetic benchmark wins;
- Firebase as a dependency of the judge core.

The final system is narrower because every public claim should be supportable by code, data, tests or an explicit boundary.
