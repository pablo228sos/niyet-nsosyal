# NIYET

NIYET is an experimental interaction allocation layer for NSosyal.

Most social feeds decide which content should receive a user's attention. NIYET looks at the opposite side of the problem: when a post needs a response, where should limited willing human attention go?

The first prototype focuses on four response-seeking intents:

- ASK: a user needs an answer or practical help
- FEEDBACK: a user wants an opinion on something they made or wrote
- COLLABORATE: a user is looking for someone to work with
- DISCUSS: a user wants a real discussion around a topic

The current work is intentionally narrow. We are first testing whether capacity-aware reciprocal matching can cover more open intents without overloading the same responders. We will add model-based retrieval after the allocation logic and evaluation setup are stable.

## Current prototype

The repository starts with a small deterministic allocation core. Each candidate match has a relevance score, a willingness score and an expected response score. Each responder also has a daily attention limit. The allocator assigns responders to open intents while respecting those limits.

This is not the final ranking model. It is a baseline we can test and replace.

## Planned evaluation

We plan to compare:

1. random routing
2. topic similarity only
3. greedy best-match routing
4. NIYET capacity-aware allocation

The main product metrics are intent coverage, relevant match rate and responder load concentration. Model metrics will be added once the intent classifier and matching benchmark are ready.

## Project status

Early prototype. The dataset, model validation and UI are still in development.
