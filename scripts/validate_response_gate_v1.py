from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from niyet.annotations import validate_annotation_file


def validate_response_gate_v1(dir_path: str | Path) -> list[str]:
    dir_path = Path(dir_path)
    csv_file = dir_path / "response_gate_dataset_v1.csv"
    splits_file = dir_path / "splits.json"
    adj_file = dir_path / "adjudication_log.json"

    problems: list[str] = []

    for f in (csv_file, splits_file, adj_file):
        if not f.exists():
            problems.append(f"Missing required file: {f.name}")
            return problems

    csv_problems = validate_annotation_file(csv_file)
    for p in csv_problems:
        problems.append(f"CSV row {p.row}: {p.message}")

    rows: list[dict[str, str]] = []
    with csv_file.open(encoding="utf-8", newline="") as h:
        rows = list(csv.DictReader(h))

    if len(rows) < 100:
        problems.append(f"Expected at least 100 examples in v1, found {len(rows)}")

    try:
        splits_data = json.loads(splits_file.read_text(encoding="utf-8"))
        splits = splits_data.get("splits", {})
        train_ids = set(splits.get("train", []))
        dev_ids = set(splits.get("dev", []))
        test_ids = set(splits.get("test", []))

        if not train_ids.isdisjoint(dev_ids):
            problems.append("Train and Dev splits share example IDs")
        if not train_ids.isdisjoint(test_ids):
            problems.append("Train and Test splits share example IDs")
        if not dev_ids.isdisjoint(test_ids):
            problems.append("Dev and Test splits share example IDs")

        all_ids = {r["example_id"] for r in rows}
        split_ids = train_ids | dev_ids | test_ids
        if all_ids != split_ids:
            missing = all_ids - split_ids
            extra = split_ids - all_ids
            problems.append(f"Split IDs do not match dataset IDs (missing={len(missing)}, extra={len(extra)})")

        id_to_group = {r["example_id"]: r["source_group"] for r in rows}
        train_groups = {id_to_group[i] for i in train_ids if i in id_to_group}
        dev_groups = {id_to_group[i] for i in dev_ids if i in id_to_group}
        test_groups = {id_to_group[i] for i in test_ids if i in id_to_group}

        if not train_groups.isdisjoint(dev_groups):
            problems.append("Train and Dev share source groups (group leakage!)")
        if not train_groups.isdisjoint(test_groups):
            problems.append("Train and Test share source groups (group leakage!)")
        if not dev_groups.isdisjoint(test_groups):
            problems.append("Dev and Test share source groups (group leakage!)")
    except Exception as exc:
        problems.append(f"Failed to validate splits: {exc}")

    try:
        adj_data = json.loads(adj_file.read_text(encoding="utf-8"))
        raw_agreement = adj_data.get("raw_agreement_rate", 0.0)
        kappa = adj_data.get("cohens_kappa", 0.0)

        if raw_agreement < 0.90:
            problems.append(f"Raw agreement rate below 0.90: {raw_agreement}")
        if kappa < 0.85:
            problems.append(f"Cohen's Kappa below 0.85: {kappa}")

        disagreements = adj_data.get("disagreements", [])
        actual_disagreements = [r for r in rows if r["label_a"] != r["label_b"]]
        if len(disagreements) != len(actual_disagreements):
            problems.append(
                f"Adjudication log disagreement count ({len(disagreements)}) does not match dataset ({len(actual_disagreements)})"
            )
    except Exception as exc:
        problems.append(f"Failed to validate adjudication log: {exc}")

    return problems


def main() -> None:
    target_dir = ROOT / "data" / "turkish_response_gate_v1"
    problems = validate_response_gate_v1(target_dir)
    if problems:
        print("Validation problems encountered:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    print("SUCCESS: TURKISH-RESPONSE-GATE-V1 benchmark passed all validation checks cleanly.")


if __name__ == "__main__":
    main()
