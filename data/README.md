# Data directory

This folder contains development data, annotation templates and benchmark fixtures used by DRSK / NIYET.

## Files

### `intent_annotations_template.csv`

Blank annotation sheet. It intentionally contains only the header row.

We keep it empty so a new annotation pass starts without labels copied from a previous dataset. Use `intent_annotations_example.csv` to see the expected format.

### `intent_annotations_example.csv`

Four small filled examples showing how the annotation columns are used. These rows are documentation examples, not evaluation data.

### `intent_seed_v1.csv`

Controlled Turkish development set for the four positive response intents:

- ASK
- FEEDBACK
- COLLABORATE
- DISCUSS

Related phrasings share the same `source_group`. Group-aware splitting keeps related examples on the same side of train/test evaluation.

### `intent_challenge_v1.csv`

Harder Turkish challenge examples with shorter wording, informal language, Turkish-English code switching and closer class boundaries.

This set is kept separate from the clean seed set so style sensitivity is easier to see.

### `response_gate_seed_v1.csv`

Controlled Turkish development set for the binary response-needed gate:

- RESPONSE
- NONE

This gate runs before four-way intent classification. It prevents normal posts from being forced into one of the response-seeking classes.

### `responder_profiles_v1.json`

Eight synthetic responder profiles used by the prototype and matching benchmark. Profiles include explicit topic areas, allowed interaction types and attention capacity.

They are synthetic product fixtures. They are not real NSosyal accounts.

### `matching_benchmark_v1_draft.json`

First 32-query Turkish matching benchmark draft.

Each query contains a 0-3 relevance grade for every responder profile. Current status: `team_review_pending`.

Results from this file remain development results until the team reviews and freezes the labels.

### Blind matching review

Generate two separate blind sheets:

```bash
python scripts/export_matching_review.py --reviewer A --output reviewer_a.csv
python scripts/export_matching_review.py --reviewer B --output reviewer_b.csv
```

Each reviewer fills only the `relevance` column with:

- 0: incompatible
- 1: weak
- 2: good
- 3: excellent

The reviewer files do not contain the draft benchmark grades.

After both independent passes:

```bash
python scripts/merge_matching_reviews.py reviewer_a.csv reviewer_b.csv --output adjudication.csv
```

This reports exact agreement and quadratic weighted Cohen's kappa. Rows where reviewers agree receive an automatic `final_relevance`; disagreements are left blank for third-person adjudication.

After every disagreement has a final grade:

```bash
python scripts/freeze_matching_benchmark.py \
  --benchmark data/matching_benchmark_v1_draft.json \
  --adjudication adjudication.csv \
  --output data/matching_benchmark_v1_reviewed.json
```

The frozen output is a new version. Do not overwrite the draft source file.

### `matching_review_template.csv`

Small documentation example of the matching-review format. Use the exporter above for the complete reviewer sheets.

### `toy_benchmark.json`

Small machine-readable fixture used to test benchmark code and allocation metrics. It is not large enough to support a competition claim.

### `usability_results_template.csv`

Blank result sheet for the six-task protocol in `docs/usability_test_protocol.md`.

It stores anonymous participant IDs, task completion, time, wrong clicks, hints and clarity ratings. Participant names are not required.

After the sessions:

```bash
python scripts/summarize_usability.py usability_results.csv
```

The summary reports task-level completion without hints, median task time and clarity ratings. Observed confusions should still be reviewed qualitatively before deciding UI changes.

## Label convention

Intent labels are stored in uppercase in CSV annotation files: `ASK`, `FEEDBACK`, `COLLABORATE`, `DISCUSS`.

Runtime enums use lowercase serialized values internally. The annotation validator normalizes casing before validation.

## Data rules

1. We do not place private messages, personal contact details or private profile data in the repository.
2. Related paraphrases share a source group.
3. Evaluation splits are group-aware to reduce near-duplicate leakage.
4. Controlled or team-written examples are labeled as such. We do not describe them as organic NSosyal data.
5. Model metrics are reported with the exact dataset version and evaluation script used to produce them.
6. External model benchmark scores are not copied into DRSK results.
7. A development result becomes a report result only after the corresponding labels and data version are frozen for that experiment.
8. Synthetic responder profiles are never described as real platform users.
9. Reviewer sheets are kept separate until both independent passes are complete.
10. Reviewed labels are frozen into a new benchmark version rather than silently replacing the development draft.
