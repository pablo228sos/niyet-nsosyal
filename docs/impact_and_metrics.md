# Impact and measurement

The project should separate what we want to improve from what we have already measured.

## Product outcomes

### Intent coverage

Share of open response-seeking intents that receive at least one eligible assignment.

This is the first coverage measure because a high average match score is not useful if many requests receive no opportunity at all.

### Relevant match rate

Share of routed assignments judged relevant above a chosen benchmark threshold.

### Time to first relevant response

For a live product test, measure the time from confirmed intent to the first response that the author marks useful or relevant.

### Intent resolution rate

Share of confirmed intents that the author later marks resolved.

This is a future live-product metric. We do not have real resolution data yet.

## Responder-side outcomes

### Responder load

Number of routed requests assigned to each responder in a window.

### Overload count

Assignments above the user's configured attention budget. The allocator should keep this at zero by construction.

### Load Gini

A concentration measure for how unevenly assignments are distributed across available responders.

A lower Gini is not automatically better. We should compare it together with relevance so we do not improve fairness by sending bad matches.

## Low-reach access

For a later product experiment we want to compare response opportunity by author reach bucket, for example:
- new account / very low reach
- low reach
- medium reach
- high reach

The core fairness question is whether a useful routing layer can reduce dependence on existing audience size without materially reducing relevance.

We do not currently have NSosyal follower-level experiment data. The technical report should describe this as an evaluation plan unless we collect a real test sample.

## Wider social value we can defend

NIYET may help with:
- access to community knowledge for users without an established audience
- collaboration discovery
- feedback discovery
- more deliberate use of responder attention

We should be careful with claims such as improved mental health, reduced addiction or improved national productivity. Those require evidence we do not have.

## Success condition for the core experiment

The allocation layer is useful if it can improve total assignment utility or intent coverage under fixed responder capacity without causing overload, and if that advantage still holds on a reviewed benchmark rather than only on a constructed example.

The final report should show both successful and failed/neutral comparisons. If global allocation does not beat a simpler baseline on a realistic benchmark, we should say so and explain when the extra optimizer is actually needed.
