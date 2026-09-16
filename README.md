# DRSK — Evidence + Human Resolution for Social Platforms

DRSK is a hybrid social-intelligence prototype for social platforms. It combines bounded evidence analysis with capacity-aware human routing instead of pretending that every ambiguous post can be solved by one model.

```text
post
  ↓
SOURCECHAIN ── claim → passage → provenance → relation → distortion
  ↓
Resolution Engine ── EVIDENCE | HUMAN | BOTH | NONE | DEFERRED
  ↓                                  │
  └──────────────────────────────────┴→ NIYET
                                      willing + relevant + available human
```

**When evidence is enough, show the evidence. When it is not, route the unresolved part to a willing person.**

SOURCECHAIN does not emit an absolute truth score. Missing evidence means `INSUFFICIENT`, not false. NIYET does not infer hidden psychological traits: it routes explicit response needs under willingness and finite attention capacity.

## What works now

- deterministic statement/check-worthiness analysis and bounded claim extraction
- pluggable evidence acquisition with a verified local corpus and optional server-side live web context
- exact passage, canonical URL, publisher, publication date, document hash and origin-cluster provenance
- `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONFLICTING` and `INSUFFICIENT` claim/evidence relations
- typed numeric, temporal, causality, certainty, scope and attribution-shift checks
- explicit `EVIDENCE`, `HUMAN`, `BOTH`, `NONE` and `DEFERRED` resolution policy
- structured SOURCECHAIN → NIYET escalation that preserves claim and evidence context
- response-needed and four-way intent classification for NIYET
- hard responder willingness, active-state and remaining-capacity constraints
- bounded global allocation across multiple open requests competing for shared responder capacity
- Accept / Skip / Pause / Resume transitions with reallocation of still-open requests
- transactional demo-state abstraction with process-local memory fallback and optional durable Upstash Redis REST storage
- bilingual English/Turkish author and responder surfaces with evidence disclosure and source links

The main architecture is documented in [`docs/DRSK_ARCHITECTURE.md`](docs/DRSK_ARCHITECTURE.md). Reproducible product scenarios are in [`docs/DRSK_DEMO.md`](docs/DRSK_DEMO.md).

## End-to-end flow

1. classify whether the post contains a check-worthy factual statement
2. extract bounded, span-linked claims
3. acquire candidate passages through the configured evidence provider
4. preserve passage-level provenance before explanation
5. align each claim with the retrieved evidence
6. expose typed wording shifts instead of collapsing them into a truth score
7. choose an explicit DRSK resolution path
8. when human interpretation is recommended, ask the author for explicit confirmation
9. after confirmation, pass structured claim/evidence context into NIYET
10. globally allocate the current open request window under responder willingness and remaining capacity
11. return evidence and/or the human answer to the original request

Accepted requests are pinned to the accepting responder and consume capacity. Open or unmatched requests are reallocated together when the matching window changes. A stale UI action is rejected as a conflict rather than silently consuming capacity twice.

## Evidence acquisition modes

SOURCECHAIN keeps evidence acquisition separate from evidence interpretation.

**Default / offline mode.** Without external credentials, the pipeline uses a small verified corpus committed with the project. Every stored passage points to its original primary/official page, so local tests and the fallback demo remain deterministic and inspectable.

**Optional live-web mode.** When `BRAVE_SEARCH_API_KEY` is configured on the server, SOURCECHAIN uses Brave's LLM Context endpoint to retrieve current web passages and source metadata. Those passages are still processed by SOURCECHAIN's own passage ranking, relation and distortion logic. Brave does not provide the project verdict. If the live provider fails or returns no usable passages, the pipeline falls back to the verified corpus.

```text
BRAVE_SEARCH_API_KEY=...
```

The key is server-side only and is never exposed to the browser.

Verified fallback scenarios:

| Scenario | Stored source | Expected behavior |
| --- | --- | --- |
| coffee mortality wording | PubMed / *Circulation* | association evidence can expose a causality shift and produce `BOTH` |
| physical-activity benefit statement | World Health Organization | exact supported wording can resolve through `EVIDENCE` |
| industrial CO₂ increase | NASA Science | changing “nearly 50%” to another numeric claim exposes a numeric distortion and can produce `BOTH` |
| factual claim outside available evidence | none | remains `INSUFFICIENT`; an explicit request for help can produce `HUMAN` |
| subjective opinion | none | stays outside factual verification and resolves to `NONE` |

Live web retrieval broadens evidence coverage; it does **not** turn SOURCECHAIN into a universal fact checker. Source quality, completeness and recency remain explicit limitations.

## NIYET evaluation

Two team reviewers independently labeled the same 256 query↔responder relevance pairs. They agreed exactly on 243/256 pairs (94.92%); quadratic weighted Cohen’s κ was 0.9756. A third team member adjudicated the 13 disagreements, producing the frozen reviewed benchmark.

Retrieval on the frozen 32-query × 8-responder benchmark:

| Retriever | Precision@3 | Recall@3 | NDCG@3 |
| --- | ---: | ---: | ---: |
| weighted lexical TF-IDF | 0.4688 | 0.8438 | 0.8450 |
| ModernBERT-TR-Embed | **0.5417** | **0.9583** | **0.9025** |

At lexical similarity floor `0.02`, the bounded global allocator covers 78.12% of reviewed requests versus 65.62% for the capacity-aware greedy baseline and increases total reviewed relevance from 45 to 52. Mean assigned relevance is 2.08 for global versus 2.14 for greedy, making the coverage/quality trade-off explicit rather than hiding it.

ModernBERT-TR-Embed is evaluated offline. The lightweight runtime intentionally keeps the lexical retriever so deployment cost and semantic-model quality remain separable engineering decisions.

## Classification checks

On the repaired controlled development sets with pinned dependencies and grouped four-fold cross-validation:

- response-needed: accuracy `0.917 ± 0.030`, macro-F1 `0.915 ± 0.030`
- four-way intent: accuracy `0.885 ± 0.062`, macro-F1 `0.880 ± 0.061`

These are controlled-development measurements, not population estimates.

## Shared demo state

`src/drsk/state_store.py` defines the mutable-state boundary used by the human-help flow.

- without external credentials, local/test execution uses a thread-safe process-local `MemoryStateStore`
- when Upstash credentials are supplied, `UpstashRedisStateStore` stores the JSON state with TTL and compare-and-set Lua mutations
- concurrent writers retry rather than overwriting a newer snapshot
- the UI distinguishes durable shared state from the process-local prototype fallback

Environment variables for durable multi-instance demo state:

```text
UPSTASH_REDIS_REST_URL=...
UPSTASH_REDIS_REST_TOKEN=...
DRSK_STATE_NAMESPACE=jury-demo-v2      # optional
DRSK_STATE_TTL_SECONDS=86400           # optional
```

The memory fallback is suitable for local development and single-process tests; it is not represented as cross-device durable state.

## Run locally

Python 3.11+ is required.

```bash
python -m pip install -c constraints.txt -e . pytest
pytest -q
python -m compileall -q src api scripts experiments
python experiments/evaluate_matching_draft.py
python experiments/evaluate_sourcechain_v0.py
python scripts/validate_annotations.py data/intent_seed_v1.csv
python scripts/validate_annotations.py data/response_gate_seed_v1.csv
python scripts/validate_sourcebench.py data/sourcebench_tr
python scripts/serve_local.py --port 8766
```

The repository CI also runs JavaScript syntax checks for the shipped web surfaces.

## Repository structure

- `src/sourcechain/` — statement/claim analysis, evidence acquisition, passage ranking, alignment, distortion, lineage baseline and EvidenceBundle assembly
- `src/niyet/` — response/intent classification, responder retrieval, eligibility, scoring, greedy/global allocation and runtime
- `src/drsk/` — resolution policy, SOURCECHAIN→NIYET adapter, human-help service and state-store abstraction
- `api/` — bounded transport handlers for analysis, experiments and human-help state transitions
- `web/` — bilingual final product surface and allocation lab
- `data/` — controlled development data, synthetic responder profiles, reviewed matching benchmark and SOURCEBENCH-TR v0
- `experiments/` — reproducible retrieval/allocation/SOURCECHAIN development evaluation
- `tests/` — unit, integration and end-to-end contract tests
- `docs/` — current architecture, dataset, safety and product documentation

## Current boundaries

- without `BRAVE_SEARCH_API_KEY`, SOURCECHAIN uses the bounded verified corpus only
- optional live web evidence retrieval broadens coverage but does not infer source reliability or guarantee complete evidence
- SOURCEBENCH-TR v0 is a 15-example development regression set, not benchmark-grade model validation
- SOURCECHAIN passage ranking/alignment/distortion logic is currently a deterministic lexical/structured baseline
- Evidence Lineage uses supplied origin-cluster IDs; live web retrieval conservatively groups pages by hostname rather than claiming automatic syndication detection
- the Distortion Lens is single-hop claim↔evidence comparison, not arbitrary repost-chain reconstruction
- responder profiles in the prototype are synthetic
- durable shared demo state requires external Upstash configuration; the default memory fallback is process-local
- authentication, platform identity, production abuse controls and production rate limiting are not implemented
- the semantic NIYET retriever is evaluated offline rather than loaded into the lightweight runtime
- offline relevance is not the same as a real-world resolved interaction
- usability samples are small prototype studies and are not presented as population estimates

The project keeps these limits explicit so the public claims remain narrower than — or equal to — what the code and reproducible evidence support.
