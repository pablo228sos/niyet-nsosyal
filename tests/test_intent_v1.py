from __future__ import annotations

import csv
import json
from pathlib import Path

from experiments.evaluate_intent_v1 import evaluate_intent_v1
from scripts.validate_intent_v1 import validate_intent_v1

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "turkish_intent_v1"


def test_intent_v1_files_exist_and_validate():
    problems = validate_intent_v1(DATA_DIR)
    assert problems == [], f"Validation problems found: {problems}"


def test_intent_v1_splits_disjointness_and_group_coverage():
    splits_path = DATA_DIR / "splits.json"
    assert splits_path.is_file()

    data = json.loads(splits_path.read_text(encoding="utf-8"))
    splits = data["splits"]

    train_ids = set(splits["train"])
    dev_ids = set(splits["dev"])
    test_ids = set(splits["test"])

    # Disjointness of example IDs
    assert train_ids.isdisjoint(dev_ids)
    assert train_ids.isdisjoint(test_ids)
    assert dev_ids.isdisjoint(test_ids)

    # Coverage
    assert len(train_ids | dev_ids | test_ids) == 120

    # Group disjointness
    csv_path = DATA_DIR / "intent_dataset_v1.csv"
    id_to_group = {}
    with csv_path.open(encoding="utf-8", newline="") as h:
        for row in csv.DictReader(h):
            id_to_group[row["example_id"]] = row["source_group"]

    train_groups = {id_to_group[i] for i in train_ids}
    dev_groups = {id_to_group[i] for i in dev_ids}
    test_groups = {id_to_group[i] for i in test_ids}

    assert train_groups.isdisjoint(dev_groups)
    assert train_groups.isdisjoint(test_groups)
    assert dev_groups.isdisjoint(test_groups)


def test_intent_v1_adjudication_log():
    adj_path = DATA_DIR / "adjudication_log.json"
    assert adj_path.is_file()

    log = json.loads(adj_path.read_text(encoding="utf-8"))
    assert log["benchmark_version"] == "TURKISH-INTENT-V1"
    assert log["raw_agreement_rate"] >= 0.90
    assert log["cohens_kappa"] >= 0.90
    assert len(log["disagreements"]) > 0


def test_intent_v1_evaluation_runner():
    res = evaluate_intent_v1(DATA_DIR)
    assert res["dataset_version"] == "TURKISH-INTENT-V1"
    assert "splits" in res
    assert "results" in res

    for split_key in ("train", "dev", "test"):
        split_res = res["results"][split_key]
        assert "metrics" in split_res
        metrics = split_res["metrics"]
        assert 0.0 <= metrics["accuracy"] <= 1.0
        assert 0.0 <= metrics["macro_f1"] <= 1.0
        for cls_name in ("ASK", "FEEDBACK", "COLLABORATE", "DISCUSS"):
            assert cls_name in metrics["per_class"]

    # Verify held-out test split performance exceeds baseline threshold
    test_acc = res["results"]["test"]["metrics"]["accuracy"]
    assert test_acc >= 0.85
