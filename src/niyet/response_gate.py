from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from .annotations import validate_annotation_file
from .classifier import LabeledText


@dataclass(frozen=True)
class GateDecision:
    """Represents a binary response-needed routing decision.

    Guarantees transparent probability reporting without presenting scores
    as real-world factuality or truth.
    """

    response_needed: bool
    probability: float
    threshold: float
    label: str
    calibrated: bool = True
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "response_needed": self.response_needed,
            "probability": round(self.probability, 4),
            "threshold": round(self.threshold, 4),
            "label": self.label,
            "calibrated": self.calibrated,
            "rationale": self.rationale,
        }


ResponseGateDecision = GateDecision


class ResponseGate:
    """Calibrated probabilistic response-needed gate for the NIYET routing pipeline.

    A normal social feed contains many non-response posts (news updates, media,
    personal status, rhetorical questions). This gate intercepts posts and gates
    the 4-way intent classifier so only genuine response-seeking posts are routed.
    """

    def __init__(
        self,
        *,
        threshold: float = 0.50,
        random_state: int = 42,
    ) -> None:
        self.threshold = threshold
        self.random_state = random_state

        features = FeatureUnion(
            [
                (
                    "word",
                    TfidfVectorizer(
                        analyzer="word",
                        ngram_range=(1, 2),
                        min_df=1,
                        sublinear_tf=True,
                    ),
                ),
                (
                    "char",
                    TfidfVectorizer(
                        analyzer="char_wb",
                        ngram_range=(3, 5),
                        min_df=1,
                        sublinear_tf=True,
                    ),
                ),
            ]
        )
        self.pipeline = Pipeline(
            [
                ("features", features),
                (
                    "model",
                    LogisticRegression(
                        max_iter=2000,
                        class_weight="balanced",
                        random_state=random_state,
                    ),
                ),
            ]
        )
        self._is_fitted = False
        self._response_idx = 1

    @property
    def is_fitted(self) -> bool:
        return self._is_fitted

    def fit(self, rows: Sequence[LabeledText | dict[str, str]]) -> ResponseGate:
        texts: list[str] = []
        labels: list[str] = []

        for item in rows:
            if isinstance(item, LabeledText):
                t, lbl = item.text, item.label.strip().upper()
            else:
                t = str(item.get("text", ""))
                lbl = str(item.get("final_label") or item.get("label", "")).strip().upper()

            if t and lbl:
                texts.append(t)
                labels.append(lbl)

        if len(set(labels)) < 2:
            raise ValueError("ResponseGate requires at least two classes (RESPONSE and NONE)")

        self.pipeline.fit(texts, labels)
        classes = list(self.pipeline.named_steps["model"].classes_)
        self._response_idx = classes.index("RESPONSE") if "RESPONSE" in classes else 1
        self._is_fitted = True
        return self

    @classmethod
    def from_csv(cls, path: str | Path, *, threshold: float = 0.50) -> ResponseGate:
        path = Path(path)
        problems = validate_annotation_file(path)
        if problems:
            details = "; ".join(f"row {p.row}: {p.message}" for p in problems[:3])
            raise ValueError(f"invalid annotation CSV: {details}")

        rows: list[dict[str, str]] = []
        with path.open(encoding="utf-8", newline="") as h:
            rows = list(csv.DictReader(h))

        gate = cls(threshold=threshold)
        gate.fit(rows)
        return gate

    def predict_probability(self, text: str) -> float:
        """Returns the calibrated posterior probability P(label = RESPONSE | text)."""
        if not self._is_fitted:
            raise RuntimeError("ResponseGate must be fitted before predict_probability()")
        clean = text.strip()
        if not clean:
            return 0.0
        probs = self.pipeline.predict_proba([clean])[0]
        return float(probs[self._response_idx])

    def decide(self, text: str, *, custom_threshold: float | None = None) -> GateDecision:
        """Evaluates whether the post requires peer response routing."""
        thr = self.threshold if custom_threshold is None else custom_threshold
        clean = text.strip()
        if not clean:
            return GateDecision(
                response_needed=False,
                probability=0.0,
                threshold=thr,
                label="NONE",
                rationale="empty input text",
            )

        prob = self.predict_probability(clean)
        response_needed = prob >= thr
        label = "RESPONSE" if response_needed else "NONE"

        rationale = (
            f"calibrated probability {prob:.3f} >= threshold {thr:.2f}"
            if response_needed
            else f"calibrated probability {prob:.3f} < threshold {thr:.2f}"
        )

        return GateDecision(
            response_needed=response_needed,
            probability=prob,
            threshold=thr,
            label=label,
            calibrated=True,
            rationale=rationale,
        )
