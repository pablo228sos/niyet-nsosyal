# DRSK Architecture

DRSK is a hybrid social-intelligence layer with two independently testable engines and one explicit resolution layer.

```text
post
  |
  v
SOURCECHAIN
  | statement -> claim -> controlled passage -> provenance -> relation -> distortion
  v
EvidenceBundle
  |
  v
Resolution Engine
  | EVIDENCE ------------------------------> evidence response
  | NONE ----------------------------------> no intervention
  | DEFERRED ------------------------------> explicit recoverable gap
  | HUMAN / BOTH
  v
NIYET
  | response intent -> responder retrieval -> hard eligibility
  | -> bounded global allocation under shared capacity
  v
HumanHelpService
  | OPEN / UNMATCHED -> ACCEPTED -> ANSWERED
  |          \-> reallocation on window/state changes
  v
original request receives evidence and/or human context
```

## Ownership

- `sourcechain` owns statement analysis, claim extraction, controlled evidence retrieval, exact passage provenance, claim/evidence alignment and typed distortion checks.
- `niyet` owns response/intent classification, responder retrieval, willingness/active/capacity eligibility, pair utility and greedy/global allocation.
- `drsk` owns the resolution policy, SOURCECHAIN→NIYET adapter, human-help request lifecycle and state-store abstraction.
- `api` owns bounded transport validation and public error semantics.
- `web` renders structured state; it does not own allocation truth or responder capacity.

Neither engine treats a score as a probability of truth. Missing evidence means insufficient evidence, not a false claim. Conflicting passages remain visible as individual evidence items.

## Evidence contracts

An `EvidenceItem` preserves at minimum:

- HTTP(S) source URL and canonical URL
- exact plain-text passage and passage location
- publisher/publication metadata when available
- retrieval timestamp and document hash
- claim/evidence relation
- typed distortion signals
- origin-cluster identifier

An `EvidenceBundle` is versioned and deterministic. Explanations may cite only evidence IDs that exist inside the bundle.

The resolution paths are:

- `EVIDENCE` — bounded evidence is sufficient and non-conflicting for the current path.
- `HUMAN` — evidence is insufficient and human help is explicitly requested.
- `BOTH` — evidence is useful but conflict/distortion or interpretation still warrants a human route.
- `NONE` — the post is subjective/non-checkable or otherwise needs neither layer.
- `DEFERRED` — a recoverable evidence operation is unavailable or intentionally postponed.

## NIYET allocation invariants

Eligibility is enforced before global optimization. A responder must be active, willing for the intent, above the relevance floor and have remaining capacity.

Open requests are allocated as one bounded window rather than independently. Responder capacity is expanded into finite assignment slots; dummy assignments allow a request to remain unmatched instead of forcing a weak route.

Human-help lifecycle invariants:

- accepted requests remain pinned to the accepting responder
- Accept consumes one responder slot exactly once
- still-open or unmatched requests are reallocated together after relevant state changes
- Skip excludes the current responder for that request and triggers reallocation when alternatives exist
- Pause removes the responder from new allocation; Resume restores eligibility only when capacity remains
- stale UI actions are rejected as conflicts instead of mutating a newer allocation state
- no transition may drive capacity below zero

The current utility is a transparent development baseline rather than a learned probability.

## Mutable-state boundary

`src/drsk/state_store.py` isolates mutable demo state behind a small transactional interface:

```text
read() -> snapshot
mutate(fn) -> atomic/serialized state transition
reset(state)
```

Two implementations are available:

- `MemoryStateStore` — thread-safe, process-local fallback for tests and local development.
- `UpstashRedisStateStore` — optional durable Redis REST backend using compare-and-set Lua mutations, TTL and bounded conflict retries.

The domain service does not know Redis commands. This keeps request/allocation logic testable and lets the deployment backend change without rewriting NIYET or DRSK contracts.

When durable state is not configured, the public health surface reports the fallback honestly; the UI does not claim multi-device durability.

## API failure semantics

Transport errors are separated from domain/state conflicts:

- malformed/invalid input → `400`
- invalid author token → `403`
- missing request/entity → `404`
- stale assignment or concurrent state conflict → `409`
- temporary durable-state backend failure → `503`

Internal storage errors are not exposed verbatim to the browser.

## Security boundary

The current SOURCECHAIN path can use server-side Tavily/Brave provider clients as bounded candidate-evidence sources; the browser does not receive provider credentials and does not expose an arbitrary URL-fetch proxy. Retrieved text is treated as untrusted candidate evidence and still passes SOURCECHAIN relevance, passage, relation and distortion logic. Any future direct document-fetch layer must independently enforce scheme/DNS/IP validation, redirect checks, private/link-local/metadata blocking, timeouts, byte/decompression limits, MIME restrictions and sanitization.

API bodies, post text and answer text are bounded before analysis. Evidence passages are rendered as text, and source links originate from validated bundle provenance.

The current shared-state layer is a prototype state mechanism, not an authentication system. Production identity, authorization, abuse controls and rate limiting remain separate requirements.

## Replaceable baselines

Statement rules, lexical retrieval and structured alignment are transparent baselines behind stable contracts. They can be replaced by measured Turkish models without changing provenance, EvidenceBundle, Resolution or human-allocation semantics.
