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

The repository currently has two allocation methods. The first is a greedy capacity-aware baseline. The second solves the candidate set as one assignment problem, so using the strongest responder for one intent does not accidentally leave another intent with a very weak match.

Each candidate match has a relevance score, a willingness score and an expected response score. Each responder also has a daily attention limit. Both methods respect those limits. The global method is still an early prototype and will be tested on a larger human-reviewed benchmark before we treat it as a project result.

## Planned evaluation

We plan to compare:

1. random routing
2. topic similarity only
3. greedy best-match routing
4. capacity-aware pair-score routing
5. NIYET global allocation

The main product metrics are intent coverage, relevant match rate and responder load concentration. Model metrics will be added once the intent classifier and matching benchmark are ready.

## Project status

Early prototype. The dataset, model validation and UI are still in development.
