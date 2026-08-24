# DRSK Architecture

DRSK is a hybrid social-intelligence layer with one bounded request path:

```text
post -> SOURCECHAIN -> EvidenceBundle -> Resolution Engine
                                           | EVIDENCE
                                           | HUMAN/BOTH -> NIYET allocation
                                           | NONE/DEFERRED
```

## Ownership

- `sourcechain` analyzes statements and claims, retrieves only from supplied or controlled evidence providers, preserves exact passages and provenance, aligns claims with passages, and reports typed distortion.
- `niyet` detects response intent and allocates willing, relevant people under shared capacity.
- `drsk` owns the explicit resolution policy and adapters between the two engines.
- `api` validates the transport boundary; `web` renders the structured result with progressive disclosure.

Neither engine treats a score as a probability of truth. An absent passage means insufficient evidence, not a false claim. Conflicting items stay independently visible in the bundle.

## Contract invariants

An `EvidenceItem` requires an HTTP(S) source URL, canonical URL, retrieval timestamp, exact plain-text passage, passage location, document hash, relation and origin cluster. An `EvidenceBundle` rejects duplicate evidence IDs and explanations that cite evidence outside the bundle. Bundles are immutable, versioned and deterministically serializable.

The resolution paths are:

- `EVIDENCE`: bounded evidence is sufficient and non-conflicting.
- `HUMAN`: evidence is insufficient and human interpretation is requested.
- `BOTH`: evidence is useful but conflicting or distorted, so it remains visible alongside a human route.
- `NONE`: a subjective/non-checkable post needs neither path.
- `DEFERRED`: a recoverable evidence operation is explicitly asynchronous or unavailable.

## Security boundary

The sprint prototype uses controlled/cached evidence. It does not expose arbitrary URL fetching. A future network provider must independently enforce scheme, DNS/IP checks before and after redirects, private/link-local/metadata blocking, timeouts, byte and decompression limits, MIME restrictions, sanitization and redirect limits.

API bodies and post text are bounded before analysis. Evidence passages are rendered as text, and source links come only from validated bundle provenance.

## Replaceable baselines

Statement rules, lexical retrieval and structured alignment are transparent baselines behind module boundaries. They can be replaced by measured Turkish models without changing evidence provenance, bundle or resolution contracts.
