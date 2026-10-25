# Technical Report Evidence Audit Matrix

This document provides complete, auditable traceability for all 14 evaluation criteria required by the technical report, resolving issue **#3** (*Track the technical report evidence*).

Every empirical claim, architecture contract, evaluation metric, dataset provenance split, and baseline in the technical report is mapped to concrete repository files, frozen JSON result artifacts, sha256 checksums, and reproducible scripts.

---

## Audit Summary

- **Audit Date:** 2026-10-25
- **Status:** **ALL 14 CRITERIA VERIFIED (100% COMPLIANT)**
- **Total Files Audited:** 56 distinct repository artifacts
- **Audit Runner:** `scripts/audit_technical_report_evidence.py`
- **Result Artifact:** `results/technical_report_evidence_audit.json`
- **Verification Gate:** `tests/test_technical_report_evidence.py`

---

## Traceability Matrix (14 Mandatory Criteria)

### 1. Problem Statement and Prior Work
- **Scope:** Empirical foundation for social disinformation, lack of resolution in feeds, and scholarly prior art.
- **Repository Artifacts:**
  - `docs/problem_evidence.md` (Grounding on Joyce & Kraut 2006 newcomer participation study; Klimashevskaia et al. 2024 recommender popularity bias; NSosyal platform scale and scope).
  - `docs/prior_art.md` (Prior art in social task routing like CrowdSTAR [Nushi et al. 2015], reciprocal recommender systems [Palomares et al. 2021], and long-tail exposure fairness).
- **Audit Verification:** Confirmed citations, DOI links, and defensive problem boundaries preventing overclaiming.

### 2. Novelty Claim and Competitor Comparison
- **Scope:** Precise differentiation of DRSK from existing fact-checking systems (Community Notes, Full Fact) and standard feed recommenders.
- **Repository Artifacts:**
  - `docs/comparison_matrix.md` (Detailed feature-by-feature matrix across Standard Feeds, CrowdSTAR, Reciprocal Recommenders, and NIYET).
  - `docs/PRODUCT_THESIS.md` ("Distribution is not resolution" thesis; SOURCECHAIN as exact claim-evidence alignment; author/reader/responder roles).
- **Audit Verification:** Verified comparison criteria (interaction intent, hard capacity constraints, batch assignment, load concentration metrics).

### 3. Repository History and Architecture
- **Scope:** Clean separation of concerns, engine ownership boundaries, and immutable logs of engineering iterations.
- **Repository Artifacts:**
  - `docs/DRSK_ARCHITECTURE.md` (System contract definitions: `sourcechain`, `niyet`, `drsk`, `api`, `web`, and `StateStore`).
  - `docs/architecture.md` (Component data flow and failure recovery).
  - `docs/ENGINEERING_JOURNEY.md` (Evolution across browser testing, multi-device sync, and retrieval boundary hardening).
- **Audit Verification:** Verified architectural boundary adherence and state-store decoupling.

### 4. Data Provenance and Split Rules
- **Scope:** Clear dataset cards, annotation guidelines, and frozen splits with zero leakage.
- **Repository Artifacts:**
  - `docs/data_card.md` (Provenance documentation, licensing, collection methods).
  - `docs/dataset_card.md` (Core dataset attributes and curation protocol).
  - `docs/SOURCEBENCH_TR_DATASET_CARD.md` (Evaluation benchmark card for Turkish claim-evidence alignment).
  - `docs/annotation.md` (Annotation guidelines for human annotators).
  - `data/intent_seed_v1.csv` & `data/response_gate_seed_v1.csv` (Seed corpora).
  - `data/sourcebench_tr/` (`alignment.jsonl`, `distortion.jsonl`, `statement_types.jsonl`).
  - `data/matching_benchmark_v1_reviewed.json` & `data/toy_benchmark.json`.
- **Audit Verification:** All CSV/JSONL records verified for schema compliance and non-empty splits.

### 5. Classifier Metrics and Baselines
- **Scope:** Offline classification baselines, model cards, and reproducibly frozen metrics.
- **Repository Artifacts:**
  - `docs/model_choice.md` (Rationale for lightweight, deterministic on-device TF-IDF models).
  - `docs/SOURCECHAIN_MODEL_CARD.md` (SOURCECHAIN model scope, safe refusal, truth disclaimer).
  - `experiments/intent_seed_v1.md` & `experiments/response_gate_seed_v1.md`.
  - `results/sourcechain_v0.json` (Frozen baseline evaluation metrics).
- **Audit Verification:** JSON metric schema valid, non-zero F1/accuracy measurements verified.

### 6. Matching and Allocation Baselines
- **Scope:** Formal mathematical formulation and reviewed baseline benchmarks.
- **Repository Artifacts:**
  - `docs/allocation_formulation.md` (Formulation of utility $u_{ij} = \frac{\text{relevance} + \text{availability}}{2}$, capacity constraints $\sum_i x_{ij} \le c_j$).
  - `results/niyet_allocation_reviewed.json` (Frozen reviewed results: global coverage **0.7812**, greedy coverage **0.6562**, batch size **8**).
  - `results/niyet_retrieval_reviewed.json` (Frozen reviewed results: Precision@3 **0.4688**, Recall@3 **0.8438**, NDCG@3 **0.8450**).
  - `src/niyet/allocator.py`, `src/niyet/optimizer.py`, `src/niyet/scoring.py`.
- **Audit Verification:** Numerical exact-match verification against committed JSON files.

### 7. Efficiency and Fairness Metrics
- **Scope:** Analysis of global vs. greedy optimization, responder load distribution, and attention conservation.
- **Repository Artifacts:**
  - `docs/impact_and_metrics.md` (Metrics: Intent coverage, relevant match rate, responder overload count = 0, load Gini).
  - `experiments/evaluate_matching_draft.py` & `experiments/global_vs_greedy.py`.
  - `results/niyet_allocation_reviewed.json`.
- **Audit Verification:** Load Gini and global allocator coverage improvement confirmed.

### 8. Target Users and User Flow
- **Scope:** Realistic user journeys across author, reader, and responder roles with visual proof.
- **Repository Artifacts:**
  - `docs/product_flow.md` (End-to-end 6-stage lifecycle: composer -> check -> resolution -> post -> explicit ask -> responder inbox).
  - `docs/DRSK_DEMO.md` (Step-by-step reproducible jury demo guide).
  - `docs/screenshots/01_live_coffee_conflict.png` (Live visual capture).
  - `web/index.html` & `web/app.js` (Working client surfaces).
- **Audit Verification:** DOM elements, language switcher, and distortion lenses confirmed in frontend code.

### 9. Accessibility Decisions and WCAG Contracts
- **Scope:** Inclusive design system, visible focus indicators, screen-reader semantics, and reduced motion.
- **Repository Artifacts:**
  - `docs/ui_design_rationale.md` (Why DRSK avoids dark patterns and AI dashboards).
  - `web/design-system.css` (Contract tokens: `--color-bg-canvas`, `--color-sourcechain-accent`, `--color-niyet-accent`, `--color-drsk-accent`, `:focus-visible`, `@media (prefers-reduced-motion: reduce)`).
  - `tests/test_web_ui_contract.py` (Automated UI accessibility contract test).
- **Audit Verification:** Passing pytest contract tests for all design tokens and accessibility media queries.

### 10. Usability Test Plan and Results
- **Scope:** Protocol, task scenarios, Likert evaluations, and completion metrics.
- **Repository Artifacts:**
  - `docs/usability_test_protocol.md` (Task protocols across author, evidence inspection, and responder roles).
  - `docs/usability_evaluation.md` (Empirical task completion rates and feedback).
  - `data/usability_results_template.csv` (Standardized recording template).
- **Audit Verification:** Protocol documentation verified complete.

### 11. Scalability Assumptions and Production Boundaries
- **Scope:** External API bounds, latency budgets, fail-closed mechanics, and verified CI test execution.
- **Repository Artifacts:**
  - `docs/runtime_provider_setup.md` (Tavily, Brave, Upstash Redis configuration; state durability verification).
  - `docs/FINAL_ACCEPTANCE.md` (Verified snapshot, GitHub Actions run #601 passed, 286 full suite passed).
  - `docs/REAL_NSOSYAL_ACCEPTANCE.md` (Hardware DOM inspection on real NSosyal).
  - `experiments/benchmark_scaling.py` & `experiments/scaling_results_v1.md`.
- **Audit Verification:** Runtime configuration verified; all provider secrets isolated to server-side env.

### 12. Sustainability and Cost Assumptions
- **Scope:** Unit economics, serverless operational expenditure, and platform value model.
- **Repository Artifacts:**
  - `docs/business_model.md` (Platform integration value, institutional mentorship pools, zero user paywalls, embedding inference cost bounds).
- **Audit Verification:** Verified absence of speculative ad revenue claims; sound unit economics based on candidate pre-filtering.

### 13. Project Timeline and Team Roles
- **Scope:** Transparent work breakdown structure, team member ownership, and milestone schedules.
- **Repository Artifacts:**
  - `docs/team_roles.md` (Ownership split: Developer A [ML & Data], Developer B [Backend & Optimization], Product Designer [UI/UX & Access]).
  - `docs/roadmap.md` (Work packages WP1-WP5 tied to milestone deliverables).
- **Audit Verification:** Anonymized roles and delivery milestones confirmed.

### 14. Academic and Technical References
- **Scope:** Scholarly citations, Internet standards, and official algorithmic references.
- **Repository Artifacts:**
  - `docs/prior_art.md`, `docs/allocation_formulation.md`, `docs/SOURCECHAIN_MODEL_CARD.md`, `docs/safety_and_failure_modes.md`.
- **Key Citations Verified:**
  - Joyce & Kraut (2006), *Predicting Continued Participation in Newsgroups*, JCMC.
  - Nushi et al. (2015), *Crowd-STAR: A Social Task Routing Framework for Online Communities*, ICWE.
  - Palomares et al. (2021), *Reciprocal Recommender Systems*, Information Fusion.
  - Klimashevskaia et al. (2024), *A Survey on Popularity Bias in Recommender Systems*.
  - Kuhn (1955), *The Hungarian Method for the Assignment Problem*.
  - Cohen (1960), *A Coefficient of Agreement for Nominal Scales*.
  - RFC 5321 (SMTP), RFC 7239 (Forwarded HTTP), RFC 9110 (HTTP Semantics).

---

## Automated Verification

To run the audit locally:

```bash
python scripts/audit_technical_report_evidence.py
```

To run the pytest regression test:

```bash
pytest tests/test_technical_report_evidence.py
```
