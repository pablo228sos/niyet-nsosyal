from __future__ import annotations

import json
from pathlib import Path

from experiments.evaluate_sourcebench_v1 import evaluate_sourcebench_v1
from scripts.validate_sourcebench import validate_sourcebench

ROOT = Path(__file__).resolve().parents[1]
DATA_V1 = ROOT / "data" / "sourcebench_tr_v1"


def test_sourcebench_v1_files_exist_and_validate():
    problems = validate_sourcebench(DATA_V1)
    assert problems == [], f"Validation problems found: {problems}"


def test_sourcebench_v1_splits_disjointness_and_coverage():
    splits_path = DATA_V1 / "splits.json"
    assert splits_path.is_file()

    data = json.loads(splits_path.read_text(encoding="utf-8"))
    splits = data["splits"]

    train_ids = set(splits["train"])
    dev_ids = set(splits["dev"])
    test_ids = set(splits["test"])

    # Disjointness
    assert train_ids.isdisjoint(dev_ids)
    assert train_ids.isdisjoint(test_ids)
    assert dev_ids.isdisjoint(test_ids)

    # Total coverage
    all_split_ids = train_ids | dev_ids | test_ids
    assert len(all_split_ids) == 111

    # Verify no source group leakage
    id_to_group = {}
    for filename in ("statement_types.jsonl", "alignment.jsonl", "distortion.jsonl"):
        for line in (DATA_V1 / filename).read_text(encoding="utf-8").splitlines():
            if line.strip():
                item = json.loads(line)
                id_to_group[item["id"]] = item["source_group"]

    train_groups = {id_to_group[i] for i in train_ids}
    dev_groups = {id_to_group[i] for i in dev_ids}
    test_groups = {id_to_group[i] for i in test_ids}

    assert train_groups.isdisjoint(dev_groups)
    assert train_groups.isdisjoint(test_groups)
    assert dev_groups.isdisjoint(test_groups)


def test_sourcebench_v1_adjudication_log():
    adj_path = DATA_V1 / "adjudication_log.json"
    assert adj_path.is_file()

    log = json.loads(adj_path.read_text(encoding="utf-8"))
    assert log["benchmark_version"] == "SOURCEBENCH-TR-v1"
    assert log["raw_agreement_rate"] >= 0.90
    assert log["quadratic_weighted_cohen_kappa"] >= 0.90
    assert len(log["disagreements"]) > 0


def test_sourcebench_v1_evaluation_runner():
    res_test = evaluate_sourcebench_v1(DATA_V1, split="test")
    assert res_test["dataset_version"] == "SOURCEBENCH-TR-v1"
    assert res_test["split_evaluated"] == "test"
    assert res_test["total_examples"] == 22
    assert "statement_type" in res_test["tasks"]
    assert "alignment" in res_test["tasks"]
    assert "distortion" in res_test["tasks"]

    res_all = evaluate_sourcebench_v1(DATA_V1, split="all")
    assert res_all["total_examples"] == 111
