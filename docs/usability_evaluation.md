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
