# NIYET Allocation Architecture

This document focuses on the NIYET human-routing subsystem. The full DRSK evidence + resolution architecture is documented in [`DRSK_ARCHITECTURE.md`](DRSK_ARCHITECTURE.md).

## Final integrated request path

1. DRSK decides that human help is needed (`HUMAN` or `BOTH`) or the user explicitly asks a person directly.
2. The request enters `HumanHelpService` with structured context.
3. NIYET builds a bounded responder candidate graph.
4. Hard eligibility removes responders who are inactive, exhausted, unwilling for the intent, explicitly skipped or below the relevance floor.
5. Every still-open/unmatched request in the current window is allocated together under the same responder capacity state.
6. The assigned responder may Accept, Skip or Pause routing.
7. Accepted requests are pinned and consume one slot exactly once.
8. State changes trigger reallocation of still-open/unmatched requests.
9. A stale action from an older UI snapshot is rejected as a conflict; the client refreshes instead of mutating newer state.
10. After Accept, the responder can submit an answer that returns to the original request.

The final product path keeps allocation truth in the server-side domain service, not in browser-provided capacity objects.

## Candidate eligibility

Willingness is a hard eligibility constraint. A responder who has not opted into an interaction type never reaches ranking.

An eligible responder must also be:

- active
- above the topic-relevance floor
- below their capacity limit / have remaining slots
- not excluded by a prior Skip for this request

Follower count is not an eligibility or expertise signal.

## Current pair utility

For an eligible edge, the development utility is:

```text
utility = (topic relevance + availability) / 2
```

`topic relevance` comes from the deployed lexical retrieval baseline.

`availability` is derived from remaining capacity relative to the configured budget.

The value is a transparent development utility, not a response probability. Equal weighting is intentionally simple until real outcome data supports calibration.

## Global allocation

Greedy routing can consume a scarce responder on an early request even when another request has no good alternative.

NIYET expands responder capacity into assignment slots and solves one bounded maximum-utility assignment across the current open window. Dummy assignments let a request remain unmatched instead of forcing a weak route.

Quality thresholds are applied before optimization. Invalid edges never enter the assignment matrix.

## Shared mutable state

The integrated path uses `HumanHelpService` plus the `StateStore` abstraction.

Two state backends exist:

- `MemoryStateStore` — thread-safe process-local fallback for tests/local development
- `UpstashRedisStateStore` — optional durable shared backend using compare-and-set Lua mutations and TTL

The domain service owns request lifecycle, responder capacity and exclusions. Browsers only send actions and identifiers; they do not get to submit authoritative capacity values for the integrated flow.

### Accept

Accept validates that the request is currently assigned to that responder and still open. It consumes one remaining slot, pins the request to that responder and then reallocates other pending requests.

### Skip

Skip adds the responder to the request's exclusions without consuming capacity, then reallocates the pending window.

### Pause / Resume

Pause removes the responder from new routing. Resume restores active eligibility only when remaining capacity is positive.

### Answer

Only the responder who accepted the request can answer it. The answer is attached to the same request record and becomes visible to the author path.

## Concurrency behavior

With the durable backend, each mutation reads a snapshot, applies one domain transition and publishes it only if the snapshot has not changed. Conflicting writers retry within a bounded limit.

At the API boundary:

- stale allocation/action conflicts → `409`
- temporary shared-state backend failure → `503`

This keeps concurrency failure explicit instead of silently double-consuming capacity.

## Scaling boundary

NIYET does not solve one dense assignment over every user on the platform.

The intended sequence is:

```text
response need / explicit human request
-> candidate retrieval
-> willingness + activity + capacity + quality filtering
-> bounded request window
-> capacity-constrained allocation
```

The current dense solver is appropriate for small bounded windows. Larger production graphs could use sparse min-cost flow or topic/time buckets while preserving the same willingness and capacity contracts.

## Outcome boundary

The prototype implements request opening, allocation, Accept, Skip, Pause/Resume and Answer. Long-term outcome history, authenticated identities and learned utility calibration remain production work.
