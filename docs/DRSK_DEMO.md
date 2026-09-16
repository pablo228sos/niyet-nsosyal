# DRSK Demo

These scenarios exercise the current bounded prototype without relying on live web search. They are product/engineering smoke tests, not jury-specific scripts.

## A — NONE: opinion stays outside factual verification

Post:

```text
I think this movie is terrible.
```

Expected:

- statement type is subjective/non-checkable
- no evidence is invented
- resolution is `NONE`
- SOURCECHAIN does not create a human escalation automatically

## B — EVIDENCE: exact supported official statement

Post:

```text
Regular physical activity provides significant physical and mental health benefits.
```

Controlled source: World Health Organization, `Physical activity`.

Expected:

- the stored WHO passage is retrieved with its original URL/provenance
- relation is supported
- the bounded path can resolve through `EVIDENCE`
- no truth score appears

## C — BOTH: association is not causation

Post:

```text
Research proves coffee consumption causes lower mortality. Can someone explain what the study actually shows?
```

Controlled source: PubMed / *Circulation*, `Association of Coffee Consumption With Total and Cause-Specific Mortality in 3 Large Prospective Cohorts`.

Expected:

- the exact stored passage says coffee consumption was **associated with** lower mortality risk
- `CAUSALITY_SHIFT` is exposed rather than silently accepting `causes/proves`
- the evidence remains visible
- no human request is created by the evidence check alone
- the author explicitly presses **Ask a relevant person**
- the unresolved interpretation is then routed through NIYET
- resolution is `BOTH`

## D — BOTH: numeric distortion

Post:

```text
A report says industrial activities raised atmospheric carbon dioxide by 90% since 1750.
```

Controlled source: NASA Science, `Causes`.

Expected:

- the stored NASA passage reports **nearly 50% since 1750**
- the changed number is exposed as `NUMERIC_DISTORTION`
- the source passage and provenance remain visible
- the resolution policy can keep evidence while requesting human interpretation (`BOTH`)

## E — HUMAN: honest insufficiency

Post:

```text
ESP32 ultrasonic sensors always detect obstacles at 50 meters. Can someone help me check this?
```

Expected:

- no unrelated controlled passage is presented as proof
- evidence status remains `INSUFFICIENT`
- when human help is requested, structured claim/status context enters NIYET
- the request is routed only to an eligible willing responder with remaining capacity, or remains unmatched honestly
- resolution path is `HUMAN`

## F — Shared-capacity window

Open two or more human-help requests that compete for the same low-capacity responder.

Expected:

- all open/unmatched requests are allocated together as one bounded window
- a one-slot responder cannot be assigned to two accepted requests
- Accept consumes capacity once and pins the accepted request
- Skip triggers reallocation of the still-open request when an alternative exists
- Pause removes the responder from new allocation; Resume restores eligibility only if capacity remains
- a stale Accept/Skip from an older UI snapshot is rejected as a conflict and the UI refreshes the current queue

For a real cross-device/serverless demo, configure the durable Upstash state backend. Without it, the local memory fallback is intentionally reported as process-local.

## Verification commands

```bash
python -m pip install -c constraints.txt -e . pytest
node --check web/app.js
node --check web/lab.js
node --check web/live.js
python -m compileall -q src api scripts experiments
pytest -q
python experiments/evaluate_matching_draft.py
python experiments/evaluate_sourcechain_v0.py
python scripts/validate_annotations.py data/intent_seed_v1.csv
python scripts/validate_annotations.py data/response_gate_seed_v1.csv
python scripts/validate_sourcebench.py data/sourcebench_tr
```

The smoke-test goal is not to force every post into an answer. Correct refusal, `INSUFFICIENT`, `NONE` and an unmatched human request are valid outcomes when the evidence or responder constraints do not support a stronger result.
