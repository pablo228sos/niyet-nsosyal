from __future__ import annotations

import json
from pathlib import Path

from scripts.generate_results import build_result_payloads, write_result_payloads


def test_result_generator_emits_four_machine_readable_artifacts(tmp_path: Path) -> None:
    test_summary = {
        "command": ["python", "-m", "pytest", "-q"],
        "exit_code": 0,
        "passed": 73,
        "failed": 0,
    }

    payloads = build_result_payloads(test_summary=test_summary)
    write_result_payloads(payloads, tmp_path)

    expected = {
        "sourcechain_v0.json",
        "niyet_retrieval_reviewed.json",
        "niyet_allocation_reviewed.json",
        "test_summary.json",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected

    for filename in expected:
        value = json.loads((tmp_path / filename).read_text(encoding="utf-8"))
        assert value["generated_at"]
        assert len(value["git_commit"]) == 40
        assert value["parameters"]

    retrieval = json.loads((tmp_path / "niyet_retrieval_reviewed.json").read_text())
    assert retrieval["dataset_version"] == "v1-reviewed"
    assert retrieval["metrics"] == {
        "ndcg_at_3": 0.845,
        "precision_at_3": 0.4688,
        "recall_at_3": 0.8438,
    }

    allocation = json.loads((tmp_path / "niyet_allocation_reviewed.json").read_text())
    assert allocation["parameters"]["similarity_floor"] == 0.02
    assert allocation["metrics"]["global"]["coverage"] == 0.7812
    assert allocation["metrics"]["global"]["total_reviewed_relevance"] == 52
