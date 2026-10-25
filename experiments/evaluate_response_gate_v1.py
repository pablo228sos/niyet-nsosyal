from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from niyet.response_gate import ResponseGate

GATE_LABELS = ("RESPONSE", "NONE")


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

    confusion = {g: {p: 0 for p in labels} for g in labels}
    for c in cases:
        confusion[c["gold"]][c["predicted"]] += 1

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_class": per_class,
        "confusion_matrix": confusion,
    }


def _slice_analysis(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyzes error slices by sub-types of negative and positive posts."""
    slices: dict[str, list[dict[str, Any]]] = {
        "contains_question_mark": [],
        "no_question_mark": [],
        "rhetorical_question": [],
        "news_headline": [],
        "promotional_or_announcement": [],
        "personal_status": [],
        "general_opinion": [],
    }

    for c in cases:
        txt = c["text"]
        grp = c.get("source_group", "")

        if "?" in txt:
            slices["contains_question_mark"].append(c)
        else:
            slices["no_question_mark"].append(c)

        if "rhetorical" in grp:
            slices["rhetorical_question"].append(c)
        elif "news" in grp:
            slices["news_headline"].append(c)
        elif "promo" in grp:
            slices["promotional_or_announcement"].append(c)
        elif "status" in grp:
            slices["personal_status"].append(c)
        elif "opinion" in grp or "quote" in grp or "humor" in grp:
            slices["general_opinion"].append(c)

    results = {}
    for name, s_cases in slices.items():
        if s_cases:
            total = len(s_cases)
            correct = sum(1 for c in s_cases if c["correct"])
            results[name] = {
                "total": total,
                "correct": correct,
                "accuracy": round(correct / total, 4),
            }
    return results


def evaluate_response_gate_v1(dataset_dir: str | Path) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    csv_file = dataset_dir / "response_gate_dataset_v1.csv"
    splits_file = dataset_dir / "splits.json"

    with csv_file.open(encoding="utf-8", newline="") as h:
        all_rows = list(csv.DictReader(h))

    splits_data = json.loads(splits_file.read_text(encoding="utf-8"))["splits"]
    train_ids = set(splits_data.get("train", []))
    dev_ids = set(splits_data.get("dev", []))
    test_ids = set(splits_data.get("test", []))

    train_rows = [r for r in all_rows if r["example_id"] in train_ids]
    dev_rows = [r for r in all_rows if r["example_id"] in dev_ids]
    test_rows = [r for r in all_rows if r["example_id"] in test_ids]

    gate = ResponseGate(threshold=0.50, random_state=42)
    gate.fit(train_rows)

    # Threshold sweep on dev split
    thresholds = [round(0.20 + 0.05 * i, 2) for i in range(13)]
    sweep_results = []
    best_thr = 0.50
    best_f1 = -1.0

    for thr in thresholds:
        dev_cases = []
        for r in dev_rows:
            dec = gate.decide(r["text"], custom_threshold=thr)
            dev_cases.append({
                "example_id": r["example_id"],
                "text": r["text"],
                "gold": r["final_label"],
                "predicted": dec.label,
                "correct": dec.label == r["final_label"],
                "probability": dec.probability,
                "source_group": r["source_group"],
            })
        m = _compute_metrics(dev_cases, GATE_LABELS)
        sweep_results.append({
            "threshold": thr,
            "accuracy": m["accuracy"],
            "macro_f1": m["macro_f1"],
            "response_precision": m["per_class"]["RESPONSE"]["precision"],
            "response_recall": m["per_class"]["RESPONSE"]["recall"],
            "none_precision": m["per_class"]["NONE"]["precision"],
            "none_recall": m["per_class"]["NONE"]["recall"],
        })
        if m["macro_f1"] > best_f1:
            best_f1 = m["macro_f1"]
            best_thr = thr

    results_by_split: dict[str, Any] = {}
    for split_name, s_rows in [("train", train_rows), ("dev", dev_rows), ("test", test_rows), ("all", all_rows)]:
        s_cases = []
        for r in s_rows:
            dec = gate.decide(r["text"], custom_threshold=best_thr)
            s_cases.append({
                "example_id": r["example_id"],
                "text": r["text"],
                "gold": r["final_label"],
                "predicted": dec.label,
                "correct": dec.label == r["final_label"],
                "probability": dec.probability,
                "source_group": r["source_group"],
            })
        results_by_split[split_name] = {
            "metrics": _compute_metrics(s_cases, GATE_LABELS),
            "slices": _slice_analysis(s_cases),
            "cases": s_cases,
        }

    dataset_hash = hashlib.sha256(csv_file.read_bytes()).hexdigest()

    return {
        "dataset_version": "TURKISH-RESPONSE-GATE-V1",
        "dataset_sha256": dataset_hash,
        "splits": {
            "train_count": len(train_rows),
            "dev_count": len(dev_rows),
            "test_count": len(test_rows),
            "total_count": len(all_rows),
        },
        "optimal_threshold": {
            "calibrated_threshold": best_thr,
            "selection_criterion": "Maximizing Macro F1 on Dev split while preventing false positive routing on normal posts",
        },
        "threshold_sweep_dev": sweep_results,
        "results": results_by_split,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "turkish_response_gate_v1")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments" / "turkish_response_gate_v1_evaluation.json")
    args = parser.parse_args()

    result = evaluate_response_gate_v1(args.dataset)
    result["generated_at"] = datetime.now(UTC).isoformat()
    try:
        result["git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        result["git_commit"] = "unknown"

    json_payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json_payload, encoding="utf-8")
        print(f"Written results to {args.output}")

    # Summary table
    print("\nTURKISH-RESPONSE-GATE-V1 EVALUATION SUMMARY:")
    print(f"Optimal Decision Threshold (tuned on Dev): {result['optimal_threshold']['calibrated_threshold']}")
    for s_name in ("train", "dev", "test"):
        m = result["results"][s_name]["metrics"]
        print(f"  {s_name.upper()} Split: Accuracy={m['accuracy']:.4f} ({m['correct']}/{m['total']}), Macro F1={m['macro_f1']:.4f}")
        for lbl in GATE_LABELS:
            pm = m["per_class"][lbl]
            print(f"    {lbl:12s}: Prec={pm['precision']:.4f}, Rec={pm['recall']:.4f}, F1={pm['f1']:.4f} (support={pm['support']})")

    print("\nHARD NEGATIVE SLICE ACCURACY (All Data):")
    for s_name, s_data in result["results"]["all"]["slices"].items():
        print(f"    {s_name:28s}: {s_data['accuracy']:.4f} ({s_data['correct']}/{s_data['total']})")


if __name__ == "__main__":
    main()
