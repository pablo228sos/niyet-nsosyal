# DRSK / NIYET dataset card

## Purpose

The project uses two different text tasks and one matching task. They are kept separate because they answer different questions.

1. Response-needed gate: does this post actually ask for a human response?
2. Intent classification: if a response is requested, what kind of response is it?
3. Responder matching: how suitable is a specific responder for a specific open intent?

A single dataset should not be used to pretend that all three tasks are solved.

## Current language scope

The first evaluation scope is Turkish because the prototype is designed for NSosyal and the local-language component is important to the competition. The product interface is bilingual English/Turkish, but English UI support is not treated as English model evaluation.

## Response-needed gate

File: `data/response_gate_seed_v1.csv`

Labels:

- RESPONSE
- NONE

The negative class includes ordinary status updates, achievements, announcements and content that can receive replies but does not require one. This distinction matters because DRSK should not force every social post into a response-seeking workflow.

## Four-way intent set

File: `data/intent_seed_v1.csv`

Labels:

- ASK
- FEEDBACK
- COLLABORATE
- DISCUSS

The label describes the response the author is trying to obtain, not only the topic of the text.

### Challenge set

File: `data/intent_challenge_v1.csv`

The challenge set is kept separate from the cleaner development set. It contains shorter conversational wording, code switching, missing punctuation and examples closer to class boundaries.

Its purpose is not to inflate the training set. It is a stress test. A model that performs well only because the development sentences follow a clean repeated structure should lose performance here, which gives us a useful signal before the final report.

### Boundary cases

ASK vs FEEDBACK:

- ASK expects an answer, explanation or practical fix.
- FEEDBACK asks for evaluation of something the author made, wrote or decided.

ASK vs DISCUSS:

- ASK usually has a concrete information need.
- DISCUSS invites a broader exchange where several positions can be valid.

FEEDBACK vs DISCUSS:

- FEEDBACK is anchored to the author's artifact or decision.
- DISCUSS is about the topic itself.

COLLABORATE vs ASK:

- COLLABORATE asks another person to participate in ongoing work.
- ASK can be satisfied by a one-off answer.

## Source and provenance fields

Every annotation row keeps:

- `example_id`
- `text`
- `source_type`
- `source_group`
- independent labels when available
- `final_label`
- notes

Allowed development source types are documented in `docs/annotation.md`.

Controlled examples remain explicitly marked as controlled. We do not describe them as collected NSosyal posts.

## Leakage control

Near-duplicate examples can make a small classifier look much stronger than it is. Related paraphrases therefore share a `source_group`.

Model evaluation uses group-aware splitting. A group is assigned to either train or test, never both. This does not remove every possible source of leakage, but it prevents the most direct form caused by paraphrase variants crossing the split.

The challenge set uses separate source groups and is intended to remain outside model fitting when used as a stress test.

## Matching benchmark

File: `data/matching_review_template.csv`

The matching task uses intent-responder pairs. Relevance is rated on a four-point scale:

- 0: incompatible
- 1: weak
- 2: good
- 3: excellent

The review considers topic fit together with the type of interaction. A highly knowledgeable person who does not want that type of request should not automatically become a strong match.

Availability is kept separate from relevance. It is used by the allocator as an eligibility/capacity signal.

## Planned retrieval metrics

Candidate retrieval will be evaluated before global allocation.

Primary metrics:

- Precision@K
- NDCG@K
- Recall@K when the reviewed benchmark has enough relevant candidates per intent

Methods to compare:

1. lexical TF-IDF retrieval
2. Turkish embedding retrieval
3. optional hybrid retrieval if it improves the same fixed benchmark

The same reviewed intent/responder pool must be used for each retrieval method.

## Planned allocation metrics

After candidate retrieval, routing methods are compared using:

- intent coverage
- mean reviewed match relevance
- responder overload count
- responder load Gini
- total allocation utility
- runtime as batch size grows

Baselines:

1. random capacity-aware routing
2. topic-only routing
3. greedy pair-score routing
4. DRSK / NIYET global capacity allocation

## Annotation agreement

For the evaluation subset, two team members should label independently before discussing disagreements.

For categorical intent labels we can report Cohen's kappa when enough double-labeled examples are available.

For the 0-3 matching relevance scale, we will report raw agreement and can add weighted kappa after the first reviewed batch.

We will not invent an agreement score before the independent labels exist.

## Current limitations

- The current seed sets are controlled development data, not a representative sample of all NSosyal content.
- The challenge set is also team-written and measures robustness to harder phrasing, not real-world prevalence.
- The matching review sheet is still small and must be expanded before final retrieval claims.
- Language coverage outside Turkish is a product UI feature at this stage, not a validated NLP capability.
- Real resolution outcomes require real interactions. Until then, reviewed relevance is only a proxy for the likelihood of a useful match.

These limitations are part of the evaluation design rather than something to hide. They define what the technical report can and cannot claim at the current stage.
