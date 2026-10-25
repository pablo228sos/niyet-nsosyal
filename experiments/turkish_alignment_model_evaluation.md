# Turkish Claim-Evidence Alignment Evaluation Report

## Executive Summary
This report benchmarks the Turkish Claim-Evidence Alignment baseline against the task-specific calibrated `TurkishAlignmentClassifier` on frozen **SOURCEBENCH-TR v1** data.

- **Benchmark Version:** `SOURCEBENCH-TR-v1`
- **Task:** 4-way Claim-Evidence Alignment (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONFLICTING`, `INSUFFICIENT`)
- **Dataset SHA256:** `48a27328efde9f0844347434e1d1fcb6218bf58078dc4ddad0f1a714b1283c25`
- **Disjoint Partitioning:** 24 Train / 8 Dev / 8 Test (disjoint source groups)

### Primary Test Split Performance
| Metric | Lexical / Heuristic Baseline | Turkish Alignment Model | Delta |
| :--- | :--- | :--- | :--- |
| **Accuracy** | 0.5000 (4/8) | **0.8750** (7/8) | **+0.3750** |
| **Macro F1** | 0.2875 | **0.8667** | **+0.5792** |
| **Brier Score** | N/A | **0.2596** | - |
| **Expected Calibration Error (ECE)** | N/A | **0.1343** | - |

---

## Per-Class Metrics (Test Split)
| Class | Support | Baseline Prec / Rec / F1 | Model Prec / Rec / F1 |
| :--- | :--- | :--- | :--- |
| `SUPPORTED` | 1 | 0.0 / 0.0 / 0.0 | **1.0** / **1.0** / **1.0** |
| `PARTIALLY_SUPPORTED` | 2 | 0.3333 / 0.5 / 0.4 | **0.6667** / **1.0** / **0.8** |
| `CONFLICTING` | 2 | 0.0 / 0.0 / 0.0 | **1.0** / **0.5** / **0.6667** |
| `INSUFFICIENT` | 3 | 0.6 / 1.0 / 0.75 | **1.0** / **1.0** / **1.0** |

---

## Calibration Limits & Semantic Safety
> [!IMPORTANT]
> **Truth Probability Guardrail:** Alignment predictions measure entailment/contradiction with respect to the supplied evidence passage only. Outputs must **never** be presented as real-world truth probabilities.

- **High Confidence Gate:** Max probability >= 0.70 (eligible for automated resolution).
- **Audit Limit:** Max probability < 0.55 (flagged for human verification).
- **Test Set ECE:** `0.1343`.
- **Multi-class Brier Score:** `0.2596`.

---

## Error Slice Breakdown (All 40 Evaluated Examples)
| Slice Dimension | Slice Group | Total | Baseline Accuracy | Model Accuracy |
| :--- | :--- | :--- | :--- | :--- |
| **Numeric Content** | Numeric Facts Present | 19 | 0.2632 | **0.8421** |
| | Numeric Facts Absent | 21 | 0.4762 | **0.8095** |
| **Polarity / Negation** | Negation Present | 6 | 0.0 | **0.6667** |
| | Negation Absent | 34 | 0.4412 | **0.8529** |
| **Passage Verbosity** | Short Passage (<12 tokens) | 10 | 0.8 | **1.0** |
| | Long Passage (>=12 tokens) | 30 | 0.2333 | **0.7667** |
| **Lexical Overlap** | High Overlap (>= 0.5) | 9 | 0.1111 | **0.8889** |
| | Low Overlap (< 0.25) | 19 | 0.5263 | **0.7368** |
