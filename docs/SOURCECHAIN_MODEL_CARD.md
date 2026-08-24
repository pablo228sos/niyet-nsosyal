# SOURCECHAIN MVP Model Card

## Intended use

SOURCECHAIN is a development prototype for checking whether a Turkish or English social post contains a bounded factual claim, comparing it with supplied evidence passages, and exposing support, conflict, insufficiency and typed wording shifts. It is not an automated truth oracle or moderation system.

## Components

- deterministic statement/check-worthiness gate;
- span-linked sentence/coordination claim extraction;
- controlled evidence-provider interface and lexical passage ranking;
- lexical, negation and structured number/certainty/causality checks;
- evidence aggregation with citation-first templates;
- source-attribution mismatch and parent-to-child Distortion Lens baselines.

No generative model invents sources, passages or explanations. Explanations are assembled from verified evidence IDs and typed findings.

## Output meaning

`SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONFLICTING` and `INSUFFICIENT` describe the relationship between a claim and the retrieved passage set. They do not express an absolute truth score. Confidence-like internal similarity values are development diagnostics only.

## Limitations

Rules can miss paraphrases, idioms, implicit negation, complex Turkish morphology and domain-specific numeric units. A controlled corpus cannot establish broad external coverage. Evidence quality, recency and publisher reliability are not inferred from URL appearance. SOURCECHAIN must defer or report insufficiency when provenance or coverage is inadequate.

## Safety

Arbitrary network retrieval is intentionally not enabled in the sprint MVP. Active HTML is not stored as a user-facing passage. Downstream interfaces must use text-safe rendering and preserve the supplied citation URL.

## Evaluation

The committed SOURCEBENCH-TR v0 set is a small, team-authored development set for regression behavior only. It is not large enough for statistically definitive performance claims. Future evaluation needs independent annotation, grouped event/source splits, hard negatives, per-class precision/recall/F1 and distortion-specific slices.
