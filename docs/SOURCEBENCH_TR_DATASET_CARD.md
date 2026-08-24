# SOURCEBENCH-TR v0 Dataset Card

## Summary

SOURCEBENCH-TR v0 is a small, team-authored development set used to lock basic SOURCECHAIN behavior. It contains no scraped personal data and makes no claim of population or topic representativeness.

Files:

- `statement_types.jsonl`: factual, opinion, experience, prediction, question and mixed examples;
- `alignment.jsonl`: supported, partial, conflicting and insufficient claim-passage pairs;
- `distortion.jsonl`: causality, certainty, numeric, scope and unchanged parent-child pairs.

Each row records a unique ID, language, label and `team-authored-development-example` origin. The validator rejects invalid JSON, missing text, duplicate IDs and labels outside the closed task vocabulary.

## Appropriate use

- deterministic unit/regression tests;
- validating schema and pipeline plumbing;
- documenting annotation targets before a larger study.

## Inappropriate use

- reporting general model accuracy;
- training or selecting a production model;
- claiming representativeness of Turkish social media;
- evaluating source reliability or user credibility.

## Known limitations and next version

v0 is intentionally tiny and contains constructed cases. SOURCEBENCH-TR v1 should add independently annotated, legally usable examples; event/source grouping; train/dev/test separation; source provenance; hard topical negatives; agreement statistics; and an adjudication log. Any benchmark metric must name the exact frozen version and split.

## Validation

```bash
python scripts/validate_sourcebench.py data/sourcebench_tr
```
