from __future__ import annotations

import argparse
import csv
from pathlib import Path

from sklearn.metrics import cohen_kappa_score


VALID_GRADES = {0, 1, 2, 3}


def read_sheet(path: Path) -> tuple[dict[str, dict[str, str]], str]:
    rows: dict[str, dict[str, str]] = {}
    reviewer_id = ""
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            pair_id = row["pair_id"].strip()
            if not pair_id:
                continue
            raw_grade = row.get("relevance", "").strip()
            if raw_grade == "":
                raise ValueError(f"{path}: missing relevance for {pair_id}")
            grade = int(raw_grade)
            if grade not in VALID_GRADES:
                raise ValueError(f"{path}: invalid relevance {grade} for {pair_id}")
            row["relevance"] = str(grade)
            rows[pair_id] = row
            reviewer_id = reviewer_id or row.get("reviewer_id", "").strip()
    if not rows:
        raise ValueError(f"{path}: no labeled rows")
    return rows, reviewer_id or path.stem


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reviewer_a", type=Path)
    parser.add_argument("reviewer_b", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows_a, reviewer_a = read_sheet(args.reviewer_a)
    rows_b, reviewer_b = read_sheet(args.reviewer_b)

    if set(rows_a) != set(rows_b):
        missing_a = sorted(set(rows_b) - set(rows_a))
        missing_b = sorted(set(rows_a) - set(rows_b))
        raise ValueError(
            f"pair sets differ; missing from A={missing_a[:5]}, "
            f"missing from B={missing_b[:5]}"
        )

    pair_ids = sorted(rows_a)
    grades_a = [int(rows_a[pair_id]["relevance"]) for pair_id in pair_ids]
    grades_b = [int(rows_b[pair_id]["relevance"]) for pair_id in pair_ids]

    exact = sum(a == b for a, b in zip(grades_a, grades_b, strict=True))
    exact_rate = exact / len(pair_ids)
    weighted_kappa = float(
        cohen_kappa_score(grades_a, grades_b, weights="quadratic")
    )
    disagreement_count = len(pair_ids) - exact

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "pair_id",
        "query_id",
        "intent_type",
        "intent_text",
        "responder_id",
        "responder_name",
        "responder_profile",
        "willing_for_intent",
        "reviewer_a",
        "label_a",
        "reviewer_b",
        "label_b",
        "final_relevance",
        "adjudication_note",
    ]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for pair_id in pair_ids:
            a = rows_a[pair_id]
            b = rows_b[pair_id]
            writer.writerow(
                {
                    "pair_id": pair_id,
                    "query_id": a["query_id"],
                    "intent_type": a["intent_type"],
                    "intent_text": a["intent_text"],
                    "responder_id": a["responder_id"],
                    "responder_name": a["responder_name"],
                    "responder_profile": a["responder_profile"],
                    "willing_for_intent": a["willing_for_intent"],
                    "reviewer_a": reviewer_a,
                    "label_a": a["relevance"],
                    "reviewer_b": reviewer_b,
                    "label_b": b["relevance"],
                    "final_relevance": (
                        a["relevance"] if a["relevance"] == b["relevance"] else ""
                    ),
                    "adjudication_note": "",
                }
            )

    print(f"pairs: {len(pair_ids)}")
    print(f"reviewers: {reviewer_a}, {reviewer_b}")
    print(f"exact_agreement: {exact_rate:.4f}")
    print(f"quadratic_weighted_kappa: {weighted_kappa:.4f}")
    print(f"disagreements_for_adjudication: {disagreement_count}")
    print(f"adjudication_sheet: {args.output}")


if __name__ == "__main__":
    main()
