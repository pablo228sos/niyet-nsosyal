# DRSK — Hybrid Social Intelligence Layer

DRSK combines evidence intelligence and human interaction intelligence in one social-feed flow:

```text
DRSK
├── SOURCECHAIN — claim, passage, provenance, relation and distortion
├── NIYET       — willing-human retrieval and capacity-aware allocation
└── Resolution  — EVIDENCE | HUMAN | BOTH | NONE | DEFERRED
```

**When evidence is enough, show the evidence. When it is not, find the right human.**

SOURCECHAIN never emits an absolute truth score. It preserves individual sources and conflicting passages. NIYET remains the tested interaction-allocation engine for posts that need a useful human response; it is reused through a structured escalation adapter rather than rewritten.

## Product flow

1. classify the statement and extract bounded, span-linked claims
2. rank passages from the controlled evidence provider
3. preserve URL, exact passage, location, hash and independent-origin metadata
4. align each claim with `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONFLICTING` or `INSUFFICIENT`
5. detect numeric, causality, certainty and attribution shifts
6. resolve to evidence, human help, both, none or deferred work
7. when needed, pass structured evidence context into NIYET retrieval, willingness, capacity and global allocation

Opinions stay outside factual verification. Missing evidence is reported as insufficient, not false. Arbitrary live URL fetching is intentionally disabled in the MVP.

## Live prototype

Prototype: https://niyet-nsosyal.vercel.app/

Allocation lab: https://niyet-nsosyal.vercel.app/lab

The web prototype calls the Python pipeline in `api/`. The current deployed path stays lightweight and reproducible:

- deterministic SOURCECHAIN statement/claim rules and controlled real-source corpus
- lexical passage ranking plus structured alignment and distortion checks
- immutable citation-first EvidenceBundles and an explicit DRSK resolution policy
- word and character TF-IDF with Logistic Regression for response-needed detection
- word and character TF-IDF with Logistic Regression for four-way intent classification
- weighted character TF-IDF for deployed responder retrieval
- explicit interaction willingness as a hard eligibility constraint
- session-level remaining responder capacity
- bounded global assignment across the current matching window

The browser keeps a small session state for the prototype and passes it to the API on each routing call. Accept decreases the matched responder's remaining capacity for later calls in that browser session. Pause removes the responder from subsequent allocation until resumed. This is a prototype session mechanism, not a production database.

The interface supports English and Turkish, including dynamic routing states. Desktop and mobile expose both the author and responder sides of the flow. The primary navigation is a small functional concept shell rather than a set of decorative controls.

ModernBERT-TR-Embed is evaluated offline as the leading Turkish semantic-retrieval candidate. It is not loaded into the public Vercel runtime yet because deployment cost and latency should be considered separately from retrieval quality.

## Allocation model

NIYET includes both a capacity-aware greedy baseline and a batch-level global allocator.

The allocator only sees candidates that already pass retrieval and eligibility checks. Willingness is therefore a hard constraint, not a ranking signal in the current implementation.

For an eligible edge, the current development utility is:

```text
utility = (topic relevance + availability) / 2
```

This is a transparent baseline. It is not a calibrated probability and the weights are not claimed to be learned or optimal.

Responder capacity is expanded into assignment slots. Dummy assignments allow an open request to remain unmatched instead of forcing a weak route. The minimum score threshold is applied before optimization.

The main prototype keeps multiple unresolved requests in a short matching window. When another request enters, the batch is allocated again under the same session capacity. This makes the shared-capacity behavior part of the product flow, not only a separate experiment.

## Data

`data/` contains:

- `response_gate_seed_v1.csv`: controlled RESPONSE / NONE development data
- `intent_seed_v1.csv`: controlled ASK / FEEDBACK / COLLABORATE / DISCUSS development data
- `intent_challenge_v1.csv`: shorter, conversational and code-switched Turkish examples
- `responder_profiles_v1.json`: synthetic responder profiles for the prototype
- `matching_benchmark_v1_draft.json`: original 32-query matching draft
- `matching_benchmark_v1_reviewed.json`: frozen human-reviewed benchmark
- `sourcebench_tr/`: small SOURCEBENCH-TR v0 statement/alignment/distortion development set
- annotation and review templates

Two team members independently reviewed all 256 query-responder relevance pairs. Exact agreement was 243/256 (94.92%) and quadratic weighted Cohen's kappa was 0.9756. The third team member adjudicated all 13 disagreements. The resulting `v1-reviewed` benchmark is now frozen. No participant names are stored.

## Current checks

Response-needed model on the repaired 96-row controlled set, four-fold grouped CV in the pinned environment:

- Accuracy: 0.917 +/- 0.030
- Macro F1: 0.915 +/- 0.030

Four-way intent baseline on the repaired 96-row controlled set, four-fold grouped CV in the pinned environment:

- Accuracy: 0.885 +/- 0.062
- Macro F1: 0.880 +/- 0.061

These replace dependency-drifted local checks; the exact NumPy, SciPy and scikit-learn versions used by CI are recorded in `constraints.txt`. The values remain controlled-development evidence, not population estimates.

Retrieval on the frozen 32-query x 8-responder human-reviewed benchmark:

| Retriever | Precision@3 | Recall@3 | NDCG@3 |
| --- | ---: | ---: | ---: |
| Weighted lexical TF-IDF | 0.4688 | 0.8438 | 0.8450 |
| ModernBERT-TR-Embed | **0.5417** | **0.9583** | **0.9025** |

The ModernBERT ranking order was produced by the fixed GitHub Actions experiment using the Yildiz Technical University COSMOS model. Final metrics above are computed against the frozen adjudicated human labels, not draft labels or copied model-card scores.

At lexical similarity floor 0.02 on the frozen labels, global allocation covers 78.12% of requests versus 65.62% for the capacity-aware greedy baseline and increases total reviewed relevance from 45 to 52. Mean assigned relevance is 2.08 for global versus 2.14 for greedy, showing the expected coverage-quality tradeoff rather than hiding it. At stricter floors the candidate graph becomes sparse and the two methods can converge to the same feasible assignments.

Human usability testing is documented separately. Eight real participants completed the initial six-task study, which exposed a mobile responder-side dead end. A five-session targeted retest after the responsive fix raised responder-control completion from 0/3 phone sessions to 2/2 mobile sessions. The remaining explainability-discoverability issue is kept explicit rather than presented as solved.

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
- `src/sourcechain/`: statement/claim analysis, controlled retrieval, alignment, distortion, lineage and EvidenceBundle assembly
- `src/drsk/`: resolution policy, NIYET adapter and end-to-end orchestrator
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
python -m pip install -c constraints.txt -e . pytest
pytest -q
python scripts/train_intent_baseline.py --cv
python scripts/train_intent_baseline.py data/response_gate_seed_v1.csv --cv
python experiments/evaluate_matching_draft.py
python experiments/benchmark_scaling.py
python scripts/validate_sourcebench.py data/sourcebench_tr
python scripts/serve_local.py
```

Semantic retrieval comparison requires the optional embedding dependencies and is intentionally kept outside the lightweight deployed runtime.

## Current limitations

- classification data are controlled development data
- SOURCEBENCH-TR v0 is a tiny team-authored regression set, not a definitive benchmark
- the default SOURCECHAIN corpus contains only a bounded verified demo source, not general web coverage
- arbitrary URL fetching and production evidence persistence are not implemented
- responder profiles are synthetic prototype profiles
- browser-session capacity is not a production persistence layer
- the semantic model is evaluated offline but is not yet the deployed Vercel retriever
- offline relevance is not the same as a real response or resolved interaction
- usability samples are small prototype studies, not population estimates

These limits are kept explicit because the current goal is a reproducible prototype whose claims match what is actually implemented.
