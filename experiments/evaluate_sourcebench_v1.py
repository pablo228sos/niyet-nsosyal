from __future__ import annotations

import argparse
import hashlib
import json
import os
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

from sourcechain.alignment import align_claim
from sourcechain.statement_classifier import classify_statement
from sourcechain.structured_checks import detect_distortions

FILES = ("statement_types.jsonl", "alignment.jsonl", "distortion.jsonl")


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _compute_metrics(cases: list[dict], labels: list[str]) -> dict[str, Any]:
    total = len(cases)
    if total == 0:
        return {"total": 0, "correct": 0, "accuracy": None, "macro_f1": None}

    correct = sum(item["correct"] for item in cases)
    accuracy = round(correct / total, 4)

    # Per-class counts
    gold_counts = Counter(item["gold"] for item in cases)
    pred_counts = Counter(item["predicted"] for item in cases)
    tp_counts = Counter(item["gold"] for item in cases if item["correct"])

    per_class = {}
    f1_list = []
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


def evaluate_sourcebench_v1(
    root: str | Path,
    *,
    split: str = "all",
) -> dict[str, Any]:
    root = Path(root)
    splits_file = root / "splits.json"
    allowed_ids = None
    if splits_file.exists() and split in {"train", "dev", "test"}:
        splits_data = json.loads(splits_file.read_text(encoding="utf-8"))
        allowed_ids = set(splits_data.get("splits", {}).get(split, []))

    cases: list[dict] = []
    by_task: dict[str, list[dict]] = {"statement_type": [], "alignment": [], "distortion": []}

    # 1. Statement Type
    st_labels = ["FACTUAL_CLAIM", "OPINION", "PERSONAL_EXPERIENCE", "PREDICTION", "QUESTION", "MIXED"]
    for row in _rows(root / "statement_types.jsonl"):
        if allowed_ids is not None and row["id"] not in allowed_ids:
            continue
        predicted = classify_statement(row["text"]).value
        case = {
            "id": row["id"],
            "task": "statement_type",
            "gold": row["label"],
            "predicted": predicted,
            "correct": predicted == row["label"],
            "source_group": row.get("source_group"),
        }
        cases.append(case)
        by_task["statement_type"].append(case)

    # 2. Alignment
    al_labels = ["SUPPORTED", "PARTIALLY_SUPPORTED", "CONFLICTING", "INSUFFICIENT"]
    for row in _rows(root / "alignment.jsonl"):
        if allowed_ids is not None and row["id"] not in allowed_ids:
            continue
        predicted = align_claim(row["claim"], row["passage"]).value
        gold = row["label"]
        case = {
            "id": row["id"],
            "task": "alignment",
            "gold": gold,
            "predicted": predicted,
            "correct": predicted == gold,
            "source_group": row.get("source_group"),
        }
        cases.append(case)
        by_task["alignment"].append(case)

    # 3. Distortion
    dt_labels = [
        "NONE",
        "CERTAINTY_SHIFT",
        "CAUSALITY_SHIFT",
        "NUMERIC_DISTORTION",
        "SCOPE_SHIFT",
        "ATTRIBUTION_SHIFT",
        "TEMPORAL_SHIFT",
    ]
    for row in _rows(root / "distortion.jsonl"):
        if allowed_ids is not None and row["id"] not in allowed_ids:
            continue
        predicted_values = [item.value for item in detect_distortions(row["child_text"], row["parent_text"])]
        best_pred = predicted_values[0] if predicted_values else "NONE"
        correct = row["label"] in predicted_values if predicted_values else (row["label"] == "NONE")
        case = {
            "id": row["id"],
            "task": "distortion",
            "gold": row["label"],
            "predicted": best_pred,
            "predicted_set": predicted_values,
            "correct": correct,
            "source_group": row.get("source_group"),
        }
        cases.append(case)
        by_task["distortion"].append(case)

    task_metrics = {
        "statement_type": _compute_metrics(by_task["statement_type"], st_labels),
        "alignment": _compute_metrics(by_task["alignment"], al_labels),
        "distortion": _compute_metrics(by_task["distortion"], dt_labels),
    }

    digest = hashlib.sha256()
    for filename in FILES:
        digest.update(filename.encode("utf-8"))
        digest.update((root / filename).read_bytes())

    return {
        "dataset_version": "SOURCEBENCH-TR-v1",
        "split_evaluated": split,
        "dataset_sha256": digest.hexdigest(),
        "total_examples": len(cases),
        "tasks": task_metrics,
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "sourcebench_tr_v1")
    parser.add_argument("--split", choices=["all", "train", "dev", "test"], default="test")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = evaluate_sourcebench_v1(args.dataset, split=args.split)
    result["generated_at"] = datetime.now(UTC).isoformat()
    try:
        result["git_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        result["git_commit"] = "unknown"

    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
