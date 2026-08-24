# DRSK Demo

Run the API/web prototype as described in the README, then exercise these acceptance scenes in the existing feed.

## A — Opinion stays outside evidence verification

Post: `I think this movie is terrible.`

Expected: `OPINION`, no factual evidence badge, resolution `NONE`.

## B — Association is not causation

Post: `Research proves X causes Y.`

Use the controlled evidence passage: `X was associated with Y.`

Expected: the passage and its source remain visible; relation is partial/conflicting; `CAUSALITY_SHIFT` (and certainty shift where detected) is shown; explanation cites the evidence ID.

## C — Conflicting evidence remains visible

Analyze a claim with controlled passages supporting different relations.

Expected: individual passages remain separate; bundle is `CONFLICTING`; resolution is `BOTH` when a human route is requested. No absolute truth score appears.

## D — Evidence-to-human escalation

Analyze a factual claim absent from the controlled corpus, then choose **Ask a relevant person**.

Expected: bundle is `INSUFFICIENT`; DRSK creates structured claim/topic/status context; NIYET runs retrieval, willingness, capacity and allocation; the response identifies a matched responder or honestly reports no match.

## E — Shared capacity

Submit two batch requests that compete for a one-slot responder.

Expected: duplicate request IDs are rejected and one responder slot cannot be assigned twice.

## Verification commands

```bash
pytest -q
node --check web/app.js
node --check web/lab.js
python scripts/validate_annotations.py data/intent_seed_v1.csv
python scripts/validate_annotations.py data/response_gate_seed_v1.csv
python scripts/validate_sourcebench.py data/sourcebench_tr
python experiments/evaluate_matching_draft.py
```
