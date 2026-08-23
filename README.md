# DRSK / NIYET

DRSK is our NSosyal project. NIYET is its interaction-allocation engine for posts that need a useful human response.

Most social feeds solve a content-ranking problem: which post should receive a user's attention? NIYET looks at the reverse problem: when several posts need a response, how should limited willing human attention be distributed across them?

## Product flow

1. detect whether a post needs a human response
2. suggest ASK, FEEDBACK, COLLABORATE or DISCUSS
3. let the author confirm or correct the intent
4. retrieve a bounded responder candidate set
5. apply intent willingness, active state and topic-quality filters
6. allocate open requests under shared responder capacity
7. let responders accept, skip or pause routing

Normal posts stay outside NIYET. A user can also activate NIYET manually if the response-needed gate misses a request.

## Live prototype

Prototype: https://niyet-nsosyal.vercel.app/

Allocation lab: https://niyet-nsosyal.vercel.app/lab

The web prototype calls the Python pipeline in `api/`. The current deployed path uses lightweight models that can be reproduced directly from this repository:

- word and character TF-IDF with Logistic Regression for response-needed detection
- word and character TF-IDF with Logistic Regression for four-way intent classification
- character TF-IDF for responder retrieval
- explicit interaction willingness as a hard eligibility constraint
- session-level remaining responder capacity
- bounded global assignment across the current matching window

The browser keeps a small session state for the prototype and passes it to the API on each routing call. Accept decreases the matched responder's remaining capacity for later calls in that browser session. Pause removes the responder from subsequent allocation until resumed. This is a prototype session mechanism, not a production database.

ModernBERT-TR-Embed is included as an optional offline Turkish semantic-retrieval candidate. We only treat it as a model choice after comparing it on the same fixed matching benchmark as the lexical baseline.

## Allocation model

NIYET includes both a capacity-aware greedy baseline and a batch-level global allocator.

The allocator only sees candidates that already pass retrieval and eligibility checks. Willingness is therefore a hard constraint, not a ranking signal in the current implementation.

For an eligible edge, the current development utility is:

```text
utility = (topic relevance + availability) / 2
```

This is a transparent baseline. It is not a calibrated probability and the weights are not claimed to be learned or optimal.

Responder capacity is expanded into assignment slots. Dummy assignments allow an open request to remain unmatched instead of forcing a weak route. The minimum score threshold is applied before optimization.

The main prototype now keeps multiple unresolved requests in a short matching window. When another request enters, the batch is allocated again under the same session capacity. This makes the shared-capacity behavior part of the product flow, not only a separate experiment.

## Data

`data/` contains:

- `response_gate_seed_v1.csv`: controlled RESPONSE / NONE development data
- `intent_seed_v1.csv`: controlled ASK / FEEDBACK / COLLABORATE / DISCUSS development data
- `intent_challenge_v1.csv`: shorter, conversational and code-switched Turkish examples
- `responder_profiles_v1.json`: synthetic responder profiles for the prototype
- `matching_benchmark_v1_draft.json`: 32-query responder-matching benchmark draft
- annotation and review templates

The matching benchmark remains marked `team_review_pending` until the registered team reviews and freezes the relevance labels. Development numbers are not presented as NSosyal field performance.

## Current development checks

Response-needed model on the controlled grouped development split:

- Accuracy: 0.917
- Macro F1: 0.916

Four-way intent baseline on the current grouped controlled data:

- Macro F1: about 0.872

Lexical retrieval on the draft 32-query matching benchmark:

- Precision@3: 0.4375
- Recall@3: 0.7969
- NDCG@3: 0.8079

The matching benchmark also exposes a real tradeoff between coverage and average match quality. We keep the full threshold sweep under `experiments/` instead of selecting only the setting where global allocation looks strongest.

## Evaluation

Routing methods:

1. random capacity-aware routing
2. topic-only routing
3. greedy pair-utility routing
4. NIYET global allocation

Main metrics:

- intent coverage
- reviewed match relevance
- Precision@K, Recall@K and NDCG@K
- responder overload
- responder-load concentration
- runtime as candidate batches grow

## Repository structure

- `src/niyet/`: classifiers, retrieval, scoring, allocation, metrics and runtime
- `api/`: deployed routing and experiment endpoints
- `data/`: development datasets, responder profiles and benchmark fixtures
- `experiments/`: reproducible evaluation and scaling checks
- `docs/`: architecture, data documentation, prior work, safety and product decisions
- `scripts/`: dataset and evaluation utilities
- `tests/`: unit and end-to-end runtime tests
- `web/`: bilingual product prototype and allocation lab

## Run locally

Python 3.11 or newer is required.

```bash
python -m pip install -e . pytest
pytest -q
python scripts/train_intent_baseline.py --cv
python scripts/train_intent_baseline.py data/response_gate_seed_v1.csv --cv
python experiments/evaluate_matching_draft.py
python experiments/benchmark_scaling.py
```

Optional semantic retrieval dependencies:

```bash
python -m pip install -e '.[embeddings]'
```

## Current limitations

- classification and matching data are controlled development data
- matching labels still need team review before they become a frozen evaluation set
- responder profiles are synthetic prototype profiles
- browser-session capacity is not a production persistence layer
- offline relevance is not the same as a real response or resolved interaction

These limits are kept explicit because the current goal is a reproducible prototype whose claims match what is actually implemented.
