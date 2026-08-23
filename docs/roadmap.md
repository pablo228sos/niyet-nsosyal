# Project roadmap

The plan is tied to the competition dates. We keep the technical report stage focused on evidence and a working core, then use the mentoring window to improve the product instead of rewriting the project from zero.

## 22-24 August: technical report stage

### WP1 Problem and prior work
- finish source ledger
- verify every market and research claim
- build the prior-work comparison table
- freeze the narrow novelty claim

Milestone: problem section can be defended without relying on one user review.

### WP2 Data and text models
- response-needed gate seed and baseline
- four-way intent seed and baseline
- team label review
- harder negative and ambiguous examples
- grouped validation and error analysis

Milestone: every reported model number is reproducible from committed data and code.

### WP3 Allocation core
- capacity-aware greedy baseline
- global allocation
- consent/eligibility rules
- baseline runner
- runtime scaling check

Milestone: allocator can be demonstrated on a repeatable benchmark and its operating limits are documented.

### WP4 Technical report
- architecture figure
- user flow figure
- benchmark tables
- sustainability and risk section
- project timeline
- team roles
- reference audit
- template/format audit

Milestone: final file passes the 100-point evidence checklist before KYS upload.

## 25 August-1 September: prototype integration

### WP5 Semantic retrieval
- run ModernBERT-TR-Embed locally
- build responder profile retrieval
- compare against lexical/topic baselines
- measure Precision@K and NDCG@K

### WP6 Working product flow
- composer suggestion
- author intent confirmation
- responder request card
- accept/skip/pause controls
- outcome feedback

Milestone: one complete author-to-responder flow works without manual edits between screens.

## 2-7 September: mentoring and product correction

Use mentor feedback to challenge:
- novelty boundary
- dataset realism
- candidate retrieval
- scale assumptions
- UX friction
- business model

Do not add unrelated features unless mentor evidence shows a core problem.

Milestone: mentor feedback results in tracked changes, not only presentation changes.

## 8-11 September: validation

- expand reviewed matching benchmark
- run baseline comparison
- run usability tasks
- accessibility audit
- failure-case tests
- latency and load checks

Milestone: final presentation uses measured results from the integrated prototype.

## 12-14 September: final submission

- freeze demo build
- final screenshots and video
- presentation
- source-code cleanup
- reproduce metrics from a clean environment
- backup demo path

Milestone: final presentation submission before the official deadline.

## Final-stage rule

A new feature is only added if it improves one of these:
- successful response allocation
- safety or consent
- measurement quality
- usability of the core flow

Everything else is out of scope until the core system is validated.
