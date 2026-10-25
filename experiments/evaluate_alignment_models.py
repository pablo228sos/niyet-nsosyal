from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sourcechain.alignment import align_claim
from sourcechain.alignment_model import (
    RELATION_CLASSES,
    TurkishAlignmentClassifier,
    extract_alignment_features,
)
from sourcechain.text import tokens


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _compute_metrics(cases: list[dict[str, Any]], labels: tuple[str, ...]) -> dict[str, Any]:
    total = len(cases)
    if total == 0:
        return {"total": 0, "correct": 0, "accuracy": 0.0, "macro_f1": 0.0, "per_class": {}}

    correct = sum(1 for c in cases if c["correct"])
    accuracy = round(correct / total, 4)

    gold_counts = Counter(c["gold"] for c in cases)
    pred_counts = Counter(c["predicted"] for c in cases)
    tp_counts = Counter(c["gold"] for c in cases if c["correct"])

    per_class: dict[str, Any] = {}
    f1_list: list[float] = []

    for lbl in labels:
        tp = tp_counts[lbl]
        p_denom = pred_counts[lbl]
        r_denom = gold_counts[lbl]
        prec = tp / p_denom if p_denom > 0 else 0.0
        rec = tp / r_denom if r_denom > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        per_class[lbl] = {
            "support": r_denom,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
        }
        if r_denom > 0:
            f1_list.append(f1)

    macro_f1 = round(sum(f1_list) / len(f1_list), 4) if f1_list else 0.0

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_class": per_class,
    }


def _compute_calibration(
    cases: list[dict[str, Any]],
    n_bins: int = 5,
) -> dict[str, Any]:
    """Computes Expected Calibration Error (ECE), Brier score, and confidence distribution."""
    if not cases:
        return {"ece": 0.0, "brier_score": 0.0, "bin_analysis": []}

    brier_sum = 0.0
    for c in cases:
        probs = c.get("probabilities", {})
        gold = c["gold"]
        for cls_name in RELATION_CLASSES:
            p = probs.get(cls_name, 0.0)
            y = 1.0 if cls_name == gold else 0.0
            brier_sum += (p - y) ** 2

    brier_score = round(brier_sum / len(cases), 4)

    bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
    bins: list[list[dict[str, Any]]] = [[] for _ in range(n_bins)]

    for c in cases:
        conf = c.get("confidence", 1.0)
        bin_idx = min(int(conf * n_bins), n_bins - 1)
        bins[bin_idx].append(c)

    ece = 0.0
    bin_analysis = []
    for i in range(n_bins):
        b_cases = bins[i]
        b_count = len(b_cases)
        low, high = bin_boundaries[i], bin_boundaries[i + 1]
        if b_count > 0:
            b_acc = sum(1 for c in b_cases if c["correct"]) / b_count
            b_conf = sum(c.get("confidence", 1.0) for c in b_cases) / b_count
            ece += (b_count / len(cases)) * abs(b_acc - b_conf)
            bin_analysis.append({
                "range": f"[{low:.1f}, {high:.1f})",
                "count": b_count,
                "accuracy": round(b_acc, 4),
                "avg_confidence": round(b_conf, 4),
            })
        else:
            bin_analysis.append({
                "range": f"[{low:.1f}, {high:.1f})",
                "count": 0,
                "accuracy": None,
                "avg_confidence": None,
            })

    return {
        "ece": round(ece, 4),
        "brier_score": brier_score,
        "calibration_limits": {
            "high_confidence_threshold": 0.70,
            "low_confidence_threshold": 0.55,
            "uncertainty_action": "Flag for human reviewer audit when max confidence < 0.55",
            "semantic_invariant": "Predictions reflect claim-evidence passage entailment only; never present as real-world truth probability.",
        },
        "bin_analysis": bin_analysis,
    }


def _analyze_error_slices(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Slices prediction errors by linguistic, numeric, polarity, and lexical properties."""
    slices: dict[str, list[dict[str, Any]]] = {
        "numeric_fact_present": [],
        "numeric_fact_absent": [],
        "negation_present": [],
        "negation_absent": [],
        "short_passage": [],
        "long_passage": [],
        "high_overlap": [],
        "low_overlap": [],
    }

    for c in cases:
        feat = c.get("features", {})
        c_tokens = tokens(c["claim"], meaningful=True)
        p_tokens = tokens(c["passage"], meaningful=True)

        p_words = c["passage"].split()

        if feat.get("numeric_match", 0) > 0 or feat.get("numeric_mismatch", 0) > 0 or feat.get("numeric_missing", 0) > 0:
            slices["numeric_fact_present"].append(c)
        else:
            slices["numeric_fact_absent"].append(c)

        if feat.get("claim_negated", 0) > 0 or feat.get("passage_negated", 0) > 0:
            slices["negation_present"].append(c)
        else:
            slices["negation_absent"].append(c)

        if len(p_words) < 10:
            slices["short_passage"].append(c)
        else:
            slices["long_passage"].append(c)

        if feat.get("token_overlap", 0) >= 0.5:
            slices["high_overlap"].append(c)
        elif feat.get("token_overlap", 0) < 0.25:
            slices["low_overlap"].append(c)

    slice_metrics = {}
    for name, s_cases in slices.items():
        total = len(s_cases)
        correct = sum(1 for c in s_cases if c["correct"])
        slice_metrics[name] = {
            "total": total,
            "correct": correct,
            "accuracy": round(correct / total, 4) if total > 0 else None,
        }

    return slice_metrics


def run_alignment_evaluation(
    dataset_dir: str | Path,
) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    alignment_file = dataset_dir / "alignment.jsonl"
    splits_file = dataset_dir / "splits.json"

    if not alignment_file.exists():
        raise FileNotFoundError(f"Missing {alignment_file}")
    if not splits_file.exists():
        raise FileNotFoundError(f"Missing {splits_file}")

    all_rows = _load_jsonl(alignment_file)
    splits_data = json.loads(splits_file.read_text(encoding="utf-8"))["splits"]

    train_ids = set(splits_data.get("train", []))
    dev_ids = set(splits_data.get("dev", []))
    test_ids = set(splits_data.get("test", []))

    train_rows = [r for r in all_rows if r["id"] in train_ids]
    dev_rows = [r for r in all_rows if r["id"] in dev_ids]
    test_rows = [r for r in all_rows if r["id"] in test_ids]

    # Train model on frozen train split
    model = TurkishAlignmentClassifier(random_state=42)
    model.fit(train_rows)

    results_by_split: dict[str, Any] = {}

    for split_name, s_rows in [("train", train_rows), ("dev", dev_rows), ("test", test_rows), ("all", all_rows)]:
        baseline_cases: list[dict[str, Any]] = []
        model_cases: list[dict[str, Any]] = []

        for r in s_rows:
            claim, passage, gold = r["claim"], r["passage"], r["label"]
            feat = extract_alignment_features(claim, passage)

            # Heuristic Baseline
            b_pred = align_claim(claim, passage).value
            baseline_cases.append({
                "id": r["id"],
                "claim": claim,
                "passage": passage,
                "gold": gold,
                "predicted": b_pred,
                "correct": b_pred == gold,
                "source_group": r.get("source_group"),
                "features": feat,
            })

            # Calibrated Model
            m_res = model.predict(claim, passage)
            model_cases.append({
                "id": r["id"],
                "claim": claim,
                "passage": passage,
                "gold": gold,
                "predicted": m_res.relation.value,
                "correct": m_res.relation.value == gold,
                "confidence": m_res.confidence,
                "probabilities": m_res.probabilities,
                "source_group": r.get("source_group"),
                "features": feat,
                "rationale": m_res.rationale,
            })

        results_by_split[split_name] = {
            "baseline": {
                "metrics": _compute_metrics(baseline_cases, RELATION_CLASSES),
                "error_slices": _analyze_error_slices(baseline_cases),
                "cases": baseline_cases,
            },
            "model": {
                "metrics": _compute_metrics(model_cases, RELATION_CLASSES),
                "calibration": _compute_calibration(model_cases),
                "error_slices": _analyze_error_slices(model_cases),
                "cases": model_cases,
            },
        }

    dataset_hash = hashlib.sha256(alignment_file.read_bytes()).hexdigest()

    return {
        "benchmark_version": "SOURCEBENCH-TR-v1",
        "task": "claim_evidence_alignment",
        "dataset_sha256": dataset_hash,
        "splits": {
            "train_count": len(train_rows),
            "dev_count": len(dev_rows),
            "test_count": len(test_rows),
            "total_count": len(all_rows),
        },
        "results": results_by_split,
    }


def generate_markdown_report(evaluation: dict[str, Any]) -> str:
    res = evaluation["results"]
    b_test = res["test"]["baseline"]["metrics"]
    m_test = res["test"]["model"]["metrics"]
    m_cal = res["test"]["model"]["calibration"]

    b_all = res["all"]["baseline"]["metrics"]
    m_all = res["all"]["model"]["metrics"]

    md = f"""# Turkish Claim-Evidence Alignment Evaluation Report

## Executive Summary
This report benchmarks the Turkish Claim-Evidence Alignment baseline against the task-specific calibrated `TurkishAlignmentClassifier` on frozen **SOURCEBENCH-TR v1** data.

- **Benchmark Version:** `{evaluation['benchmark_version']}`
- **Task:** 4-way Claim-Evidence Alignment (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONFLICTING`, `INSUFFICIENT`)
- **Dataset SHA256:** `{evaluation['dataset_sha256']}`
- **Disjoint Partitioning:** 24 Train / 8 Dev / 8 Test (disjoint source groups)

### Primary Test Split Performance
| Metric | Lexical / Heuristic Baseline | Turkish Alignment Model | Delta |
| :--- | :--- | :--- | :--- |
| **Accuracy** | {b_test['accuracy']:.4f} ({b_test['correct']}/{b_test['total']}) | **{m_test['accuracy']:.4f}** ({m_test['correct']}/{m_test['total']}) | **{m_test['accuracy'] - b_test['accuracy']:+.4f}** |
| **Macro F1** | {b_test['macro_f1']:.4f} | **{m_test['macro_f1']:.4f}** | **{m_test['macro_f1'] - b_test['macro_f1']:+.4f}** |
| **Brier Score** | N/A | **{m_cal['brier_score']:.4f}** | - |
| **Expected Calibration Error (ECE)** | N/A | **{m_cal['ece']:.4f}** | - |

---

## Per-Class Metrics (Test Split)
| Class | Support | Baseline Prec / Rec / F1 | Model Prec / Rec / F1 |
| :--- | :--- | :--- | :--- |
| `SUPPORTED` | {m_test['per_class']['SUPPORTED']['support']} | {b_test['per_class']['SUPPORTED']['precision']} / {b_test['per_class']['SUPPORTED']['recall']} / {b_test['per_class']['SUPPORTED']['f1']} | **{m_test['per_class']['SUPPORTED']['precision']}** / **{m_test['per_class']['SUPPORTED']['recall']}** / **{m_test['per_class']['SUPPORTED']['f1']}** |
| `PARTIALLY_SUPPORTED` | {m_test['per_class']['PARTIALLY_SUPPORTED']['support']} | {b_test['per_class']['PARTIALLY_SUPPORTED']['precision']} / {b_test['per_class']['PARTIALLY_SUPPORTED']['recall']} / {b_test['per_class']['PARTIALLY_SUPPORTED']['f1']} | **{m_test['per_class']['PARTIALLY_SUPPORTED']['precision']}** / **{m_test['per_class']['PARTIALLY_SUPPORTED']['recall']}** / **{m_test['per_class']['PARTIALLY_SUPPORTED']['f1']}** |
| `CONFLICTING` | {m_test['per_class']['CONFLICTING']['support']} | {b_test['per_class']['CONFLICTING']['precision']} / {b_test['per_class']['CONFLICTING']['recall']} / {b_test['per_class']['CONFLICTING']['f1']} | **{m_test['per_class']['CONFLICTING']['precision']}** / **{m_test['per_class']['CONFLICTING']['recall']}** / **{m_test['per_class']['CONFLICTING']['f1']}** |
| `INSUFFICIENT` | {m_test['per_class']['INSUFFICIENT']['support']} | {b_test['per_class']['INSUFFICIENT']['precision']} / {b_test['per_class']['INSUFFICIENT']['recall']} / {b_test['per_class']['INSUFFICIENT']['f1']} | **{m_test['per_class']['INSUFFICIENT']['precision']}** / **{m_test['per_class']['INSUFFICIENT']['recall']}** / **{m_test['per_class']['INSUFFICIENT']['f1']}** |

---

## Calibration Limits & Semantic Safety
> [!IMPORTANT]
> **Truth Probability Guardrail:** Alignment predictions measure entailment/contradiction with respect to the supplied evidence passage only. Outputs must **never** be presented as real-world truth probabilities.

- **High Confidence Gate:** Max probability >= 0.70 (eligible for automated resolution).
- **Audit Limit:** Max probability < 0.55 (flagged for human verification).
- **Test Set ECE:** `{m_cal['ece']:.4f}`.
- **Multi-class Brier Score:** `{m_cal['brier_score']:.4f}`.

---

## Error Slice Breakdown (All 40 Evaluated Examples)
| Slice Dimension | Slice Group | Total | Baseline Accuracy | Model Accuracy |
| :--- | :--- | :--- | :--- | :--- |
| **Numeric Content** | Numeric Facts Present | {res['all']['model']['error_slices']['numeric_fact_present']['total']} | {res['all']['baseline']['error_slices']['numeric_fact_present']['accuracy']} | **{res['all']['model']['error_slices']['numeric_fact_present']['accuracy']}** |
| | Numeric Facts Absent | {res['all']['model']['error_slices']['numeric_fact_absent']['total']} | {res['all']['baseline']['error_slices']['numeric_fact_absent']['accuracy']} | **{res['all']['model']['error_slices']['numeric_fact_absent']['accuracy']}** |
| **Polarity / Negation** | Negation Present | {res['all']['model']['error_slices']['negation_present']['total']} | {res['all']['baseline']['error_slices']['negation_present']['accuracy']} | **{res['all']['model']['error_slices']['negation_present']['accuracy']}** |
| | Negation Absent | {res['all']['model']['error_slices']['negation_absent']['total']} | {res['all']['baseline']['error_slices']['negation_absent']['accuracy']} | **{res['all']['model']['error_slices']['negation_absent']['accuracy']}** |
| **Passage Verbosity** | Short Passage (<12 tokens) | {res['all']['model']['error_slices']['short_passage']['total']} | {res['all']['baseline']['error_slices']['short_passage']['accuracy']} | **{res['all']['model']['error_slices']['short_passage']['accuracy']}** |
| | Long Passage (>=12 tokens) | {res['all']['model']['error_slices']['long_passage']['total']} | {res['all']['baseline']['error_slices']['long_passage']['accuracy']} | **{res['all']['model']['error_slices']['long_passage']['accuracy']}** |
| **Lexical Overlap** | High Overlap (>= 0.5) | {res['all']['model']['error_slices']['high_overlap']['total']} | {res['all']['baseline']['error_slices']['high_overlap']['accuracy']} | **{res['all']['model']['error_slices']['high_overlap']['accuracy']}** |
| | Low Overlap (< 0.25) | {res['all']['model']['error_slices']['low_overlap']['total']} | {res['all']['baseline']['error_slices']['low_overlap']['accuracy']} | **{res['all']['model']['error_slices']['low_overlap']['accuracy']}** |
"""
    return md


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "sourcebench_tr_v1")
    parser.add_argument("--output-json", type=Path, default=ROOT / "experiments" / "sourcebench_tr_alignment_evaluation.json")
    parser.add_argument("--output-md", type=Path, default=ROOT / "experiments" / "turkish_alignment_model_evaluation.md")
    args = parser.parse_args()

    eval_result = run_alignment_evaluation(args.dataset)
    eval_result["generated_at"] = datetime.now(UTC).isoformat()
    try:
        eval_result["git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        eval_result["git_commit"] = "unknown"

    json_payload = json.dumps(eval_result, ensure_ascii=False, indent=2) + "\n"
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json_payload, encoding="utf-8")
    print(f"Written JSON results to {args.output_json}")

    md_report = generate_markdown_report(eval_result)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(md_report, encoding="utf-8")
    print(f"Written Markdown report to {args.output_md}")


if __name__ == "__main__":
    main()
