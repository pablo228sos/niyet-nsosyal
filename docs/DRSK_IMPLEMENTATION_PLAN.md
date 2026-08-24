# DRSK Implementation Plan

Plan date: 2026-08-24
Precondition: `docs/DRSK_REPOSITORY_AUDIT.md` accepted
Rule: preserve NIYET as a first-class engine; implement incrementally after approval.

Sprint status (2026-08-24): M0/M1 and the bounded MVP portions of M3-M7 are implemented on `feat/drsk-sourcechain-integration`. Secure arbitrary web ingestion, persistent evidence storage and research-scale model/benchmark work remain tracked GitHub follow-ups. Acceptance evidence is in the test suite and `docs/DRSK_DEMO.md`.

## 1. Architecture

DRSK will be one system with two independently testable engines and one resolution layer.

```text
PostRequest
   |
   v
DRSK Orchestrator
   |-- statement/check-worthiness ----------> SOURCECHAIN
   |                                             |
   |                                             v
   |                                      EvidenceBundle
   |
   |-- response-needed / manual request ----> NIYET
   |                                             |
   |                                             v
   |                                      HumanRouteBundle
   |                 +---------------------------+
   v                 v
Resolution Engine -> EVIDENCE | HUMAN | BOTH | NONE | DEFERRED
   |
   v
Versioned API -> feed indicator / Evidence Panel / responder flow
```

Package rule:

- `niyet` owns human-response classification, retrieval, eligibility and allocation.
- `sourcechain` owns claims, sources, passages, relations, distortion and provenance.
- `drsk` owns orchestration, cross-engine schemas, resolution policy and compatibility adapters.
- Neither engine imports the web layer.
- `drsk` may import both engines; the engines do not import `drsk`.

## 2. Core contracts

### Evidence item

Minimum fields:

```text
evidence_id
claim_id
source_url
canonical_url
publisher
publication_date
retrieved_at
document_hash
passage
passage_location
relation
relation_confidence_band
origin_cluster_id
retrieval_method
provenance_metadata
```

### Evidence Bundle

An immutable versioned bundle contains:

- normalized post and atomic claims;
- retrieved documents and exact passages;
- claim-passage relations and typed limitations;
- independent-origin clusters;
- sufficiency decision inputs;
- citation-first explanation fragments referencing evidence IDs;
- creation timestamp, model/rule versions and dataset/result versions.

No explanation may contain a source URL or passage that is absent from the bundle.

### Resolution decision

```text
EVIDENCE    traceable evidence is sufficient for the bounded question
HUMAN       evidence is insufficient/contested and the user opts into help
BOTH        evidence is useful but specialist interpretation adds value
NONE        neither evidence processing nor human routing is appropriate
DEFERRED    cold retrieval is queued or a recoverable dependency is unavailable
```

Every decision carries typed reasons, never only a score.

## 3. Dependency graph

```text
M0 Baseline truth and CI
  -> M1 Schemas and provenance invariants
      -> M2 Secure document/passages
      -> M3 Statement gate and claims
          -> M4 Retrieval and alignment
              -> M5 Evidence Bundle and explanation
                  -> M6 Resolution -> NIYET escalation
                      -> M7 API and product UI
                          -> M8 SOURCEBENCH-TR freeze and final evaluation

Security tests begin in M1 and gate M2-M8.
Accessibility and documentation begin in M7 and gate release.
```

## 4. Milestones

### M0 - Repair the NIYET evidence baseline

Files:

- modify `data/intent_seed_v1.csv`
- modify `data/response_gate_seed_v1.csv`
- modify `src/niyet/annotations.py`
- modify `scripts/validate_annotations.py`
- modify both retrieval evaluators
- modify `api/experiment.py`, `web/lab.js`
- modify `.github/workflows/tests.yml`, `pyproject.toml`
- add a dependency lock/constraints file and machine-readable result artifacts

Dependencies: none.

Acceptance criteria:

- all 96 rows in each seed parse into the intended columns;
- task-specific validators pass and training rejects any dropped row;
- duplicate batch IDs return 400;
- reviewed benchmark is an explicit required argument for final jobs;
- CI reproduces reviewed lexical metrics and checks `lab.js`;
- classifier result metadata records Python, package versions, dataset hash and seed;
- legacy NIYET API behavior remains green.

Tests:

- CSV structure/row-count/label-distribution regression;
- gate/intent validator tests;
- duplicate-ID runtime/API test;
- reviewed-metric golden test with tolerance;
- API handler tests for body limits, types and error codes.

Risk: fixing malformed CSV rows changes classifier metrics. Record the new result; do not preserve the old number artificially.

### M1 - Versioned DRSK and SOURCECHAIN schemas

Files to add:

- `src/drsk/__init__.py`
- `src/drsk/schemas.py`
- `src/sourcechain/__init__.py`
- `src/sourcechain/schemas.py`
- `src/sourcechain/evidence.py`
- `tests/test_drsk_schemas.py`
- `tests/sourcechain/test_evidence.py`

Dependencies: M0.

Acceptance criteria:

- JSON round-trip is deterministic;
- IDs are unique and stable inside a bundle;
- canonical URL, retrieval time, passage and document hash are mandatory;
- relation values are a closed enum;
- an explanation cannot cite an unknown evidence ID;
- untrusted HTML is never stored as a user-facing passage.

Tests: schema validation, duplicate IDs, missing provenance, Unicode Turkish text, serialization compatibility and explanation-citation invariants.

### M2 - Secure bounded document and passage ingestion

Files to add:

- `src/sourcechain/fetching.py`
- `src/sourcechain/documents.py`
- `src/sourcechain/passages.py`
- `src/sourcechain/cache.py`
- `tests/sourcechain/test_fetching_security.py`
- `tests/sourcechain/test_passages.py`

Dependencies: M1.

P0 implementation choice:

- Start with an allowlisted/curated real-source adapter and deterministic local fixtures.
- Add arbitrary HTTP/HTTPS only after the security suite passes.
- Extract readable text, retain a hash and location, and discard active content.
- Enforce scheme, DNS/IP, redirects, MIME type, byte limit, timeout and decompression limits.

Acceptance criteria:

- private, loopback, link-local and metadata addresses are blocked before and after redirects;
- DNS rebinding and redirect-to-private tests fail closed;
- oversized, compressed-bomb-like, non-text and timeout cases return typed failures;
- extracted passages map back to document hash and location;
- cached documents retain retrieval/provenance metadata.

### M3 - Statement gate and atomic claim extraction

Files to add:

- `src/sourcechain/statement_classifier.py`
- `src/sourcechain/claim_extractor.py`
- `data/sourcebench_tr/annotation_guide.md`
- `data/sourcebench_tr/statement_seed_v0.csv`
- `tests/sourcechain/test_statement_classifier.py`
- `tests/sourcechain/test_claim_extractor.py`

Dependencies: M1.

Implementation realism:

- statement type/check-worthiness: compare majority, rules, TF-IDF+LogReg and Turkish encoder;
- atomic extraction: deterministic sentence/coordination rules first, then a model only where measured;
- opinions and personal experiences remain explicit non-claim types;
- no model result is reported before a grouped split is frozen.

Acceptance criteria:

- one post can produce zero, one or several span-linked claims;
- each claim retains exact source offsets and normalized text;
- examples with opinion/experience do not receive a factual-evidence badge;
- group/event leakage checks pass.

### M4 - Evidence retrieval, passage ranking and alignment baseline

Files to add:

- `src/sourcechain/retrieval.py`
- `src/sourcechain/passage_ranker.py`
- `src/sourcechain/alignment.py`
- `src/sourcechain/structured_checks.py`
- `experiments/evaluate_sourcechain_retrieval.py`
- `experiments/evaluate_sourcechain_alignment.py`
- `tests/sourcechain/test_retrieval.py`
- `tests/sourcechain/test_alignment.py`
- `tests/sourcechain/test_structured_checks.py`

Dependencies: M2 and M3.

Implementation choices:

- retrieval: lexical/BM25 baseline, ModernBERT dense candidate and optional hybrid;
- passage ranking: bounded candidate passages, with a reranker only if it beats the baseline;
- relation: compare transparent similarity/NLI baseline with task-specific Turkish model;
- numeric/date differences: structured extraction and comparison, not an LLM verdict;
- alignment labels: SUPPORTED, PARTIALLY_SUPPORTED, CONFLICTING, INSUFFICIENT.

Acceptance criteria:

- every ranked item is a real passage with source provenance;
- hard topical negatives are present in evaluation;
- numeric contradictions cannot be hidden by high semantic similarity;
- no retrieval result is silently converted into support;
- metrics include Recall@K, MRR/NDCG, per-class precision/recall/F1 and error slices.

### M5 - Evidence Bundle, source mismatch and citation-first explanation

Files to add:

- `src/sourcechain/mismatch.py`
- `src/sourcechain/distortion.py`
- `src/sourcechain/explanation.py`
- `tests/sourcechain/test_mismatch.py`
- `tests/sourcechain/test_distortion.py`
- `tests/sourcechain/test_explanation_faithfulness.py`

Dependencies: M4.

Acceptance criteria:

- explanation text is template-generated from typed bundle facts for P0;
- cited URL, publisher, date and passage exactly match the bundle;
- source mismatch is distinct from source reputation;
- P0 supports at least numeric, temporal, certainty and causality checks with explicit UNKNOWN cases;
- hallucinated-source count is zero in automated adversarial tests.

### M6 - DRSK orchestrator and Resolution Engine

Files to add:

- `src/drsk/orchestrator.py`
- `src/drsk/resolution.py`
- `src/drsk/niyet_adapter.py`
- `tests/test_drsk_orchestrator.py`
- `tests/test_resolution.py`

Dependencies: M5 and existing NIYET runtime.

Policy:

- deterministic rules consume typed SOURCECHAIN outputs;
- insufficient/contested evidence does not automatically contact a person;
- user opt-in creates a NIYET request with claim text, topics, entities, evidence status and bundle ID;
- human-contributed sources create a new bundle version, not an in-place mutation;
- no human vote is treated as truth.

Acceptance criteria:

- evidence-sufficient fixture returns EVIDENCE and no human route;
- insufficient/contested fixture offers HUMAN and routes only after opt-in;
- BOTH is supported for specialist interpretation;
- duplicate/replayed requests are idempotent;
- NIYET remains independently importable/testable.

### M7 - Versioned API and integrated product flow

Files to modify:

- `api/index.py`
- `web/index.html`
- `web/app.js`
- `web/styles.css`
- `web/live.css`
- `vercel.json`
- `.github/workflows/tests.yml`

Files to add:

- `api/drsk.py` only if Vercel routing requires a separate async/status endpoint;
- `tests/test_api_contract.py`
- browser end-to-end tests for desktop/mobile/TR/EN;
- `docs/api.md`

Dependencies: M6.

Migration:

- keep current flat NIYET payload as a compatibility adapter;
- introduce `schema_version`, `engines`, `resolution`, `evidence_bundle` and `human_route` envelope;
- use one product flow, not separate SOURCECHAIN and NIYET applications;
- render an inline evidence status, Evidence Panel and opt-in Ask a relevant person action;
- repair all localized visible and accessibility labels.

Acceptance criteria:

- old NIYET demo calls still pass;
- a factual claim reaches a traceable Evidence Panel;
- insufficient evidence reaches the existing responder flow after confirmation;
- keyboard, screen-reader text, reduced motion and 390px mobile tests pass;
- CSP/security headers are enabled without breaking the app;
- API applies body limits, rate limits and stable error codes.

### M8 - SOURCEBENCH-TR freeze and final evidence package

Files to add:

- `data/sourcebench_tr/README.md`
- `data/sourcebench_tr/dataset_card.md`
- versioned statement, claim-evidence, mismatch and evolution datasets
- `scripts/validate_sourcebench.py`
- `scripts/freeze_sourcebench.py`
- `experiments/results/*.json`
- `docs/DRSK_EVIDENCE_LEDGER.md`

Dependencies: M3-M7.

Freeze rules:

- group by underlying event/source/origin before splitting;
- two independent reviewers plus adjudication;
- freeze hashes before final baseline/model comparison;
- preserve raw anonymized reviews when consent/licensing permits, otherwise provide a verifiable signed aggregate procedure and explain the boundary;
- retain failed experiment outputs.

Acceptance criteria:

- final metrics are produced by CI from the frozen tag/hash;
- result JSON includes command, commit, environment, data hash, model/rule version and seed;
- adversarial/challenge slices are separate from training;
- final report statements link to a code/test/data/result artifact.

## 5. Scope priorities

### P0 - End-to-end defensible prototype

- M0 baseline repair and CI truthfulness.
- M1 schemas/provenance.
- M2 bounded secure real-document/passages.
- M3 statement gate and atomic claims.
- M4 lexical/dense retrieval baseline plus four-way relation baseline.
- M5 immutable Evidence Bundle and citation-first explanation.
- M6 deterministic evidence-to-human resolution.
- M7 one integrated UI/API path.
- Minimum frozen evaluation slice sufficient to report honest baseline behavior.

### P1 - Strong TEKNOFEST evidence

- Complete SOURCEBENCH-TR minimum sizes from the Technical Report.
- Source mismatch and structured numeric/date distortion.
- Calibration analysis where confidence is displayed.
- Server-authoritative NIYET state, identity, idempotency and outcome storage.
- Automated WCAG/browser suite and anonymized raw user-study results.
- Latency/cache/cost measurements and offline demo bundle.

### P2 - High-value competition features

- Distortion Lens for certainty, causality, quantity, scope, attribution and temporal shifts.
- Evidence Explorer with source/repost comparison.
- Evidence lineage and independent-origin clustering.
- Claim evolution graph and human-added evidence bundle revisions.

### P3 - Stretch

- Sparse allocation backend for larger windows.
- Institutional responder-pool administration.
- Advanced active learning and review queues.
- Additional languages after Turkish evidence is strong.

### DO NOT BUILD in 2026 scope

- generic truth score or fake-news label;
- automatic moderation/removal;
- political/person credibility score;
- follower-based expertise score;
- blockchain provenance;
- multimodal deepfake detection;
- general-purpose autonomous web-browsing agent;
- free-form LLM explanation that can introduce sources.

## 6. Acceptance-test map

| Feature claim | Required acceptance proof |
| --- | --- |
| Statement gate | Frozen grouped test, per-class metrics, opinion/experience cases |
| Atomic claim | Exact span/offset golden fixtures and multi-claim cases |
| Evidence retrieval | Real source/passages, Recall@K/NDCG, hard negatives |
| Alignment | Four relations, per-class metrics, numeric adversarial cases |
| Provenance | Schema invariant and source/passage round-trip |
| Citation-first explanation | Zero unknown citation IDs and zero invented URLs |
| Source mismatch | Attributed-source hard pairs and UNKNOWN behavior |
| Resolution | EVIDENCE/HUMAN/BOTH/NONE/DEFERRED policy tests |
| NIYET escalation | Structured transfer, opt-in and capacity compliance |
| Human evidence update | New immutable bundle version and audit event |
| UI | Desktop/mobile/TR/EN keyboard and a11y flow |
| Deployment | Clean build, smoke endpoint, security headers, rollback/offline demo |

## 7. Proposed file changes

### Add

- sibling packages `src/drsk/` and `src/sourcechain/` listed above;
- SOURCECHAIN and DRSK test directories;
- `data/sourcebench_tr/` with annotation/freeze assets;
- versioned experiment result JSON;
- API/evidence/security documentation and evidence ledger;
- browser/API/security CI tests;
- dependency constraints/lock file.

### Modify

- existing NIYET CSVs, validators, evaluators and CI first;
- `api/index.py` through a backward-compatible orchestrator adapter;
- `web/index.html`, `app.js` and styles for one integrated flow;
- `pyproject.toml` for bounded optional model/fetch dependencies and tool configuration;
- `vercel.json` for headers/routing/time-bound functions only after local verification;
- README and stale dataset/experiment documents together with code.

NIYET allocator, optimizer, metrics and core types should be extended or wrapped, not rewritten.

## 8. Migration risks and controls

| Risk | Control |
| --- | --- |
| Breaking current live demo | Compatibility contract tests and feature flag for DRSK envelope |
| Serverless timeout/model memory | Cached bounded P0 path; worker interface; measured fallback |
| Provenance loss | Immutable schemas and invariant tests before retrieval UI |
| Dataset leakage | Event/source grouping and freeze before final runs |
| Metric chasing | Freeze hashes and retain raw result artifacts before model comparison |
| Unsafe URL fetch | Dedicated security boundary and fail-closed adversarial suite |
| Human-routing state races | Idempotency keys, unique IDs and transactional repository |
| Scope explosion | P0 acceptance slice; P2 features cannot block core resolution path |

## 9. Recommended implementation order

```text
M0 -> M1 -> (M2 + M3) -> M4 -> M5 -> M6 -> M7 -> M8
```

M2 and M3 may proceed in parallel only after schema invariants are frozen. No SOURCECHAIN UI should be implemented before M5 can produce a traceable bundle. No final performance claim should be written before M8 freezes data and emits machine-readable results.

## 10. Stop point

This plan intentionally stops before implementation. The first approved coding change should be M0 baseline repair, not SOURCECHAIN feature code.
