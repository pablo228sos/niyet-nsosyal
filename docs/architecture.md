# Architecture

NIYET is split into small stages so classification, retrieval and allocation can be tested independently.

## Live request path

1. The response-needed gate decides whether the post should enter NIYET.
2. If needed, the intent classifier suggests ASK, FEEDBACK, COLLABORATE or DISCUSS.
3. The author confirms or corrects the intent. A user can also activate NIYET manually when the gate misses a request.
4. Confirmed requests enter a short open-request matching window.
5. Responder retrieval creates a bounded candidate graph.
6. Hard eligibility checks remove inactive responders, exhausted capacity and unsupported intent types.
7. A minimum topic-relevance floor removes weak retrieval edges.
8. The remaining open requests are allocated together under shared responder capacity.
9. Accept, Skip and Pause update the browser-session prototype state used by later routing calls.

The main prototype and the Allocation Lab both call the Python allocation code. The Lab exposes controlled benchmark batches, while the main product keeps unresolved user requests in its own short matching window.

## Current candidate utility

Willingness is currently a hard eligibility constraint. A responder who does not accept an interaction type never reaches ranking.

For an eligible candidate edge, the development utility is:

```text
utility = (topic relevance + availability) / 2
```

`topic relevance` comes from the deployed lexical retrieval baseline.

`availability` is the responder's remaining session slots divided by the configured daily budget.

The value is a development utility, not a response probability. The equal weighting is deliberately simple until real outcome data exists.

## Capacity state

The competition prototype uses browser-session state rather than a production database.

The browser sends a responder-state object with each routing request. The API validates that state against the configured responder profiles and uses the remaining slots as allocation capacity.

- Accept reduces the matched responder's remaining slots for later calls in that browser session.
- Pause makes the responder inactive for later calls.
- Resume re-enables the responder when capacity remains.
- Skip excludes the current responder for that open request and triggers reallocation.

This is enough to demonstrate stateful shared capacity without claiming production persistence.

## Global allocation

A greedy allocator chooses the best available edge one at a time. That can be suboptimal when several requests compete for the same responders.

NIYET expands responder capacity into assignment slots and solves one bounded maximum-utility assignment across the current request window. Dummy assignments allow a request to remain unmatched instead of forcing a weak route.

Quality thresholds are applied before optimization. Invalid edges never influence the assignment matrix.

## Scaling boundary

We do not run one dense assignment over every NSosyal user.

The intended production sequence is:

```text
response gate
-> intent confirmation
-> candidate retrieval
-> eligibility and quality filtering
-> bounded allocation window
```

The current dense solver is suitable for small bounded windows. A larger production graph could use sparse min-cost flow or smaller topic/time buckets while preserving the same capacity and consent constraints.

## Outcome path

Accepted, Skipped, Useful and Resolved are useful future learning signals. The current live prototype implements routing-state actions, while long-term outcome storage and model calibration remain production work.
