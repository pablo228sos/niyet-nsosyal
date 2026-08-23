# Safety and failure modes

NIYET is allowed to be wrong. The product should make a wrong suggestion easy to correct and should never turn model relevance into forced contact.

## Unwanted contact

A relevant user may still not want routed requests.

Current prototype controls:

- interaction type must be enabled for the responder
- responder can Skip
- responder can Pause within the current browser session
- no automatic direct message is sent

Production requirements:

- platform-level opt-in state
- block lists
- per-topic controls
- cooldowns and rate limits

## Responder overload

A small number of active responders can attract too many requests.

Current prototype controls:

- explicit remaining capacity
- batch allocation across competing requests
- Accept consumes a session slot
- Pause removes the responder from later session calls
- exhausted capacity removes the responder from the candidate graph

The current capacity state is a browser-session prototype, not a production database. A real deployment must persist capacity centrally so multiple devices and concurrent requests see the same state.

## False response detection

A response-needed model can make both kinds of mistakes.

False positive:

- author dismisses the NIYET suggestion

False negative:

- author can manually choose `Use NIYET anyway`
- a confirmed intent override activates routing even when the binary gate predicted NONE

## Bad expertise inference

Posting about a topic does not prove expertise.

Controls:

- responder profiles describe topics they are willing to receive, not verified expert status
- follower count is not treated as expertise
- no `expert` badge is inferred by NIYET
- future outcome history should only influence ranking after enough interactions exist

## Harassment and unsafe matching

Routing can create a new path for unwanted interaction.

Production requirements:

- blocked users can never be matched
- platform moderation rules run before routing
- report controls remain available on routed content
- repeated negative feedback can lower eligibility

The standalone prototype does not claim to reproduce NSosyal's complete moderation or abuse-prevention stack.

## Sensitive inference

Matching does not need health, politics, religion or other sensitive personal traits.

Rules:

- sensitive traits are not matching features
- use only the current request, broad opted-in topics and capacity state
- do not infer hidden personal profile attributes for routing
- document any future feature added to the candidate model

## Gaming the routing layer

A user may phrase promotional content as a help request to gain extra distribution.

Possible controls:

- response-needed gate
- per-author request limits
- spam and moderation signals
- skip and outcome feedback
- lower eligibility after repeated low-value routing

These are production safeguards unless explicitly implemented in the current prototype.

## Weak matches

A global optimizer cannot fix a poor candidate graph. If weak candidates enter allocation, it can increase coverage by distributing bad matches.

Current controls:

- retrieval before allocation
- minimum topic-relevance floor
- minimum edge utility
- dummy unmatched assignments
- full threshold-sensitivity experiment instead of reporting only the best-looking setting

## False sense of certainty

Similarity and development utility do not guarantee that someone will answer.

Controls:

- no `93% match` style probability in the user-facing UI
- technical values are marked as development diagnostics
- requests can remain unmatched
- offline relevance is never described as response probability

## Data minimization

The prototype needs only:

- request text
- confirmed intent
- broad responder topic profile
- interaction-type willingness
- current session capacity
- candidate similarity and utility

It does not require private messages, phone numbers, contact lists or sensitive inferred attributes.

## Product rule

Relevance can decide who is a candidate. Consent and available capacity decide whether routing is allowed.
