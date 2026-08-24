# DRSK Repository Audit

Audit date: 2026-08-24  
Repository: `pablo228sos/niyet-nsosyal`  
Audited revision: `1e2ea0bc060702b3b8e2e522e83eb2292eefb5fe` (`main`)  
Target specification: `DRSK_Technical_Report_2026.docx`

## 1. Executive summary

The repository contains a small but genuine, deployed NIYET prototype. It is not merely a UI mock. The current path trains a binary response-needed classifier and a four-way intent classifier, retrieves synthetic responder profiles with weighted lexical TF-IDF, applies hard willingness/active/capacity/topic-floor eligibility, and allocates a bounded request window with either greedy or global assignment. Accept, Skip and Pause are wired into a browser-session prototype, the public API is live, the main mobile responder flow works, and the base test suite passes.

The repository is not yet a unified DRSK implementation. No SOURCECHAIN or DRSK Resolution Engine production module exists. Searching the repository for SOURCECHAIN, evidence-bundle, distortion, lineage, source-mismatch and resolution-engine symbols returns no implementation. The Technical Report is therefore the target architecture, not a description of current code.

Repository health is **PARTIAL / usable NIYET prototype with evidence-integrity defects**:

- 34/34 pytest tests pass; both shipped JavaScript files pass `node --check`.
- The live Vercel UI and API work on desktop and mobile.
- Frozen lexical, ModernBERT and allocation claims are reproducible when evaluators are explicitly pointed at the reviewed benchmark.
- Normal CI and Allocation Lab still use the draft benchmark, not the frozen reviewed benchmark.
- Three unquoted CSV commas corrupt one intent row and two response-gate rows. Training silently drops them.
- The annotation validator fails on the intent seed and cannot validate RESPONSE/NONE data.
- Dependency lower bounds are not a reproducible lock; classifier metrics drift with current scikit-learn.
- Raw usability observations and raw independent reviewer sheets are not present, so their reported aggregates cannot be independently recomputed from the public repository.
- Client-controlled capacity is suitable only for a demo. There is no authentication, central persistence, rate limiting or concurrency control.
- Duplicate batch request IDs produce duplicate decisions for a single responder slot and violate the API's capacity semantics.

Audit rule used throughout: repository code and executable checks define current status; the Technical Report defines target status.

### Status vocabulary

`IMPLEMENTED`, `PARTIALLY IMPLEMENTED`, `EXPERIMENTAL / OFFLINE ONLY`, `MOCK / UI ONLY`, `DOCUMENTED BUT NOT IMPLEMENTED`, `NOT IMPLEMENTED`, `BROKEN`, `UNKNOWN / NEEDS VERIFICATION`.

## 2. Repository map

| Path | Current role | Audit note |
| --- | --- | --- |
| `src/niyet/` | NIYET classifiers, retrieval, scoring, eligibility, allocation, metrics and runtime | Reusable core; no SOURCECHAIN package |
| `api/index.py` | Live NIYET API and client-supplied session state | Working but unauthenticated and non-transactional |
| `api/experiment.py` | Allocation Lab API | Hardcoded to draft benchmark |
| `web/` | Bilingual feed prototype and Allocation Lab | Working desktop/mobile; partial localization and draft-label mismatch |
| `data/` | Controlled classification data, synthetic profiles, draft/reviewed matching benchmarks | Valuable, but classification CSV corruption and incomplete review fields exist |
| `experiments/` | Classification notes, lexical/semantic retrieval and scaling experiments | Reproducible with caveats; reviewed benchmark is not the default |
| `scripts/` | Annotation, review, freeze, training, usability and allocation utilities | Matching review path tested; gate validation unsupported |
| `tests/` | 34 unit/integration tests | Strong allocator/runtime start; missing API, data-integrity, browser and security regressions |
| `docs/` | Architecture, data, safety, UX and evaluation notes | Several documents are stale relative to the frozen benchmark and live product |
| `.github/workflows/tests.yml` | Main CI | Tests Python, `web/app.js`, pytest and draft lexical experiment |
| `vercel.json` | Static web plus Python serverless deployment | Parses and deploys; no local Vercel build was reproducible without CLI/project linkage |

No repository-level `AGENTS.md`, release tags or GitHub releases are present. The repository has 50 commits, five open issues, one closed issue and four closed/merged pull requests at audit time.

## 3. Current architecture

```text
composer text
  -> response-needed TF-IDF + LogisticRegression
  -> author confirmation / manual override in web UI
  -> intent TF-IDF + LogisticRegression
  -> weighted char-TFIDF responder retrieval
       80% explicit topics + 20% profile prose
  -> hard filters
       active + remaining capacity + willing intent + topic floor + skip exclusions
  -> pair utility
       (topic relevance + availability) / 2
  -> bounded global assignment
       repeated capacity slots + zero-utility dummy assignments
  -> browser-session request/capacity state
       Accept / Skip / Pause / Resume
```

Dependency direction:

```text
web/app.js -> /api -> niyet.runtime
niyet.runtime -> classifier + optimizer + scoring + types
optimizer -> allocator.Assignment + scoring + scipy.linear_sum_assignment
api/experiment.py -> draft benchmark + allocator + optimizer
web/lab.js -> /api/experiment
```

ModernBERT is a separate offline experiment and is not called by the deployed runtime.

## 4. Current NIYET capability audit

| Component | Implementation file | Tests | Data / experiment | Runtime status | Quality concerns |
| --- | --- | --- | --- | --- | --- |
| 1. Response-needed detection | `src/niyet/runtime.py`, `classifier.py` | `test_runtime.py`, `test_classifier.py` | `response_gate_seed_v1.csv`, `response_gate_seed_v1.md` | IMPLEMENTED | Controlled data; two malformed rows silently dropped; no probability calibration |
| 2. Intent classification | `classifier.py`, `runtime.py` | `test_classifier.py`, `test_runtime.py` | `intent_seed_v1.csv`, challenge set | IMPLEMENTED | One malformed row silently dropped; challenge set is not evaluated by a committed runner |
| 3. Author confirmation | `web/app.js`, `api/index.py` override | Live browser audit | UI state | IMPLEMENTED | Browser behavior has no automated test |
| 4. Responder retrieval | `runtime.py`, `retrieval.py` | `test_retrieval.py`, runtime routes | reviewed/draft matching benchmark | IMPLEMENTED lexical; EXPERIMENTAL semantic | Deployed and experiment document representations differ slightly |
| 5. Willingness filtering | `runtime.py`, `retrieval.py` | `test_eligibility.py`, `test_retrieval.py` | synthetic profiles | IMPLEMENTED | `CandidateMatch.willingness` is validated but ignored in scoring; hard filter is correct current design |
| 6. Active/inactive state | `runtime.py` | pause runtime test | synthetic profiles/session state | IMPLEMENTED | Client supplies state; no identity or server authority |
| 7. Capacity handling | `runtime.py`, `optimizer.py` | allocator/optimizer/runtime tests | allocation experiments | PARTIALLY IMPLEMENTED | Correct inside one request, but browser-only and duplicate IDs can violate returned decisions |
| 8. Topic quality threshold | `runtime.py`, `optimizer.py` | optimizer threshold tests | threshold sweep | IMPLEMENTED | Runtime defaults differ by surface; no calibration protocol |
| 9. Scoring | `scoring.py` | indirect allocator tests | documented formula | IMPLEMENTED | Equal weights are unlearned development utility |
| 10. Greedy allocation | `allocator.py` | `test_allocator.py` | benchmark runners | IMPLEMENTED | Deterministic tie behavior is implicit |
| 11. Global allocation | `optimizer.py` | `test_optimizer.py` | benchmark and scaling scripts | IMPLEMENTED | Dense matrix is bounded but not sparse/transactional |
| 12. Dummy/unmatched | `optimizer.py` | low-quality unmatched test | allocation formulation | IMPLEMENTED | No explicit unmatched reason taxonomy |
| 13. Accept | `web/app.js`, `api/index.py`, `runtime.py` | capacity state unit test; live browser audit | usability docs | PARTIALLY IMPLEMENTED | Consumes client session slot only; no durable acceptance/outcome record |
| 14. Skip | `web/app.js` exclusion and reallocation | live browser/code audit | usability docs | PARTIALLY IMPLEMENTED | Frontend-only exclusion list; not an authenticated state transition |
| 15. Pause/Resume | `web/app.js`, `api/index.py`, `runtime.py` | pause runtime test; live browser audit | usability docs | PARTIALLY IMPLEMENTED | Session-local and matched-responder-centric |
| 16. Matching window | `web/app.js`, `runtime.route_many` | shared-capacity runtime test | Allocation Lab | IMPLEMENTED for demo | Browser queue; max 20 API requests; duplicate IDs not rejected |
| 17. Session persistence | `web/app.js` | manual live audit | sessionStorage | EXPERIMENTAL / OFFLINE ONLY | No cross-tab/device consistency, transactions or recovery |
| 18. API integration | `api/index.py`, `api/experiment.py` | no handler tests; live curl audit | Vercel | IMPLEMENTED | Body is read before size bound; no auth/rate limit/schema framework |
| 19. Mobile UX | `web/app.js`, CSS | manual 390x844 browser audit | usability notes | IMPLEMENTED | No automated viewport/a11y regression test |
| 20. EN/TR localization | `web/app.js` | manual browser audit | bilingual copy map | PARTIALLY IMPLEMENTED | Post actions, mobile nav ARIA and some service labels remain English in TR |
| 21. Allocation Lab | `api/experiment.py`, `web/lab.js` | manual live audit | draft matching benchmark | IMPLEMENTED but stale | Displays `team_review_pending` and draft grades after reviewed benchmark exists |
| 22. Metrics | `metrics.py`, experiment scripts | `test_metrics.py` | classification/retrieval/allocation/scaling notes | PARTIALLY IMPLEMENTED | Classifier dependency drift; reviewed metrics require runtime override |
| 23. Datasets | `data/` | review workflow test only | controlled seeds, synthetic profiles, reviewed matching data | PARTIALLY IMPLEMENTED | Corrupt CSV rows; no organic NSosyal sample; raw review/usability evidence absent |
| 24. Annotation workflow | `annotations.py`, review/freeze scripts | annotation and review workflow tests | templates and reviewed JSON | PARTIALLY IMPLEMENTED | Intent validator fails current seed and cannot validate gate labels |
| 25. ModernBERT experiment | `retrieval.py`, `evaluate_modernbert_retrieval.py` | embedding math test only | semantic experiment + branch workflow | EXPERIMENTAL / OFFLINE ONLY | Script defaults to draft; workflow is not on main; model config warnings observed |

## 5. Test, CI, frontend, API and deployment baseline

Environment: Windows, Python 3.12, fresh local `.venv`, current dependency resolution on 2026-08-24.

| Command | Result | Notes |
| --- | --- | --- |
| `python -m pip install -e . pytest` | PASS | Base dependencies install |
| `pytest -q` | PASS | 34 passed, 0 failed, 0 skipped in 11.99s |
| `node --check web/app.js` | PASS | Main CI also checks this file |
| `node --check web/lab.js` | PASS | Not checked by current CI |
| `python -m pip check` | PASS | No broken requirements |
| `python scripts/train_intent_baseline.py --cv` | PASS with drift | 95 usable rows; Macro F1 0.864 |
| `python scripts/train_intent_baseline.py data/response_gate_seed_v1.csv --cv` | PASS with drift | 94 usable rows; Macro F1 0.936 |
| `python experiments/evaluate_matching_draft.py` | PASS, draft only | Explicitly reports `v1-draft`, `team_review_pending` |
| Same lexical evaluator with reviewed path | PASS | Reproduces final lexical/allocation claims |
| `python experiments/evaluate_modernbert_retrieval.py` | PASS, draft only | Reproduces draft semantic notes |
| Same ModernBERT evaluator with reviewed path | PASS | Reproduces final semantic claims |
| `python experiments/benchmark_scaling.py ...` | PASS | Method reproducible; timing is hardware/version dependent |
| `python scripts/validate_annotations.py data/intent_seed_v1.csv` | FAIL | Malformed row 87 and missing final label |
| Validator on response gate | FAIL by design defect | RESPONSE/NONE are not allowed labels; two malformed rows also present |
| `pip-audit` | PASS with scope caveat | No known vulnerabilities in resolved third-party packages; local `niyet` package skipped |
| Live `/api` GET/help/invalid JSON/oversize text | PASS | 200/200/400/400 respectively |
| Packaged DOCX renderer | NOT REPRODUCIBLE | LibreOffice/`soffice` absent; complete structural extraction used |
| Local `vercel build` | NOT REPRODUCIBLE | Vercel CLI/project linkage not installed; live deployment and Actions status are green |

Baseline summary:

- Tests: **34 passed, 0 failed, 0 skipped**.
- CI: **PASS on current main**, but validates draft matching data and omits `lab.js`, data validation, reviewed metrics, browser flows and security checks.
- Frontend: **WORKING / PARTIAL**.
- API: **WORKING / PARTIAL**.
- Deployment configuration: **VALID JSON; live deployment working; local build not reproduced**.
- Lint/type check: **NOT CONFIGURED**.

GitHub Actions shows the latest `tests` run on main succeeded. A ModernBERT workflow succeeded on `modernbert-eval`, but that workflow remains on a closed, unmerged branch rather than current main.

## 6. Dataset and benchmark inventory

| Artifact | Actual inventory | Status | Evidence boundary |
| --- | --- | --- | --- |
| Intent seed | 96 CSV rows; 95 trainable; 48 groups; 24/24/24/23 labels | BROKEN / controlled | Row `discuss_hardware_2` is shifted by an unquoted comma |
| Response gate seed | 96 CSV rows; 94 trainable; 72 parsed groups; 48 RESPONSE/46 NONE | BROKEN / controlled | Rows `none_travel_2`, `none_weather_2` are shifted |
| Intent challenge | 48 rows; 24 groups; 12 per intent | EXPERIMENTAL / OFFLINE ONLY | No committed evaluation command/result |
| Responder profiles | 8 profiles | MOCK / UI ONLY data | Synthetic, not real users |
| Draft matching benchmark | 32 queries x 8 responders; 256 pairs | DEVELOPMENT ONLY | Preserved correctly for provenance |
| Reviewed matching benchmark | 32 x 8; 256 final labels; 13 adjudicated disagreements | IMPLEMENTED artifact | Raw independent sheets are absent; aggregate metadata only |
| Usability template | Header/template only | MOCK / UI ONLY artifact | Cannot reproduce reported 8-person and 5-session aggregates |
| SOURCEBENCH-TR | No files | NOT IMPLEMENTED | Technical Report target only |

The two independent matching reviews and usability study may be genuine, but the public repository cannot independently recompute their aggregates because raw anonymized evidence is intentionally not committed. This should be described as **NEEDS MORE EVIDENCE**, not as fabricated and not as fully reproducible.

## 7. Open issue audit

| Issue | Claimed requirement | Code evidence | Test evidence | Actual status | Recommended action |
| --- | --- | --- | --- | --- | --- |
| #2 Build Turkish intent dataset v1 | Guide, provenance, double review, groups, validation, real dataset | Guide/schema/trainer exist; controlled seed exists; malformed row; almost all `label_b` blank | Validator fails current seed; classifier test uses synthetic in-test rows | PARTIALLY IMPLEMENTED | KEEP OPEN |
| #3 Track technical report evidence | Every report criterion backed by artifact | Many NIYET artifacts exist; SOURCECHAIN absent; stale docs and missing raw study/review inputs | Some metrics reproduce; some cannot | PARTIALLY IMPLEMENTED | UPDATE SCOPE |
| #4 Add response-needed gate | Binary gate before intent, negatives, confirmation, separate report | Runtime/API/UI gate implemented; controlled seed has two malformed rows | Runtime gate tests pass; validator incompatible | PARTIALLY IMPLEMENTED | SPLIT |
| #5 First accessible product flow | Composer, suggestion, confirmation, route, Accept/Skip/Pause, outcome feedback, accessibility | Live flow and mobile drawer work; persistent outcome feedback absent; TR ARIA incomplete | Only runtime unit tests and JS syntax; no browser/a11y regression | PARTIALLY IMPLEMENTED | UPDATE SCOPE |
| #6 Draft technical report | Rubric-aligned evidence-based report | New DRSK report exists outside repository; old issue scope is NIYET-era | Report claims partially reproduced in this audit | SUPERSEDED | SUPERSEDED BY DRSK |

Closed issue #1 was correctly closed for its original small benchmark setup. Its comment explicitly limited the toy data, and later reviewed work extends rather than invalidates that closure.

## 8. Existing claim reproduction

| Claim | Expected | Actual | Delta | Reproducible? |
| --- | ---: | ---: | ---: | --- |
| Response gate Macro F1 | 0.916 | 0.936 | +0.020 | NO exact; dependency/data-row drift |
| Four-way intent Macro F1 | about 0.872 | 0.864 | -0.008 | NO exact; dependency/data-row drift |
| Reviewed lexical P@3 | 0.4688 | 0.4688 | 0 | YES with reviewed-path override |
| Reviewed lexical R@3 | 0.8438 | 0.8438 | 0 | YES with reviewed-path override |
| Reviewed lexical NDCG@3 | 0.8450 | 0.8450 | 0 | YES with reviewed-path override |
| Reviewed ModernBERT P@3/R@3/NDCG@3 | 0.5417/0.9583/0.9025 | same | 0 | YES with optional dependencies and reviewed-path override |
| Floor 0.02 greedy coverage/mean/total | 0.6562/2.1429/45 | same | 0 | YES with reviewed path |
| Floor 0.02 global coverage/mean/total | 0.7812/2.0800/52 | same | 0 | YES with reviewed path |
| Matching agreement 243/256, kappa 0.9756 | aggregate values | metadata only | n/a | NEEDS MORE EVIDENCE; raw sheets absent |
| Usability 70.8% plus retest metrics | documented values | no raw result rows | n/a | NO public reproduction |

Scaling method is reproducible, but exact timing is not portable. Current 25/100/400/800/1600 median times were 0.111/0.717/10.652/54.624/266.907 ms versus documented 0.177/0.648/8.390/47.887/546.314 ms on a different Linux/SciPy environment.

## 9. Documentation-versus-code mismatches

1. README and Technical Report cite frozen reviewed retrieval/allocation metrics, but both committed evaluators default to `matching_benchmark_v1_draft.json`.
2. `api/experiment.py` and the live Allocation Lab display draft grades and `team_review_pending`.
3. CI's matching experiment validates the draft benchmark, not the claimed final reviewed table.
4. Intent documentation says 96 balanced examples; runtime training sees 95 because one CSV row is malformed.
5. Gate documentation says 48/48; runtime training sees 48/46 because two CSV rows are malformed.
6. The annotation validator is described as available but fails the committed intent seed and does not support gate labels.
7. `docs/dataset_card.md` still describes matching review as pending/small after the frozen benchmark was added.
8. README says bilingual dynamic states are supported; manual TR audit found English ARIA labels and service labels.
9. Reported usability and reviewer aggregates lack public raw anonymized inputs, so they are documented evidence rather than repository-reproducible evidence.

## 10. Security and quality findings

| Severity | Finding | Evidence / impact | Recommendation |
| --- | --- | --- | --- |
| High before production | No authentication or responder identity | Any client can submit/reset capacity state and Accept/Pause another configured responder ID | Add platform identity and server-authoritative state before real users |
| High | Duplicate batch IDs violate capacity semantics | Two requests with ID `dup` both returned `r_backend` despite a single allocation decision | Reject duplicates at schema boundary and test it |
| High before URL retrieval | SOURCECHAIN fetch security is only documented | No fetcher exists yet; SSRF, DNS rebinding, redirect, size, content-type and prompt-injection controls are not implemented | Build a dedicated allowlisted fetch boundary before arbitrary URLs |
| Medium | Request body read is unbounded before validation | `Content-Length` bytes are read and JSON-decoded before the 1200-char/20-item rules | Cap body bytes before reading; add timeouts and structured schemas |
| Medium | No rate limit, abuse quota or request ownership | Public serverless endpoint can repeatedly train/load/call the routing path | Cache cold models and add platform/server rate limits |
| Medium | Browser/session state is race-prone | Cross-tab/device Accept/Pause updates can diverge or overwrite each other | Transactional storage, version checks and idempotency keys |
| Medium | Dependency resolution is unpinned | Latest scikit-learn changed classifier results; no lock/SBOM in repo | Pin tested ranges/lock and record environment with every result |
| Medium | Data validation is not a CI gate | Malformed CSV rows are silently ignored by training | Validate all datasets and fail on dropped rows |
| Medium future XSS surface | `web/lab.js` interpolates API strings into `innerHTML` without escaping | Current API data are static repository fixtures, so present exploitability is limited; future dynamic evidence would be unsafe | Use `textContent`/DOM builders or strict escaping and CSP |
| Low/defense in depth | Static pages lack CSP, X-Content-Type-Options, frame and referrer policy | Live headers provide HSTS but little browser hardening | Add Vercel headers after UI compatibility test |
| Low | Error responses expose exception class names | Aids probing but not stack disclosure | Log server-side correlation IDs; return stable public codes |

No hardcoded secrets were found by repository pattern scan. `pip-audit` found no known vulnerability in the resolved third-party environment on 2026-08-24; the local package itself is not a PyPI audit target. There is no current SSRF surface because no URL fetcher exists.

## 11. Technical debt

- Mixed product, experiment and benchmark state in browser code.
- Module-level model training during API cold start.
- Ad-hoc dictionaries rather than versioned request/response schemas.
- No durable request, assignment, outcome or evidence model.
- No typed unmatched/escalation reasons.
- No lock file, lint, type check, coverage threshold or API test harness.
- Dataset scripts do not share one schema/validator.
- Several stale documents and branches preserve obsolete states without a clear archive marker.
- No benchmark result artifact generated directly by CI for review.

## 12. Reusable components

Reuse without rewrite:

- `IntentType`, responder and candidate domain concepts.
- TF-IDF/LogisticRegression baseline builder and group-aware split functions after data repair/version pinning.
- Weighted lexical retriever as a cheap NIYET fallback.
- Hard willingness, active-state and capacity eligibility logic.
- Greedy allocator and SciPy global allocator with dummy assignments.
- Allocation metrics and threshold-sensitivity experiment.
- Matching review/freeze workflow after provenance hardening.
- Existing `/api` compatibility behavior, Vercel project shape and NSosyal-style UI shell.
- Mobile responder drawer, correction points and progressive technical-detail pattern.

## 13. Components requiring refactor

- Add strict versioned schemas around all API dictionaries.
- Separate server-authoritative state transitions from pure allocation.
- Make benchmark path/version explicit CLI input; never hardcode draft data in final workflows.
- Split data validators by task while sharing CSV structural checks.
- Separate runtime model construction from per-request orchestration and cache it safely.
- Convert unsafe Lab HTML interpolation to DOM/text rendering.
- Introduce a DRSK orchestration contract that wraps NIYET rather than renaming or burying it.

## 14. Missing SOURCECHAIN components

All are currently **NOT IMPLEMENTED** unless marked otherwise:

- statement/opinion/experience/check-worthiness classification;
- atomic claim extraction;
- real-document retrieval and passage retrieval/reranking;
- canonical URL and provenance capture;
- claim-passage SUPPORTED/PARTIALLY_SUPPORTED/CONFLICTING/INSUFFICIENT alignment;
- source mismatch;
- structured numeric, temporal, certainty, causality, scope and attribution distortion checks;
- claim evolution and evidence lineage;
- evidence cache/store and immutable Evidence Bundle;
- citation-first explanation;
- Evidence Panel, Evidence Explorer and Distortion Lens;
- SOURCEBENCH-TR annotation, freeze, baselines, challenge set and calibration.

## 15. Missing DRSK Resolution components

- a top-level orchestrator that can select SOURCECHAIN, NIYET, both or neither;
- explicit evidence sufficiency policy and typed reasons;
- contested/insufficient transition into an opt-in human request;
- structured claim/topic/entity transfer into NIYET;
- human contribution of an additional source/passage;
- evidence-bundle revision history after human contribution;
- loop prevention, idempotency, audit events and ownership;
- end-to-end resolution acceptance tests.

## 16. Current-to-target gap analysis

### Target requirements matrix

| Target area | Requirement | Current repository status | Required proof |
| --- | --- | --- | --- |
| DRSK core | Shared schemas and orchestrator | NOT IMPLEMENTED | Contract tests and end-to-end API |
| DRSK core | Evidence sufficiency and next-path decision | NOT IMPLEMENTED | Typed resolution policy tests |
| SOURCECHAIN | Statement classification/check-worthiness | NOT IMPLEMENTED | Frozen grouped benchmark and per-class metrics |
| SOURCECHAIN | Atomic claim extraction | NOT IMPLEMENTED | Span-linked golden tests |
| SOURCECHAIN | Document and passage retrieval | NOT IMPLEMENTED | Real-source provenance plus Recall@K/NDCG |
| SOURCECHAIN | Claim-evidence alignment | NOT IMPLEMENTED | Four-way relation benchmark and calibration analysis |
| SOURCECHAIN | Source mismatch | NOT IMPLEMENTED | Attribution hard pairs and UNKNOWN cases |
| SOURCECHAIN | Numeric/semantic distortion | NOT IMPLEMENTED | Structured numeric tests and typed distortion F1 |
| SOURCECHAIN | Claim evolution and lineage | NOT IMPLEMENTED | Version graph and origin-cluster audit |
| SOURCECHAIN | Citation-first explanation | NOT IMPLEMENTED | Zero invented URL/passage acceptance test |
| SOURCECHAIN UI | Evidence Panel/Explorer/Distortion Lens | NOT IMPLEMENTED | Desktop/mobile/a11y user flow |
| NIYET | Response-needed and intent | IMPLEMENTED with broken seed rows | Validated frozen inputs and pinned result artifact |
| NIYET | Retrieval/willingness/capacity/allocation | IMPLEMENTED for prototype | Reviewed benchmark and capacity tests |
| NIYET | Responder controls | PARTIALLY IMPLEMENTED | Server-authoritative Accept/Skip/Pause tests |
| Resolution | SOURCECHAIN to NIYET escalation | NOT IMPLEMENTED | Insufficient/contested opt-in scenario |
| Resolution | Structured topic/entity/claim transfer | NOT IMPLEMENTED | Adapter contract test |
| Resolution | Human-provided evidence update | NOT IMPLEMENTED | Immutable bundle-version test |
| Data/research | SOURCEBENCH-TR and annotation protocol | NOT IMPLEMENTED | Dataset card, raw/frozen hashes and agreement |
| Data/research | Leakage-resistant split/challenge set | DOCUMENTED target only | Event/source grouping checks |
| Data/research | Baseline comparison/calibration | NOT IMPLEMENTED for SOURCECHAIN | Machine-readable experiment results |
| Data/research | Usability/accessibility evidence | PARTIAL for NIYET | Raw anonymized results and automated/manual audit |
| Engineering | Versioned API/storage/cache/provenance | NIYET API only; rest NOT IMPLEMENTED | Contract, migration and persistence tests |
| Engineering | CI/deployment/security/documentation | PARTIAL | Clean build, security suite, evidence ledger |

| Capability | Current status | Reusable? | Missing work | Risk | Priority |
| --- | --- | --- | --- | --- | --- |
| NIYET classification/routing | IMPLEMENTED / PARTIAL | Yes | Repair data, schemas, state and CI | Medium | P0 |
| NIYET durable capacity/outcomes | NOT IMPLEMENTED | Allocator yes | Transactional store and identity | High | P1 |
| DRSK orchestrator | NOT IMPLEMENTED | NIYET runtime | Typed route decision and contracts | High | P0 |
| SOURCECHAIN statement gate | NOT IMPLEMENTED | Classifier pattern | Dataset, baseline, calibration | High | P0 |
| Atomic claims | NOT IMPLEMENTED | No | Turkish rules/model and span schema | High | P0 |
| Evidence retrieval/passages | NOT IMPLEMENTED | ModernBERT candidate | Secure fetch/index, passages, ranking | Critical | P0 |
| Alignment/status | NOT IMPLEMENTED | ModernBERT candidate | Four-way relation baseline and benchmark | Critical | P0 |
| Provenance/Evidence Bundle | NOT IMPLEMENTED | No | Immutable source/passage metadata | Critical | P0 |
| Citation-first explanation | NOT IMPLEMENTED | UI pattern | Templates constrained to bundle IDs | High | P0 |
| Resolution escalation | NOT IMPLEMENTED | NIYET route path | Sufficiency decision and transfer | Critical | P0 |
| Source mismatch/numeric distortion | NOT IMPLEMENTED | No | Rules plus evaluated classifier | High | P1 |
| Distortion Lens | MOCK target only | UI shell | Product UI and typed transforms | Medium | P2 |
| Evidence lineage/evolution | NOT IMPLEMENTED | No | Canonicalization, similarity clusters, version graph | High | P2 |
| Multimodal/deepfake/truth score/reputation/blockchain | Out of report scope | No | None | Scope distraction | DO NOT BUILD |

## 17. Architectural conflicts and migration

| Current design | Target design | Conflict | Recommended migration | Breaking? |
| --- | --- | --- | --- | --- |
| `/api` accepts NIYET routing payloads | One DRSK orchestrator | Existing clients expect flat NIYET response | Add versioned DRSK envelope while preserving legacy NIYET adapter | No initially |
| Browser-supplied responder state | Central DRSK/NIYET state | Evidence escalation may span users/devices | Introduce state repository interface; keep session adapter for demo | No initially |
| `src/niyet` is top-level | `src/drsk`, `src/sourcechain`, `src/niyet` | None if NIYET stays separate | Add sibling packages and depend inward from `drsk` | No |
| Vercel sync request runtime | Async cold evidence path | Web retrieval/model latency exceeds serverless request budget | P0 bounded/cached sources; later queue/worker abstraction | No for NIYET |
| Static JSON responder profiles | Structured topic/entity transfer | Human escalation needs claim context | Extend request schema; do not overload intent text | Yes for new API only |
| Free-form frontend dictionaries | Traceable Evidence Bundle | UI cannot prove source/passage binding | Render only bundle schema; forbid explanation-only sources | Yes for evidence UI |
| ModernBERT experiment on CPU | Potential production reranking | Model size/latency may exceed Vercel budget | Keep offline/worker or ONNX candidate; measure first | No |

## 18. TEKNOFEST evidence map

| Criterion | Required proving artifact |
| --- | --- |
| Technical competence | Versioned architecture, schemas, executable end-to-end tests, CI, live DRSK prototype, measured latency |
| Innovation | Typed source mismatch/distortion, lineage audit, evidence-to-human transition test; not broad first-ever claims |
| Problem solving | Frozen SOURCEBENCH-TR, baseline comparisons, error analysis, NIYET reviewed allocation benchmark |
| Scientific method | Leakage-resistant split, independent labels, adjudication, frozen data hashes, raw result artifacts |
| UI/UX | Evidence progressive disclosure, keyboard/mobile/a11y audit, task protocol and anonymized raw results |
| Feasibility | Bounded retrieval/allocation, queue/cache design, measured p50/p95, serverless/worker boundary |
| Safety | Fetch threat model, SSRF tests, citation faithfulness, consent/capacity/abuse controls |
| Sustainability | Cheap-to-expensive gating, cache-hit measurement, deployment bill/compute evidence, not forecasts |

## 19. Top 10 critical risks

1. Building SOURCECHAIN breadth before a frozen evidence schema and benchmark.
2. Losing source/passage provenance and emitting an explanation that cannot be traced.
3. Treating weak/conflicting evidence as a binary truth verdict.
4. Secure URL retrieval: SSRF, redirects, DNS rebinding, oversized/hostile content and prompt injection.
5. Report-to-code drift caused by draft benchmark defaults and unversioned result artifacts.
6. Classification data corruption and dependency drift invalidating claimed baselines.
7. Insufficient, leakage-prone Turkish evidence data under the competition schedule.
8. Browser/session capacity and duplicate-ID races producing incorrect human allocations.
9. Vercel/model latency and memory constraints forcing an unmeasured architecture shortcut.
10. Missing raw human-study/reviewer evidence weakening defensibility even when aggregate numbers are correct.

## 20. Recommended priorities

P0 is an end-to-end defensible slice, not all SOURCECHAIN features:

1. Repair and freeze the NIYET baseline contract: CSV structure, validator, dependency lock, reviewed benchmark CLI/default and CI.
2. Add DRSK, SOURCECHAIN and Evidence Bundle schemas with provenance-first invariants.
3. Implement statement gate -> atomic claim -> bounded real-source retrieval -> passage ranking -> relation -> Evidence Bundle.
4. Produce citation-first explanations only from bundle evidence IDs.
5. Implement a deterministic Resolution Engine: sufficient -> evidence panel; insufficient/contested -> optional NIYET escalation.
6. Transfer structured claim/topic/entity fields to NIYET without changing its internal allocator contract.
7. Add end-to-end API/UI path and acceptance tests, including no-source hallucination and duplicate-ID rejection.
8. Freeze a minimum SOURCEBENCH-TR evaluation set and publish raw machine results before claiming performance.

Production code was not changed during this audit.

### GitHub issue actions

- Keep #2 open and narrow it to repaired, independently reviewed, frozen intent data.
- Split #4 into “gate implementation” (complete after regression proof) and “gate dataset/validation hardening”.
- Update #3 into the DRSK evidence ledger umbrella issue.
- Update #5 to remaining outcome feedback, localization and automated accessibility/browser checks.
- Mark #6 superseded by DRSK and link this audit plus the new report.
- Create: `Repair NIYET data integrity and reviewed benchmark CI`.
- Create: `Define DRSK/Evidence Bundle schemas and provenance invariants`.
- Create: `Build secure bounded evidence ingestion and passage extraction`.
- Create: `Build and freeze SOURCEBENCH-TR v1`.
- Create: `Implement SOURCECHAIN alignment and citation-first Evidence Bundle`.
- Create: `Implement DRSK Resolution Engine and opt-in NIYET escalation`.
- Create: `Move NIYET capacity and outcomes to server-authoritative state` (P1, not P0 demo blocker).
