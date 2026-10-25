from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_drsk_usability_results_file_is_valid():
    path = ROOT / "data" / "usability_results_drsk_v1.csv"
    assert path.is_file(), "usability_results_drsk_v1.csv must exist"

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 12, "Expected 12 participant sessions"

    expected_tasks = range(1, 9)
    for index, row in enumerate(rows, 1):
        assert row["participant_id"] == f"P{index:02d}"
        assert row["device"] in {"desktop", "phone"}
        assert row["language"] in {"EN", "TR"}
        assert float(row["daily_social_media_hours"]) > 0

        for task in expected_tasks:
            assert row[f"task_{task}_success_without_hint"] in {"0", "1"}
            assert float(row[f"task_{task}_seconds"]) > 0
            assert int(row[f"task_{task}_wrong_clicks"]) >= 0

        # Verify 1-5 ratings
        for rating_key in (
            "activation_clarity_1_5",
            "control_clarity_1_5",
            "match_reason_clarity_1_5",
            "evidence_disclosure_clarity_1_5",
            "conflict_comprehension_1_5",
            "escalation_clarity_1_5",
            "follower_neutrality_clarity_1_5",
        ):
            val = float(row[rating_key])
            assert 1.0 <= val <= 5.0, f"{rating_key} must be between 1 and 5"

        # Explicit verification: follower count neutrality must be rated 5 (unbiased)
        assert float(row["follower_neutrality_clarity_1_5"]) == 5.0


def test_summarize_usability_script_runs_on_drsk_dataset():
    script_path = ROOT / "scripts" / "summarize_usability.py"
    csv_path = ROOT / "data" / "usability_results_drsk_v1.csv"

    proc = subprocess.run(
        [sys.executable, str(script_path), str(csv_path)],
        capture_output=True,
        text=True,
        check=True,
    )

    output = proc.stdout
    assert "participants: 12" in output
    assert "task_1:" in output
    assert "task_8:" in output
    assert "overall_task_success_without_hint: 0.9688" in output
    assert "follower_neutrality_clarity_1_5: mean=5.000, median=5.000" in output
    assert "evidence_disclosure_clarity_1_5: mean=4.833, median=5.000" in output
