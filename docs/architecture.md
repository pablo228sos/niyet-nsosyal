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

## Global allocation prototype

A greedy allocator can make a locally good choice that hurts the rest of the batch. For example, one responder may be the best match for two intents while a second responder is almost as good for only one of them. Assigning the first responder too early can waste the second intent.

The current global prototype expands each responder into a number of slots equal to their attention budget and solves one maximum-utility assignment across the batch. Dummy slots allow an intent to stay unassigned when no candidate passes the minimum score.

This step works after candidate retrieval. It is not meant to compare every user with every open intent on the platform. A production version would first retrieve a small candidate set, then run allocation on that set.
