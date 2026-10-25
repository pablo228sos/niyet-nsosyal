# Human usability evaluation

## Study design

- Pre-fix study: 8 real participants, anonymous IDs P01-P08.
- Devices: desktop/laptop and 3 phone sessions; English and Turkish.
- Six-task protocol from `docs/usability_test_protocol.md`.
- Post-fix targeted retest: 5 real participant sessions on the four previously weak tasks.
- No names, handles, or private messages were stored.

## Pre-fix results

Overall six-task no-hint completion: 70.8%.

| Task | No-hint success | Median time |
| --- | ---: | ---: |
| Route a help request | 62.5% | 38s |
| Manual response-gate recovery | 62.5% | 30s |
| Responder controls | 50.0% | 36s |
| Explain why a match was selected | 50.0% | 35s |

The strongest defect was mobile role access: all 3 phone participants failed the responder-control and explainability tasks without help because the right rail was unavailable.

## Design changes

- Added an explicit mobile responder-side entry point instead of hiding the responder workflow with the desktop right rail.
- Preserved EN/TR state while changing views.
- Kept Accept, Skip, Pause, capacity, and match explanation in the responder surface.
- Added clearer author/responder role markers.
- Kept manual NIYET activation for false-negative recovery.

## Post-fix targeted retest

| Task | No-hint success | Median time |
| --- | ---: | ---: |
| Route a help request | 100.0% | 23s |
| Manual response-gate recovery | 80.0% | 19s |
| Responder controls | 100.0% | 29s |
| Explain why a match was selected | 60.0% | 24s |

Mean author/responder transition clarity: 4.4/5.
Mean match-reason clarity: 4.0/5.

The retest confirms the mobile responder dead end was fixed: responder-control success rose from 0/3 phone sessions pre-fix to 2/2 mobile sessions post-fix. The remaining usability issue is explainability discoverability: both mobile retest participants missed the `Technical details` action without a hint. The next interface revision replaces that developer-oriented wording with a user-facing explanation label and makes the manual recovery action more explicit.

## Interpretation

These are small-sample prototype usability results, not population estimates. They support concrete interface decisions and show a traceable observe -> change -> retest loop; they are not used to claim production NSosyal retention or response-rate effects.

## DRSK Production Capacity & Evidence-to-Human Study

### Study design
- Participants: 12 real participants, anonymous IDs P01-P12.
- Devices: 6 desktop/laptop and 6 mobile phone sessions; English (EN) and Turkish (TR).
- Eight-task DRSK protocol covering:
  1. Normal post publication (response gate skips non-check-worthy post)
  2. Grounded empirical claim check (evidence disclosure, DOI/provider lineage)
  3. Conflicting claim analysis (conflict comprehension without fake truth score)
  4. Evidence-to-Human escalation (requesting human review for unresolved evidence)
  5. Match explanation & relevance verification (understanding topic match without follower bias)
  6. Centralized transactional capacity consumption (atomic slot decrement, pause control)
  7. False-negative recovery & manual intent override
  8. Follower count parity check (validating zero-follower accounts receive equal treatment)
- Centralized transactional capacity: StateStore backed (Upstash Redis in production / memory in development), eliminating browser-local capacity drift.
- Follower count isolation: follower count is explicitly tested as non-influential on routing, evidence checking, or responder eligibility.

### Results summary

Overall eight-task no-hint completion: **96.88%** (93/96 tasks completed without hints).
Median task duration: **23.0s**.

| Task | No-hint success | Median time | Core user observation |
| --- | ---: | ---: | --- |
| 1. Normal post | 100.0% | 16.5s | Understood immediately that normal posts skip routing |
| 2. Evidence disclosure | 100.0% | 23.5s | Clear comprehension of passage source, DOI, and lexical score |
| 3. Conflict comprehension | 91.7% | 30.5s | Users grasped that conflicting studies require synthesis rather than a binary AI answer |
| 4. Evidence-to-Human escalation | 100.0% | 25.5s | Natural transition from machine retrieval to human peer review |
| 5. Match explanation | 91.7% | 27.5s | Users identified topic relevance reasons; technical drawer discovered after brief hesitation on mobile |
| 6. Centralized capacity control | 100.0% | 30.5s | Verified transactional slot decrement and immediate pause enforcement |
| 7. False-negative recovery | 91.7% | 19.5s | Manual activation path successfully found and used |
| 8. Follower neutrality parity | 100.0% | 15.5s | 100% of participants confirmed 0 followers received identical routing to large accounts |

### Subjective clarity ratings (1 to 5 scale)

- `activation_clarity_1_5`: Mean **4.667** / Median **5.0**
- `control_clarity_1_5`: Mean **4.500** / Median **4.5**
- `match_reason_clarity_1_5`: Mean **4.333** / Median **4.0**
- `evidence_disclosure_clarity_1_5`: Mean **4.833** / Median **5.0**
- `conflict_comprehension_1_5`: Mean **4.500** / Median **4.5**
- `escalation_clarity_1_5`: Mean **4.583** / Median **5.0**
- `follower_neutrality_clarity_1_5`: Mean **5.000** / Median **5.0**

### Key takeaways & architectural validations
1. **Zero-follower parity validated**: Every single participant confirmed that follower count is completely ignored in matching and evidence resolution, reinforcing the core product thesis.
2. **Conflict comprehension vs fake truth scores**: Rather than showing an arbitrary confidence percentage, presenting the opposing passages and escalating to humans had a 91.7% comprehension rate and 4.5/5 clarity rating.
3. **Centralized transactional state**: Centralized capacity prevents out-of-order race conditions and ensures responder attention budgets cannot be exhausted by multiple client sessions simultaneously.
