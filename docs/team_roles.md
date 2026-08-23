# Team responsibility split

The registered team has three members. The technical report should describe responsibilities without personal names or photos.

## Developer A: ML, data and evaluation

Primary ownership:

- response-needed classification
- four-way intent classification
- dataset structure and annotation protocol
- retrieval experiments
- benchmark design
- model metrics and error analysis
- dataset leakage checks

Cross-review:

- checks that model claims in the report match committed results
- explains model limitations and domain shift during the jury presentation

## Developer B: backend, optimization and integration

Primary ownership:

- candidate data model
- eligibility and attention constraints
- greedy allocation baseline
- global capacity-constrained allocation
- threshold and edge-case tests
- runtime pipeline and API
- CI and deployment integration
- scalability experiments

Cross-review:

- checks that the web prototype is using the same routing logic described in the report
- explains the assignment formulation, capacity slots and scaling limits during the jury presentation

## Product and UI/UX Designer

Primary ownership:

- NSosyal integration concept
- interaction flow from composer to responder preview
- English/Turkish interface
- visual system and component hierarchy
- accessibility decisions
- responsive behavior
- usability test protocol and design iteration
- presentation visuals and demo flow

Cross-review:

- checks that technical states are understandable without exposing misleading probabilities
- documents usability findings and the changes made after testing

## Shared responsibility

All three members review the final product and report in their own area before submission. The report is coordinated as one team document rather than assigned to a separate fictional role.

The team should be able to explain the complete product flow. Each member should also be able to answer detailed questions about the part they own.
