# Safety and Failure Modes

DRSK and NIYET are allowed to be wrong. The product should make uncertainty and bad suggestions visible, recoverable and bounded rather than converting model relevance into forced contact or an unsupported truth verdict.

## Unwanted contact

A relevant user may still not want routed requests.

Current prototype controls:

- interaction type willingness is a hard eligibility constraint
- responder can Skip a request
- responder can Pause new routing
- no automatic direct message is sent
- exhausted capacity removes the responder from new allocation

Production requirements still include platform-level identity/consent, block lists, per-topic controls, cooldowns and rate limits.

## Responder overload

A small number of active responders can attract too many requests.

Current controls:

- explicit finite responder capacity
- bounded global allocation across competing open requests
- Accept consumes one slot exactly once
- accepted requests remain pinned
- Pause removes the responder from new allocation
- exhausted capacity removes the responder from the candidate graph
- stale concurrent actions are rejected instead of double-consuming capacity

Mutable state lives behind `StateStore`. Local development uses a process-local memory backend; a durable shared demo can use the Upstash Redis REST backend with compare-and-set mutations. The UI reports which state mode is active.

This state layer demonstrates shared-capacity semantics; it is not a replacement for production identity, authorization or abuse controls.

## Concurrent/stale UI actions

Two devices can act on an allocation window that has already changed.

Controls:

- the backend validates that the request is still assigned/open before Accept or Skip
- durable-state mutations use compare-and-set and bounded retries
- stale assignment/capacity conflicts return `409`
- the responder UI refreshes the current queue after a conflict
- temporary durable-store failure returns `503` rather than silently falling back to stale state

## False response detection

A response-needed model can make both kinds of mistakes.

False positive:

- the system should stay dismissible / avoid forcing human routing

False negative:

- the author can explicitly request a person
- the human-help path does not require pretending the response gate is always correct

## Evidence insufficiency

SOURCECHAIN can fail to retrieve a relevant controlled passage.

Controls:

- missing evidence is `INSUFFICIENT`, not false
- unrelated passages are not presented as proof
- the resolution layer may remain `DEFERRED` or enter `HUMAN` when a person is explicitly requested
- the product does not invent a citation to make the flow look complete

## Claim/evidence distortion

A post may strengthen, narrow, broaden or numerically change what a source says.

Current typed checks include numeric, temporal, causality, certainty, scope and attribution shifts.

Controls:

- preserve the exact stored passage
- preserve the original source URL and provenance
- show the typed difference as a signal, not a truth score
- use `BOTH` when evidence is useful but human interpretation is still warranted

The current Distortion Lens is single-hop claim↔evidence comparison; it does not claim arbitrary repost-chain reconstruction.

## Bad expertise inference

Posting about a topic does not prove expertise.

Controls:

- responder profiles describe opted-in topics/willingness, not verified expert status
- follower count is not treated as expertise
- no hidden `expert` badge is inferred
- synthetic responder profiles are labeled as prototype fixtures

## Harassment and unsafe matching

Routing creates a path for unwanted interaction.

Production requirements:

- blocked users can never be matched
- platform moderation rules run before routing
- report controls remain available on routed content
- repeated negative outcomes can influence future eligibility only after a measured policy is defined

The standalone prototype does not claim to reproduce NSosyal's full moderation or abuse-prevention stack.

## Sensitive inference

Matching does not require health status, politics, religion or other sensitive personal traits.

Rules:

- sensitive traits are not matching features
- use the current request, broad opted-in responder topics, willingness and capacity
- do not infer hidden personal attributes for routing
- document and review any future feature added to the candidate model

## Gaming the routing layer

A user may phrase promotional content as a help request to gain distribution.

Possible production controls include response-needed gating, per-author request limits, moderation/spam signals, skip/outcome feedback and rate limits. These are not claimed unless explicitly implemented.

## Weak matches

A global optimizer cannot repair a poor candidate graph.

Current controls:

- retrieval before allocation
- hard willingness/activity/capacity constraints
- minimum topic-relevance floor
- minimum edge utility
- dummy unmatched assignments
- threshold-sensitivity evaluation instead of reporting only a favorable setting

## False sense of certainty

Similarity and development utility do not guarantee that someone will answer, and evidence relation does not equal universal truth.

Controls:

- no `93% match` style probability in the user-facing UI
- development utility is not described as response probability
- requests can remain unmatched
- offline relevance is not described as real-world resolution probability
- SOURCECHAIN emits evidence relations and typed signals rather than an absolute truth score

## Data minimization

The integrated prototype needs only bounded fields such as:

- request text
- explicit/derived interaction intent
- broad responder topic profile
- interaction-type willingness
- active state and remaining capacity
- candidate similarity/utility
- bounded evidence passage/provenance when SOURCECHAIN is used
- request lifecycle state and responder answer

It does not require phone numbers, contact lists, private-message history or sensitive inferred traits.

## Product rule

**Relevance decides who may be a candidate. Willingness and available capacity decide whether routing is allowed. Evidence provenance decides what can be shown. Missing evidence never becomes fabricated certainty.**
