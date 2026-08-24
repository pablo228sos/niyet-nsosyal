from pathlib import Path

from experiments.evaluate_sourcechain_v0 import evaluate_sourcebench


def test_sourcebench_evaluation_is_complete_and_machine_readable():
    root = Path(__file__).resolve().parents[1]
    result = evaluate_sourcebench(root / "data" / "sourcebench_tr")

    assert result["dataset_version"] == "SOURCEBENCH-TR-v0-development"
    assert result["development_only"] is True
    assert result["total_examples"] == 15
    assert result["tasks"]["statement_type"]["total"] == 6
    assert result["tasks"]["alignment"]["total"] == 4
    assert result["tasks"]["distortion"]["total"] == 5
    assert all("accuracy" in task for task in result["tasks"].values())
    assert result["metrics"] == result["tasks"]
    assert len(result["cases"]) == 15
