# Product flow

NIYET is designed as a small extension of posting and replying, not as a separate matching application.

## 1. Author writes a normal post

The user writes in the existing composer.

The response-needed model runs first.

If the post looks like a normal update, NIYET stays out of the flow. The interface still offers a small manual `Use NIYET anyway` path so a false negative does not block the user.

If the post appears to seek a response, NIYET suggests one of four intents:

- ASK
- FEEDBACK
- COLLABORATE
- DISCUSS

The author can accept the suggestion, change it or dismiss NIYET.

## 2. Confirmed request enters the matching window

A confirmed request joins the current open-request window.

The window matters because several requests can compete for the same willing responders. NIYET does not immediately lock the locally best responder for every request independently.

Candidate retrieval first narrows the pool.

Before allocation, the runtime removes:

- inactive responders
- responders with no remaining session capacity
- responders who do not accept the confirmed intent type
- responders explicitly skipped for this request
- candidates below the current topic-relevance floor

## 3. Requests are allocated together

When a new confirmed request enters the window, the current unresolved requests are allocated again under one shared responder state.

This is the product-level reason for the global allocator. If two requests both prefer the same responder but one has a strong alternative and the other does not, batch allocation can use the scarce responder where it matters more.

A request may stay unmatched when no valid candidate clears the quality rules.

## 4. Responder sees a request card

The routed request appears as a suggestion, not as an automatic direct message.

The prototype shows:

- original request text
- confirmed intent type
- matched responder profile
- plain-language match reasons
- Accept
- Skip
- Pause routing

Development similarity and utility values are hidden behind Technical details and are clearly labeled as diagnostics, not probabilities.

## 5. Responder actions change later allocation

The live prototype keeps a small browser-session state.

### Accept

Accept decreases that responder's remaining slots for later routing calls and removes the current request from the open window.

### Skip

Skip excludes the current responder from that request and reallocates the remaining window. It does not consume capacity.

### Pause

Pause makes the matched responder inactive in later routing calls within the session. Resume re-enables the responder if capacity remains.

This session mechanism demonstrates stateful capacity. A real production integration would move the same state into platform storage rather than relying on the browser.

## 6. Interaction stays in normal NSosyal surfaces

If a responder accepts, the actual conversation can continue in the normal reply or messaging surface. NIYET does not need to create a second social network.

## 7. Outcome feedback

Useful and Resolved are intended future learning signals. The current prototype demonstrates routing-state actions, while persistent long-term outcome collection remains production work.

## Correction points

The interface is designed so model mistakes are recoverable:

- false positive response detection: dismiss NIYET
- false negative response detection: manually activate NIYET
- wrong intent: change it before routing
- poor responder: Skip and reallocate
- too many requests: Pause routing
- exhausted attention: capacity reaches zero for later session calls

## Accessibility requirements

- keyboard access for every action
- visible focus state
- semantic button and form labels
- no critical state communicated by color alone
- screen-reader status announcements
- reduced-motion support
- responsive desktop and mobile layouts
- no forced time limit for accepting a request

## Usability test tasks

The prepared usability test checks whether a participant can:

1. publish a normal update without accidentally activating NIYET
2. route a help-seeking post
3. correct the suggested intent
4. manually activate NIYET after a normal-post decision
5. accept or skip a routed request
6. pause incoming routing
7. understand why a match was suggested

We record task completion, time, wrong clicks, facilitator hints and the main point of confusion. Results are only reported after real participants complete the protocol.
