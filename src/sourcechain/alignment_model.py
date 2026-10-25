from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from .passage_ranker import lexical_score
from .schemas import EvidenceRelation
from .structured_checks import (
    comparable_numeric_facts,
    has_negation,
    numeric_values,
    years,
)
from .text import normalize, tokens

# Extended Turkish negation pattern capturing lexical negation tokens as well as
# verbal participle infixes with consonant voicing mutations (e.g., -ma-dığı, -me-diği).
_TURKISH_NEGATION_RE = re.compile(
    r"\b(?:değil\w*|degil\w*|yok\w*|asla|hiç\w*|hic\w*)\b|"
    r"\b\w+(?:ma|me|mi)(?:[dıt][iıuüğ]|y[ae]|z|maz|mez)\w*\b",
    re.IGNORECASE,
)

# Common Turkish opposing / antonymous semantic pairs used to detect conflicting directionality.
_TURKISH_OPPOSITIONS: list[tuple[set[str], set[str]]] = [
    ({"arttı", "artır", "artış", "yüksel"}, {"azal", "düştü", "düşüş", "gerile"}),
    ({"dur", "durdur", "iptal", "son"}, {"sürdür", "devam", "başla"}),
    ({"kabul", "onay"}, {"ret", "red", "reddet"}),
    ({"yasak", "men"}, {"serbest", "izin"}),
    ({"başarı", "kazan"}, {"başarısız", "kaybet"}),
    ({"doğru", "kanıt"}, {"yalan", "çürüt", "sahte"}),
    ({"zarar"}, {"kar", "kâr", "hasılat"}),
    ({"artırmaktadır", "artırır"}, {"artırmadığını", "artırmaz"}),
    ({"azaltmaktadır", "azaltır"}, {"azaltmadığını", "azaltmaz"}),
]

RELATION_CLASSES: tuple[str, ...] = (
    EvidenceRelation.SUPPORTED.value,
    EvidenceRelation.PARTIALLY_SUPPORTED.value,
    EvidenceRelation.CONFLICTING.value,
    EvidenceRelation.INSUFFICIENT.value,
)


@dataclass(frozen=True)
class AlignmentPrediction:
    """Represents a predicted evidence relation between a claim and an evidence passage.

    IMPORTANT SAFETY NOTICE:
    Alignment scores and probabilities quantify only the degree of entailment or
    contradiction between the *given claim* and the *specific passage*. They must
    never be presented or interpreted as an absolute real-world truth probability.
    """

    relation: EvidenceRelation
    confidence: float
    probabilities: dict[str, float]
    features: dict[str, float] = field(default_factory=dict)
    rationale: str = ""
    truth_probability_warning: str = (
        "This prediction measures claim-passage alignment only, NOT real-world factuality or truth probability."
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation": self.relation.value,
            "confidence": round(self.confidence, 4),
            "probabilities": {k: round(v, 4) for k, v in self.probabilities.items()},
            "features": {k: round(v, 4) for k, v in self.features.items()},
            "rationale": self.rationale,
            "truth_probability_warning": self.truth_probability_warning,
        }


def has_turkish_negation(text: str) -> bool:
    """Detects explicit lexical or morphological negation in Turkish text."""
    norm = normalize(text)
    return bool(_TURKISH_NEGATION_RE.search(norm)) or has_negation(text)


def detect_antonym_conflict(claim: str, passage: str) -> bool:
    """Detects directional semantic contradictions using opposition lexicons."""
    c_norm = normalize(claim)
    p_norm = normalize(passage)
    for pos_set, neg_set in _TURKISH_OPPOSITIONS:
        c_has_pos = any(w in c_norm for w in pos_set)
        c_has_neg = any(w in c_norm for w in neg_set)
        p_has_pos = any(w in p_norm for w in pos_set)
        p_has_neg = any(w in p_norm for w in neg_set)
        if (c_has_pos and p_has_neg) or (c_has_neg and p_has_pos):
            return True
    return False


def extract_stem(token: str) -> str:
    """Extracts a leading prefix stem to accommodate Turkish agglutinative morphology."""
    norm = normalize(token)
    return norm[:5] if len(norm) > 5 else norm


def extract_alignment_features(claim: str, passage: str) -> dict[str, float]:
    """Extracts linguistic, morphological, numeric, and semantic features for claim-evidence alignment."""
    c_tokens = set(tokens(claim, meaningful=True))
    p_tokens = set(tokens(passage, meaningful=True))

    token_overlap = len(c_tokens & p_tokens) / max(1, len(c_tokens))
    p_token_overlap = len(c_tokens & p_tokens) / max(1, len(p_tokens))

    c_stems = {extract_stem(t) for t in c_tokens}
    p_stems = {extract_stem(t) for t in p_tokens}
    stem_overlap = len(c_stems & p_stems) / max(1, len(c_stems))
    p_stem_overlap = len(c_stems & p_stems) / max(1, len(p_stems))

    c_norm = normalize(claim)
    p_norm = normalize(passage)
    c_trigrams = {c_norm[i : i + 3] for i in range(len(c_norm) - 2)}
    p_trigrams = {p_norm[i : i + 3] for i in range(len(p_norm) - 2)}
    trigram_jaccard = (
        len(c_trigrams & p_trigrams) / max(1, len(c_trigrams | p_trigrams))
        if (c_trigrams | p_trigrams)
        else 0.0
    )

    c_neg = has_turkish_negation(claim)
    p_neg = has_turkish_negation(passage)
    polarity_mismatch = 1.0 if c_neg != p_neg else 0.0
    neg_conflict = (
        1.0
        if (polarity_mismatch and (token_overlap >= 0.15 or stem_overlap >= 0.25))
        else 0.0
    )

    c_nums = set(numeric_values(claim))
    p_nums = set(numeric_values(passage))
    num_match = 1.0 if (c_nums and c_nums <= p_nums) else 0.0
    num_mismatch = 1.0 if (c_nums and p_nums and not (c_nums <= p_nums)) else 0.0
    num_missing = 1.0 if (c_nums and not p_nums) else 0.0

    c_facts = set(comparable_numeric_facts(claim))
    p_facts = set(comparable_numeric_facts(passage))
    fact_match = 1.0 if (c_facts and c_facts <= p_facts) else 0.0

    c_years = set(years(claim))
    p_years = set(years(passage))
    year_match = 1.0 if (c_years and c_years <= p_years) else 0.0
    year_mismatch = 1.0 if (c_years and p_years and not (c_years <= p_years)) else 0.0

    antonym_conflict = 1.0 if detect_antonym_conflict(claim, passage) else 0.0
    lex_score = lexical_score(claim, passage)
    exact_match = 1.0 if c_norm.rstrip(".!") == p_norm.rstrip(".!") else 0.0
    len_ratio = len(c_tokens) / max(1, len(p_tokens))

    return {
        "token_overlap": float(token_overlap),
        "p_token_overlap": float(p_token_overlap),
        "stem_overlap": float(stem_overlap),
        "p_stem_overlap": float(p_stem_overlap),
        "trigram_jaccard": float(trigram_jaccard),
        "claim_negated": 1.0 if c_neg else 0.0,
        "passage_negated": 1.0 if p_neg else 0.0,
        "polarity_mismatch": polarity_mismatch,
        "negation_conflict": neg_conflict,
        "numeric_match": num_match,
        "numeric_mismatch": num_mismatch,
        "numeric_missing": num_missing,
        "fact_match": fact_match,
        "year_match": year_match,
        "year_mismatch": year_mismatch,
        "antonym_conflict": antonym_conflict,
        "lexical_score": float(lex_score),
        "exact_match": exact_match,
        "length_ratio": float(len_ratio),
    }


class TurkishAlignmentClassifier:
    """Task-specific calibrated alignment model for Turkish claim-evidence evaluation.

    Preserves 4-way EvidenceRelation semantics (SUPPORTED, PARTIALLY_SUPPORTED,
    CONFLICTING, INSUFFICIENT) without collapsing output to truth probabilities.
    """

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self.model = RandomForestClassifier(
            random_state=random_state,
            n_estimators=60,
            max_depth=5,
            class_weight="balanced",
        )
        self.classes_: list[str] = list(RELATION_CLASSES)
        self._is_fitted = False

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def fit(self, examples: Sequence[Mapping[str, Any]]) -> TurkishAlignmentClassifier:
        """Trains the classifier on labeled claim-passage examples."""
        features_list: list[list[float]] = []
        labels: list[str] = []

        for item in examples:
            feat_dict = extract_alignment_features(item["claim"], item["passage"])
            features_list.append(list(feat_dict.values()))
            labels.append(str(item["label"]))

        X = np.asarray(features_list, dtype=np.float64)
        y = np.asarray(labels)

        self.model.fit(X, y)
        self.classes_ = list(self.model.classes_)
        self._is_fitted = True
        return self

    def predict(self, claim: str, passage: str) -> AlignmentPrediction:
        """Predicts the EvidenceRelation and calibrated class probabilities."""
        feat_dict = extract_alignment_features(claim, passage)
        feat_vector = np.asarray([list(feat_dict.values())], dtype=np.float64)

        if not self._is_fitted:
            # Fall back to heuristic rule-based alignment if model is not yet fitted
            from .alignment import align_claim

            rel = align_claim(claim, passage)
            return AlignmentPrediction(
                relation=rel,
                confidence=1.0,
                probabilities={c: (1.0 if c == rel.value else 0.0) for c in RELATION_CLASSES},
                features=feat_dict,
                rationale="Unfitted classifier fallback to lexical-structural heuristics",
            )

        probs = self.model.predict_proba(feat_vector)[0]
        prob_map = {cls_name: float(p) for cls_name, p in zip(self.classes_, probs)}

        # Ensure all standard classes exist in prob_map
        for cls_name in RELATION_CLASSES:
            if cls_name not in prob_map:
                prob_map[cls_name] = 0.0

        best_class = max(prob_map, key=lambda k: prob_map[k])
        confidence = prob_map[best_class]

        rationale_parts = []
        if feat_dict["antonym_conflict"] > 0 or feat_dict["negation_conflict"] > 0:
            rationale_parts.append("detected semantic or polarity opposition")
        if feat_dict["numeric_match"] > 0:
            rationale_parts.append("verified consistent numeric facts")
        elif feat_dict["numeric_mismatch"] > 0:
            rationale_parts.append("detected mismatched numeric facts")
        if feat_dict["stem_overlap"] >= 0.5:
            rationale_parts.append("high morphological stem overlap")
        elif feat_dict["token_overlap"] < 0.2:
            rationale_parts.append("insufficient content token overlap")

        rationale = "; ".join(rationale_parts) if rationale_parts else "calibrated tree ensemble vote"

        return AlignmentPrediction(
            relation=EvidenceRelation(best_class),
            confidence=confidence,
            probabilities=prob_map,
            features=feat_dict,
            rationale=rationale,
        )
