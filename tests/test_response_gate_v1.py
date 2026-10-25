from __future__ import annotations

import json
from pathlib import Path

import pytest

from niyet.response_gate import ResponseGate, ResponseGateDecision
from niyet.runtime import NiyetRuntime
from scripts.validate_response_gate_v1 import validate_response_gate_v1
from experiments.evaluate_response_gate_v1 import evaluate_response_gate_v1

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "turkish_response_gate_v1"


def test_response_gate_v1_validation():
    problems = validate_response_gate_v1(DATA_DIR)
    assert problems == [], f"Validation failed with problems: {problems}"


def test_response_gate_splits_disjointness():
    splits_file = DATA_DIR / "splits.json"
    data = json.loads(splits_file.read_text(encoding="utf-8"))
    splits = data["splits"]
    group_map = data.get("example_to_group", {})

    train_ids = set(splits["train"])
    dev_ids = set(splits["dev"])
    test_ids = set(splits["test"])

    # ID disjointness
    assert train_ids.isdisjoint(dev_ids)
    assert train_ids.isdisjoint(test_ids)
    assert dev_ids.isdisjoint(test_ids)

    # Group disjointness
    if group_map:
        train_groups = {group_map[eid] for eid in train_ids if eid in group_map}
        dev_groups = {group_map[eid] for eid in dev_ids if eid in group_map}
        test_groups = {group_map[eid] for eid in test_ids if eid in group_map}

        assert train_groups.isdisjoint(dev_groups)
        assert train_groups.isdisjoint(test_groups)
        assert dev_groups.isdisjoint(test_groups)


def test_response_gate_adjudication_log():
    log_file = DATA_DIR / "adjudication_log.json"
    log = json.loads(log_file.read_text(encoding="utf-8"))

    assert log["raw_agreement_rate"] >= 0.95
    assert log["cohens_kappa"] >= 0.90
    assert log["disagreement_count"] == len(log["disagreements"])


def test_response_gate_classifier_decide():
    csv_file = DATA_DIR / "response_gate_dataset_v1.csv"
    gate = ResponseGate.from_csv(csv_file)

    # Clear help-seeking post
    help_text = "Çizgi izleyen robotum virajlarda salınım yapıyor. PID ayarına nereden başlamalıyım?"
    prob_help = gate.predict_probability(help_text)
    dec_help = gate.decide(help_text)

    assert prob_help >= 0.50
    assert dec_help.response_needed is True
    assert dec_help.label == "RESPONSE"
    assert dec_help.probability == prob_help

    # Clear status/announcement post
    status_text = "Bugün prototipin ilk benchmark koşusunu tamamladık. Sonuçları yarın paylaşacağız."
    prob_status = gate.predict_probability(status_text)
    dec_status = gate.decide(status_text)

    assert prob_status < 0.50
    assert dec_status.response_needed is False
    assert dec_status.label == "NONE"


def test_runtime_with_response_gate():
    runtime = NiyetRuntime()

    # Normal post: gate blocks routing
    normal_res = runtime.route("Bugün prototipin ilk benchmark koşusunu tamamladık. Sonuçları yarın paylaşacağız.")
    assert normal_res.response_needed is False
    assert normal_res.gate_probability is not None
    assert normal_res.gate_probability < 0.50
    assert normal_res.intent is None

    # Help post: gate allows routing
    help_res = runtime.route("Çizgi izleyen robotum virajlarda salınım yapıyor. PID ayarına nereden başlamalıyım?")
    assert help_res.response_needed is True
    assert help_res.gate_probability is not None
    assert help_res.gate_probability >= 0.50
    assert help_res.intent == "ask"


def test_response_gate_evaluation_runner():
    res = evaluate_response_gate_v1(DATA_DIR)

    test_metrics = res["results"]["test"]["metrics"]
    assert test_metrics["accuracy"] >= 0.80
    assert test_metrics["macro_f1"] >= 0.80

    # Ensure hard negative slices are evaluated
    all_slices = res["results"]["all"]["slices"]
    assert "rhetorical_question" in all_slices
    assert "news_headline" in all_slices
    assert all_slices["rhetorical_question"]["accuracy"] >= 0.90
