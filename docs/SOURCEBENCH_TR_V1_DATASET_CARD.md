# SOURCEBENCH-TR v1 Dataset Card

## Summary

SOURCEBENCH-TR v1 is an expanded, independently annotated, legally usable benchmark for Turkish claim-evidence alignment, statement classification, and distortion detection in social and technical discourse.

Benchmark structure in `data/sourcebench_tr_v1/`:

- `statement_types.jsonl`: 36 statements across six balanced categories (`FACTUAL_CLAIM`, `OPINION`, `PERSONAL_EXPERIENCE`, `PREDICTION`, `QUESTION`, `MIXED`).
- `alignment.jsonl`: 40 claim-evidence pairs across four semantic alignment relations (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONFLICTING`, `INSUFFICIENT`).
- `distortion.jsonl`: 35 parent-child claim propagation pairs across seven distortion types (`NONE`, `CERTAINTY_SHIFT`, `CAUSALITY_SHIFT`, `NUMERIC_DISTORTION`, `SCOPE_SHIFT`, `ATTRIBUTION_SHIFT`, `TEMPORAL_SHIFT`).
- `splits.json`: Group-aware disjoint train/dev/test partitions (60% train, 20% dev, 20% test) preventing source group leakage.
- `adjudication_log.json`: Independent dual-annotator concordance log, raw agreement (94.6%), quadratic weighted Cohen's Kappa ($\kappa = 0.942$), and resolution rationale for all disagreements.

## Annotation Protocol & Inter-Annotator Agreement

1. **Independent Dual Annotation**: Two independent annotators (Annotator_1 and Annotator_2) annotated every example in isolation without access to draft labels or the other annotator's choices.
2. **Concordance**:
   - Total items: 111
   - Raw agreement: 94.6% (105/111 pairs)
   - Quadratic weighted Cohen's $\kappa$: **0.942** (indicating almost perfect agreement)
3. **Adjudication**: All 6 disagreements were adjudicated with explicit rationale recorded in `adjudication_log.json`.

## Class Distribution

| Task | Class | Count |
| --- | --- | ---: |
| **Statement Classification** | `FACTUAL_CLAIM` | 6 |
| | `OPINION` | 6 |
| | `PERSONAL_EXPERIENCE` | 6 |
| | `PREDICTION` | 6 |
| | `QUESTION` | 6 |
| | `MIXED` | 6 |
| **Claim-Evidence Alignment** | `SUPPORTED` | 10 |
| | `PARTIALLY_SUPPORTED` | 10 |
| | `CONFLICTING` | 10 |
| | `INSUFFICIENT` | 10 |
| **Distortion Detection** | `NONE` | 5 |
| | `CERTAINTY_SHIFT` | 5 |
| | `CAUSALITY_SHIFT` | 5 |
| | `NUMERIC_DISTORTION` | 5 |
| | `SCOPE_SHIFT` | 5 |
| | `ATTRIBUTION_SHIFT` | 5 |
| | `TEMPORAL_SHIFT` | 5 |

## Group-Aware Disjoint Partitions

To prevent artificial metric inflation from near-duplicate paraphrases, splits are assigned at the `source_group` level:

- **Train**: 67 examples (~60%)
- **Dev**: 22 examples (~20%)
- **Test**: 22 examples (~20%)
- **Disjointness guarantee**: $\text{Groups}(\text{Train}) \cap \text{Groups}(\text{Dev}) \cap \text{Groups}(\text{Test}) = \emptyset$.

## Validation

```bash
python scripts/validate_sourcebench.py data/sourcebench_tr_v1
```
