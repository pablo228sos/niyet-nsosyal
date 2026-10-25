from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.evaluate_alignment_models import (
    _analyze_error_slices,
    _compute_calibration,
    _compute_metrics,
    run_alignment_evaluation,
)
from sourcechain.alignment_model import (
    RELATION_CLASSES,
    AlignmentPrediction,
    TurkishAlignmentClassifier,
    extract_alignment_features,
    has_turkish_negation,
)
from sourcechain.schemas import EvidenceRelation

ROOT = Path(__file__).resolve().parents[1]
DATA_V1 = ROOT / "data" / "sourcebench_tr_v1"


def test_alignment_feature_extraction_contract():
    claim = "Türkiye'de yıllık enflasyon yüzde 48 olarak açıklandı."
    passage = "TÜİK bültenine göre yıllık enflasyon yüzde 48 seviyesinde."

    features = extract_alignment_features(claim, passage)
    assert isinstance(features, dict)

    expected_keys = {
        "token_overlap",
        "p_token_overlap",
        "stem_overlap",
        "p_stem_overlap",
        "trigram_jaccard",
        "claim_negated",
        "passage_negated",
        "polarity_mismatch",
        "negation_conflict",
        "numeric_match",
        "numeric_mismatch",
        "numeric_missing",
        "fact_match",
        "year_match",
        "year_mismatch",
        "antonym_conflict",
        "lexical_score",
        "exact_match",
        "length_ratio",
    }
    assert expected_keys.issubset(set(features.keys()))

    for key, val in features.items():
        assert isinstance(val, (int, float)), f"Feature {key} is not numeric"
        assert not isinstance(val, bool)


def test_has_turkish_negation():
    # Lexical negation
    assert has_turkish_negation("Bu iddia doğru değildir.")
    assert has_turkish_negation("Elimizde hiçbir kanıt yok.")

    # Morphological participle negation
    assert has_turkish_negation("Risklerin artmadığını ortaya koydu.")
    assert has_turkish_negation("Herhangi bir ilerleme sağlanamadı.")

    # Affirmative controls
    assert not has_turkish_negation("Proje başarıyla tamamlandı.")
    assert not has_turkish_negation("Enflasyon yüzde 15 yükseldi.")


def test_unfitted_classifier_fallback():
    clf = TurkishAlignmentClassifier()
    assert not clf.is_fitted

    pred = clf.predict("Test claim.", "Test passage.")
    assert isinstance(pred, AlignmentPrediction)
    assert isinstance(pred.relation, EvidenceRelation)
    assert "fallback" in pred.rationale.lower()
    assert sum(pred.probabilities.values()) == pytest.approx(1.0, abs=1e-5)


def test_turkish_alignment_classifier_fit_and_predict():
    train_records = [
        {"claim": "A 10 birim arttı.", "passage": "A tam 10 birim arttı.", "label": "SUPPORTED"},
        {"claim": "B 20 birim arttı.", "passage": "B 20 birim arttı fakat C azaldı.", "label": "PARTIALLY_SUPPORTED"},
        {"claim": "C durduruldu.", "passage": "C seferleri artırılarak sürdürüldü.", "label": "CONFLICTING"},
        {"claim": "D yeni yöntem geliştirdi.", "passage": "Hava durumu açık ve güneşli.", "label": "INSUFFICIENT"},
    ]

    clf = TurkishAlignmentClassifier(random_state=42)
    clf.fit(train_records)
    assert clf.is_fitted

    pred = clf.predict("A 10 birim arttı.", "A tam 10 birim arttı.")
    assert isinstance(pred, AlignmentPrediction)
    assert pred.relation in (
        EvidenceRelation.SUPPORTED,
        EvidenceRelation.PARTIALLY_SUPPORTED,
        EvidenceRelation.CONFLICTING,
        EvidenceRelation.INSUFFICIENT,
    )
    assert 0.0 <= pred.confidence <= 1.0

    # Invariant: probabilities must sum to 1.0
    prob_sum = sum(pred.probabilities.values())
    assert prob_sum == pytest.approx(1.0, abs=1e-4)

    # Invariant: all 4 classes must be represented in probabilities
    for cls_name in RELATION_CLASSES:
        assert cls_name in pred.probabilities


def test_semantic_truth_probability_guardrail():
    """Verifies that predictions explicitly disclaim being truth probabilities."""
    clf = TurkishAlignmentClassifier(random_state=42)
    pred = clf.predict("Claim", "Passage")

    warning = pred.truth_probability_warning
    assert "NOT real-world factuality or truth probability" in warning
    assert "claim-passage alignment only" in warning

    as_dict = pred.to_dict()
    assert "truth_probability_warning" in as_dict
    assert as_dict["truth_probability_warning"] == warning


def test_metrics_computation_empty_and_valid():
    empty_res = _compute_metrics([], RELATION_CLASSES)
    assert empty_res["total"] == 0
    assert empty_res["accuracy"] == 0.0

    cases = [
        {"gold": "SUPPORTED", "predicted": "SUPPORTED", "correct": True},
        {"gold": "CONFLICTING", "predicted": "INSUFFICIENT", "correct": False},
    ]
    res = _compute_metrics(cases, RELATION_CLASSES)
    assert res["total"] == 2
    assert res["correct"] == 1
    assert res["accuracy"] == 0.5


def test_calibration_and_error_slices():
    cases = [
        {
            "gold": "SUPPORTED",
            "predicted": "SUPPORTED",
            "correct": True,
            "confidence": 0.90,
            "probabilities": {"SUPPORTED": 0.90, "PARTIALLY_SUPPORTED": 0.05, "CONFLICTING": 0.03, "INSUFFICIENT": 0.02},
            "features": {"numeric_match": 1.0, "claim_negated": 0.0, "passage_negated": 0.0, "token_overlap": 0.7},
            "claim": "Test 1",
            "passage": "Test passage 1 with words",
        },
        {
            "gold": "CONFLICTING",
            "predicted": "INSUFFICIENT",
            "correct": False,
            "confidence": 0.60,
            "probabilities": {"SUPPORTED": 0.10, "PARTIALLY_SUPPORTED": 0.10, "CONFLICTING": 0.20, "INSUFFICIENT": 0.60},
            "features": {"numeric_match": 0.0, "claim_negated": 1.0, "passage_negated": 0.0, "token_overlap": 0.2},
            "claim": "Test 2 not true",
            "passage": "Test passage 2",
        },
    ]

    cal = _compute_calibration(cases, n_bins=5)
    assert "ece" in cal
    assert "brier_score" in cal
    assert "calibration_limits" in cal
    assert 0.0 <= cal["ece"] <= 1.0

    slices = _analyze_error_slices(cases)
    assert "numeric_fact_present" in slices
    assert "numeric_fact_absent" in slices
    assert "negation_present" in slices
    assert "negation_absent" in slices
    assert slices["numeric_fact_present"]["total"] == 1
    assert slices["numeric_fact_present"]["correct"] == 1


def test_full_sourcebench_v1_alignment_evaluation():
    eval_result = run_alignment_evaluation(DATA_V1)
    assert eval_result["benchmark_version"] == "SOURCEBENCH-TR-v1"
    assert eval_result["task"] == "claim_evidence_alignment"

    results = eval_result["results"]
    for split_key in ("train", "dev", "test", "all"):
        assert split_key in results
        split_data = results[split_key]
        assert "baseline" in split_data
        assert "model" in split_data

        b_metrics = split_data["baseline"]["metrics"]
        m_metrics = split_data["model"]["metrics"]
        assert 0.0 <= b_metrics["accuracy"] <= 1.0
        assert 0.0 <= m_metrics["accuracy"] <= 1.0

    # Ensure model beats or matches baseline on test split
    test_model_acc = results["test"]["model"]["metrics"]["accuracy"]
    test_base_acc = results["test"]["baseline"]["metrics"]["accuracy"]
    assert test_model_acc > test_base_acc
