from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def fill_relevance(path: Path, value: int) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0].keys())
    for row in rows:
        row["relevance"] = str(value)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_matching_review_can_be_merged_and_frozen(tmp_path: Path):
    reviewer_a = tmp_path / "reviewer_a.csv"
    reviewer_b = tmp_path / "reviewer_b.csv"
    adjudication = tmp_path / "adjudication.csv"
    frozen = tmp_path / "matching_reviewed.json"

    run(
        "scripts/export_matching_review.py",
        "--reviewer",
        "A",
        "--output",
        str(reviewer_a),
    )
    run(
        "scripts/export_matching_review.py",
        "--reviewer",
        "B",
        "--output",
        str(reviewer_b),
    )
    fill_relevance(reviewer_a, 2)
    fill_relevance(reviewer_b, 2)

    merged = run(
        "scripts/merge_matching_reviews.py",
        str(reviewer_a),
        str(reviewer_b),
        "--output",
        str(adjudication),
    )
    assert "exact_agreement: 1.0000" in merged.stdout
    assert "disagreements_for_adjudication: 0" in merged.stdout

    run(
        "scripts/freeze_matching_benchmark.py",
        "--benchmark",
        "data/matching_benchmark_v1_draft.json",
        "--adjudication",
        str(adjudication),
        "--output",
        str(frozen),
    )
    payload = json.loads(frozen.read_text(encoding="utf-8"))
    assert payload["review_status"] == "reviewed"
    assert payload["review_metadata"]["pairs"] == 256
    assert all(
        grade == 2
        for query in payload["queries"]
        for grade in query["relevance"].values()
    )
