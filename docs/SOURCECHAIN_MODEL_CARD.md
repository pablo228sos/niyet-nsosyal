# SOURCECHAIN MVP Model Card

## Intended use

SOURCECHAIN is a development prototype for checking whether a Turkish or English social post contains a bounded factual claim, comparing it with supplied evidence passages, and exposing support, conflict, insufficiency and typed wording shifts. It is not an automated truth oracle or moderation system.

## Components

- deterministic statement/check-worthiness gate;
- span-linked sentence/coordination claim extraction;
- pluggable evidence-provider boundary with lexical passage ranking;
- deterministic verified-corpus provider for offline/reproducible behavior;
- verified-first live evidence cascade: Tavily basic behind a quality gate, Tavily advanced when needed, optional Brave fallback;
- lexical, negation and structured number/certainty/causality checks;
- evidence aggregation with citation-first templates;
- source-attribution mismatch and parent-to-child Distortion Lens baselines.

No generative model invents sources, passages or explanations. Live providers supply candidate URLs/passages only; SOURCECHAIN still owns passage ranking, claim/evidence relations, typed distortions and the decision to stay `INSUFFICIENT`. Explanations are assembled from evidence IDs and typed findings.

## Output meaning

`SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONFLICTING` and `INSUFFICIENT` describe the relationship between a claim and the retrieved passage set. They do not express an absolute truth score. Confidence-like internal similarity values are development diagnostics only.

## Evidence acquisition modes

Without external credentials, SOURCECHAIN uses the committed verified corpus and remains deterministic. With `TAVILY_API_KEY`, the runtime keeps strong verified matches on the deterministic fast path, then tries Tavily basic search behind a quality gate and Tavily advanced only when basic evidence is too weak. `BRAVE_SEARCH_API_KEY` is an optional later fallback when configured. The full verified corpus remains the final deterministic fallback.

Provider credentials stay server-side. Provider output is candidate evidence, not a verdict. Numeric coincidence alone is not enough to qualify live evidence; weak results fail closed.

## Limitations

Rules can miss paraphrases, idioms, implicit negation, complex Turkish morphology and domain-specific numeric units. Live web retrieval broadens coverage but does not make source quality automatic: evidence quality, recency and publisher reliability are not inferred from URL appearance. Retrieval can miss relevant material or surface conflicting sources. SOURCECHAIN must defer or report insufficiency when provenance or coverage is inadequate.

The current live provider still uses the lightweight lexical passage ranker after web acquisition. A multilingual dense retriever/reranker is a planned quality layer, not a capability claimed by the deployed runtime today.

## Safety

Live retrieval is performed only by the server-side provider against a fixed external search endpoint; user-controlled arbitrary fetch URLs are not exposed as a backend proxy. Retrieved content is rendered as text, not active HTML. Downstream interfaces preserve the supplied citation URL and must continue using text-safe rendering.

Provider failure is fail-closed: the pipeline falls back to the bounded verified corpus and otherwise returns `INSUFFICIENT` rather than inventing evidence.

## Evaluation

The committed SOURCEBENCH-TR v0 set is a small, team-authored development set for regression behavior only. It is not large enough for statistically definitive performance claims. Future evaluation needs independent annotation, grouped event/source splits, hard negatives, per-class precision/recall/F1 and distortion-specific slices.
