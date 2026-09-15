# Product Flow

DRSK is designed to feel like part of a social feed, not a separate AI dashboard or expert marketplace.

## 1. A user writes a normal post

The composer accepts a question, claim or idea. DRSK first decides whether the post contains a check-worthy factual statement and whether human help is being requested.

A subjective post can remain outside both systems. A factual statement can enter SOURCECHAIN. A direct request for help can enter NIYET even when there is no useful evidence path.

## 2. SOURCECHAIN exposes bounded evidence

For check-worthy statements, SOURCECHAIN extracts bounded claims and searches only the configured controlled evidence corpus.

The product keeps visible:

- exact passage text
- source title and canonical URL
- publisher/publication metadata when available
- claim/evidence relation
- typed wording/distortion signals

It does not convert these fields into an absolute truth score.

If no relevant stored passage exists, the result stays `INSUFFICIENT` rather than inventing a source.

## 3. Resolution Engine chooses the path

The explicit resolution paths are:

- `EVIDENCE` — the bounded evidence is sufficient for the current path
- `HUMAN` — evidence is insufficient and a person is explicitly requested
- `BOTH` — useful evidence exists but conflict/distortion/interpretation still warrants a human response
- `NONE` — no evidence or human intervention is appropriate
- `DEFERRED` — a recoverable dependency/evidence operation is unavailable or postponed

This keeps uncertainty visible instead of forcing every post through one model response.

## 4. Structured context enters NIYET

When the path needs a person, DRSK sends NIYET structured context rather than only the raw post:

- topic
- claim text
- evidence status
- distortion types
- requested resolution

NIYET then retrieves responders and applies hard eligibility constraints.

A responder must be active, willing for the interaction type, have remaining capacity and clear the current relevance floor. Follower count is not used as an eligibility signal.

## 5. Open requests compete in one bounded allocation window

NIYET does not permanently lock the locally best responder independently for each request.

Every still-open/unmatched request is allocated together under the same responder capacity state. This matters when two requests both want a scarce responder but only one has a strong alternative.

A request can remain unmatched when no eligible candidate clears the quality rules.

## 6. Responder receives an actionable request card

The responder side shows the request, attached evidence context when present, remaining capacity and controls to:

- Accept
- Skip
- Pause / Resume routing
- Answer after acceptance

### Accept

Accept is server-authoritative. It validates the current assignment, consumes one slot exactly once, pins the request to that responder and reallocates other pending requests.

### Skip

Skip excludes the current responder for that request without consuming capacity, then reallocates the pending window.

### Pause / Resume

Pause removes the responder from new allocation. Resume re-enables routing only when capacity remains.

If the UI is stale because another action already changed the shared window, the backend rejects the action as a conflict and the client refreshes the current queue.

## 7. Answer returns to the same request

After acceptance, the matched responder can submit a concise answer. The author path polls the same request state and displays the answer next to the evidence context.

The product story therefore stays one journey:

```text
need
-> evidence when useful
-> human when needed
-> shared outcome
```

## 8. State persistence boundary

The integrated human-help flow is implemented behind a `StateStore` abstraction.

- local/tests: process-local `MemoryStateStore`
- durable multi-instance demo: optional Upstash Redis REST backend with compare-and-set mutations and TTL

The UI reports whether durable shared state is actually configured. It does not claim cross-device durability when running on the memory fallback.

## Correction points

The system is intentionally recoverable:

- subjective/non-checkable post → `NONE`
- no controlled evidence → `INSUFFICIENT`, not false
- evidence wording differs → preserve the passage and expose the typed difference
- weak responder candidate → remain unmatched
- poor route → Skip and reallocate
- responder overloaded → capacity reaches zero and removes them from eligibility
- responder unavailable → Pause
- stale client action → reject with conflict and refresh

## Accessibility requirements

- keyboard access for every action
- visible focus state
- semantic buttons and form labels
- no critical state communicated only by color
- screen-reader status announcements for routing changes
- reduced-motion support
- responsive author and responder layouts
- no forced time limit for accepting a request

## Usability boundary

Prototype usability studies are small. They are useful for finding interface failures, but they are not population estimates. Product claims should remain tied to the observed prototype tasks rather than generalized to all NSosyal users.
