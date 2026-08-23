# Prior work and novelty boundary

We should be precise about what is already known. NIYET is stronger if we show where it builds on existing work instead of claiming that every part is new.

## What already exists

### Social task routing

CrowdSTAR routes tasks to people in online communities using topic expertise and social availability. It was tested with Twitter and Quora. This is direct prior work for the idea of sending a question or task to a likely responder.

Source:
- Nushi, B., Alonso, O., Hentschel, M., Kandylas, V. Crowd-STAR: A Social Task Routing Framework for Online Communities, ICWE 2015.
- https://www.microsoft.com/en-us/research/publication/crowd-star-a-social-task-routing-framework-for-online-communities/

### Reciprocal recommender systems

Reciprocal recommenders treat people as the recommended entities and require compatibility from both sides. This is established research and is used in domains such as dating, recruitment, learning and social matching.

Source:
- Palomares, I., Porcel, C., Pizzato, L., Guy, I., Herrera-Viedma, E. Reciprocal Recommender Systems: Analysis of state-of-art literature, challenges and opportunities towards social recommendation. Information Fusion, 2021.
- https://www.sciencedirect.com/science/article/pii/S1566253520304267

### Popularity bias and long-tail exposure

Popularity bias is also established work. Recommendation algorithms can over-expose already popular items and reduce long-tail visibility. We should not claim that fairness toward low-reach content is a new problem.

Source:
- Klimashevskaia, A., Jannach, D., Elahi, M., Trattner, C. A survey on popularity bias in recommender systems, 2024.
- https://link.springer.com/article/10.1007/s11257-024-09406-0

## NSosyal product direction

NSosyal already uses AI for moderation and for reducing spam, bot accounts and manipulation attempts. Public statements also describe the platform as prioritizing real interaction instead of ad-driven profiling and manipulative engagement patterns.

This matters because NIYET should fit that product direction. We should not pitch it as a replacement for NSosyal's feed or existing moderation stack.

Sources:
- Anadolu Agency, 30 Dec 2025: NSosyal surpassed 1.7 million users after a major update.
- https://www.aa.com.tr/en/turkiye/turkish-social-media-platform-nsosyal-surpasses-17m-users-following-major-update/3785095

NSosyal also already has normal content and engagement features such as stories, replies, profile search, pinned posts and communities. Translation is not a new gap either. Turkish-English translation through DeepL was announced in 2025.

Sources:
- https://www.aa.com.tr/en/turkiye/new-features-added-to-turkish-social-media-platform-nsosyal/3780881
- https://nsosyal.com/post/104732633883316139
- https://nsosyal.com/post/131544928126791566

## What we should not claim

We should not write:
- "we invented intent-aware recommendation"
- "we invented reciprocal matching"
- "we are the first system to route questions to experts"
- "we solved popularity bias"
- "NSosyal has no recommendation or AI systems"

Those claims are too broad or false.

## NIYET's narrower contribution

Our current contribution is the combination of these ideas in one response-allocation layer for a social feed:

1. identify posts that actually seek a human response
2. retrieve a small set of relevant and willing responders
3. estimate pair utility
4. treat responder attention as a limited capacity
5. allocate that capacity across several open intents together instead of ranking every post independently
6. allow a low-quality intent to remain unmatched instead of forcing an assignment
7. collect outcome feedback such as useful or resolved for future matching

The main technical distinction we are testing is step 5. A normal top-1 or greedy router can make a good local choice that reduces total utility across the rest of the batch. NIYET's global allocator treats the candidate set as one constrained assignment problem.

## Comparison questions for the report

The final comparison table should answer these questions for each system or research line:
- Does it rank content or match people?
- Does it model whether both sides want the interaction?
- Does it model temporary availability?
- Does it have a hard capacity or attention budget?
- Does it allocate across a batch of open requests?
- Can it leave a request unmatched when all candidates are weak?
- Does it measure an interaction outcome instead of only exposure/clicks?
- Does it explicitly measure load concentration or fairness?

We need a source for every yes/no in the final table. Unknown should stay unknown instead of being guessed.
