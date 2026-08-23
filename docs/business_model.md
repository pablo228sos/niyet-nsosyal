# Business and sustainability notes

NIYET is designed as a platform capability inside NSosyal. We do not plan to charge ordinary users to receive a useful reply. Putting the core matching layer behind a paywall would work against the product goal.

## Platform value

The main value to NSosyal is product-side:
- more useful interaction around response-seeking posts
- better use of willing responder attention
- another reason for low-reach users to publish questions, feedback requests and collaboration posts
- measurable outcome signals beyond views and likes

These are hypotheses that need product testing. We should not turn them into revenue claims before data exists.

## Possible commercial layer

A later B2B layer could support verified institutional response pools.

Examples:
- a university opens weekly mentoring capacity for student questions
- a technology company offers a limited engineering Q&A pool
- an NGO routes volunteering or collaboration requests to opted-in members
- a municipality routes selected community questions to verified teams

Possible paid tools for an institution:
- verified pool management
- responder scheduling and attention limits
- aggregate response analytics
- topic configuration
- service-level monitoring for the institution's own pool

Ordinary user-to-user routing remains independent from paid placement. An institution should not be able to buy a higher personal match score.

## Why this is a better business fit than ads

An advertising model is not necessary to prove NIYET's sustainability and could conflict with NSosyal's public positioning around non-manipulative interaction. For the competition report we should keep the business model narrow and platform-aligned instead of inventing an ad marketplace.

## Cost structure

Main technical costs would come from:
- embedding inference
- candidate retrieval storage/indexing
- allocation compute
- outcome logging
- moderation and abuse handling

The current architecture reduces cost by retrieving a small candidate set before allocation. We also plan to test a Turkish 150M embedding model that can be hosted locally instead of requiring a closed external embedding API.

We should add measured inference numbers before the final presentation. We should not invent per-user or monthly infrastructure costs in the technical report.

## Technical sustainability

- separate retrieval and allocation modules
- replaceable embedding model
- documented feature set
- reproducible benchmarks
- outcome labels for later retraining
- bounded allocation queues instead of one network-wide solver

## Social sustainability

Responder supply is not unlimited. The system therefore needs:
- opt-in routing
- attention budgets
- pause controls
- cooldowns
- no automatic direct messages
- a way to reduce irrelevant requests

A matching system that burns out its best responders is not sustainable even if its relevance score is high.

## Partnerships that make sense

Potential partnerships should provide response capacity or technical infrastructure, not merely logos:
- universities and student communities
- technical communities
- public-interest organizations
- Turkish NLP research groups
- cloud or inference providers

Any partnership mentioned in the report should be described as a potential partnership unless we actually have an agreement.
