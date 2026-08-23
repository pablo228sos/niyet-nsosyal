# Safety and failure modes

NIYET is allowed to be wrong. The product flow should make a wrong match easy to ignore and should not turn model confidence into forced contact between users.

## Main risks

### Unwanted contact

A user may be relevant to a request but may not want to receive it.

Controls:
- responder routing is opt-in
- users can pause routing completely
- daily attention budget
- per-topic preferences
- accept/skip before a conversation starts
- cooldown after repeated skips

### Responder overload

The best-known responders can receive too many requests.

Controls:
- hard attention budgets
- batch allocation instead of independent top-1 routing
- load metrics
- cooldowns
- availability signal

### Bad expertise inference

Posting about a topic does not automatically make someone an expert.

Controls:
- use `capability` as a probabilistic signal, not a verified credential
- let users add/remove topics they are willing to help with
- use outcome history only after enough interactions exist
- do not show labels such as "expert" unless NSosyal has an independent verification process

### Harassment and unsafe matching

Routing can create a new path for unwanted interactions.

Controls:
- blocked users can never be matched
- safety/moderation filters run before allocation
- users can report a routed request
- no automatic direct message before the responder accepts
- repeated negative feedback can lower routing eligibility

### Sensitive inference

A model could infer health, politics, religion or other sensitive traits from posts even when matching does not need them.

Controls:
- do not use sensitive traits as matching features
- match on the text/topic needed for the current request
- keep the feature set documented
- avoid storing extra inferred profile attributes

### Gaming the system

Users may phrase ordinary promotional content as a help request to get extra distribution.

Controls:
- response-needed gate
- spam/moderation signals before routing
- per-author rate limits
- outcome and skip signals
- repeated low-value routing can reduce eligibility

### False sense of guaranteed help

A high match score does not mean a response will happen.

Controls:
- no promise of a guaranteed reply in the UI
- show routing as a suggestion
- allow an intent to remain unmatched when all candidates are weak

## Data minimization

The MVP does not need private messages, contact lists, phone numbers or sensitive profile fields.

For the prototype we only need:
- post text or a derived embedding
- confirmed intent type
- broad help topics
- responder opt-in and attention budget
- candidate scores
- outcome labels

A production integration should define retention periods and access rules with the platform team.

## Product safety rule

The allocator never bypasses user consent. Relevance decides who may be a good candidate. Consent decides whether an interaction can start.
