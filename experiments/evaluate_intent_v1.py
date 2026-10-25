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

from niyet.classifier import build_tfidf_baseline

INTENT_LABELS = ("ASK", "FEEDBACK", "COLLABORATE", "DISCUSS")


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

    # Confusion matrix
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


def evaluate_intent_v1(dataset_dir: str | Path) -> dict[str, Any]:
    dataset_dir = Path(dataset_dir)
    csv_file = dataset_dir / "intent_dataset_v1.csv"
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

    train_texts = [r["text"] for r in train_rows]
    train_labels = [r["final_label"] for r in train_rows]

    # Fit TF-IDF model on train split
    model = build_tfidf_baseline()
    model.fit(train_texts, train_labels)

    results_by_split: dict[str, Any] = {}
    for split_name, s_rows in [("train", train_rows), ("dev", dev_rows), ("test", test_rows), ("all", all_rows)]:
        s_texts = [r["text"] for r in s_rows]
        s_preds = model.predict(s_texts)

        cases = []
        for r, pred in zip(s_rows, s_preds):
            cases.append({
                "example_id": r["example_id"],
                "text": r["text"],
                "gold": r["final_label"],
                "predicted": pred,
                "correct": pred == r["final_label"],
                "source_group": r["source_group"],
            })

        results_by_split[split_name] = {
            "metrics": _compute_metrics(cases, INTENT_LABELS),
            "cases": cases,
        }

    dataset_hash = hashlib.sha256(csv_file.read_bytes()).hexdigest()

    return {
        "dataset_version": "TURKISH-INTENT-V1",
        "dataset_sha256": dataset_hash,
        "splits": {
            "train_count": len(train_rows),
            "dev_count": len(dev_rows),
            "test_count": len(test_rows),
            "total_count": len(all_rows),
        },
        "results": results_by_split,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "turkish_intent_v1")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments" / "turkish_intent_v1_evaluation.json")
    args = parser.parse_args()

    result = evaluate_intent_v1(args.dataset)
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

    # Print summary table
    print("\nTURKISH-INTENT-V1 EVALUATION SUMMARY:")
    for s_name in ("train", "dev", "test"):
        m = result["results"][s_name]["metrics"]
        print(f"  {s_name.upper()} Split: Accuracy={m['accuracy']:.4f} ({m['correct']}/{m['total']}), Macro F1={m['macro_f1']:.4f}")
        for lbl in INTENT_LABELS:
            pm = m["per_class"][lbl]
            print(f"    {lbl:12s}: Prec={pm['precision']:.4f}, Rec={pm['recall']:.4f}, F1={pm['f1']:.4f} (support={pm['support']})")


if __name__ == "__main__":
    main()
