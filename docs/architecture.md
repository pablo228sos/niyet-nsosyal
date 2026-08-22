# Architecture notes

The first version separates the system into five steps.

1. Detect whether a post is asking for a response and assign an intent type.
2. Retrieve a small set of potentially relevant responders.
3. Score each intent-responder pair in both directions.
4. Allocate limited responder attention across open intents.
5. Record the outcome after the interaction.

We keep intent detection and allocation separate on purpose. This lets us test whether a better allocation strategy helps even before the classifier is mature.

## Pair score

The first baseline uses three factors:

- topic relevance
- responder willingness
- expected response probability

The score is only used for ordering candidate edges. Capacity is handled by the allocator, not hidden inside the score.

## Constraints

The initial allocator respects one hard constraint: a responder cannot receive more assignments than their attention budget.

The next version will add:

- opt-in and blocking rules
- minimum compatibility threshold
- repeat-invitation cooldown
- fairness penalty for repeated exposure

## Outcome signal

The target product signal is not a click. We want to collect whether the interaction was useful or resolved the original intent. That outcome can later become a training label for the matching model.
