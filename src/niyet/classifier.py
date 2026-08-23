from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline


@dataclass(frozen=True)
class LabeledText:
    text: str
    label: str
    group: str


@dataclass(frozen=True)
class ClassificationResult:
    train_size: int
    test_size: int
    accuracy: float
    macro_f1: float


@dataclass(frozen=True)
class CrossValidationResult:
    folds: int
    accuracy_mean: float
    accuracy_std: float
    macro_f1_mean: float
    macro_f1_std: float
    fold_accuracies: tuple[float, ...]
    fold_macro_f1: tuple[float, ...]


def load_labeled_texts(path: str | Path) -> list[LabeledText]:
    rows: list[LabeledText] = []
    with Path(path).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            text = row["text"].strip()
            label = row["final_label"].strip()
            group = row["source_group"].strip()
            if text and label and group:
                rows.append(LabeledText(text=text, label=label, group=group))
    return rows


def build_tfidf_baseline() -> Pipeline:
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
    model = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42,
    )
    return Pipeline([("features", features), ("model", model)])


def evaluate_tfidf_baseline(
    rows: list[LabeledText],
    *,
    test_size: float = 0.25,
    random_state: int = 42,
) -> ClassificationResult:
    if len({row.label for row in rows}) < 2:
        raise ValueError("at least two labels are required")
    if len({row.group for row in rows}) < 2:
        raise ValueError("at least two source groups are required")

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=test_size,
        random_state=random_state,
    )
    texts = [row.text for row in rows]
    labels = [row.label for row in rows]
    groups = [row.group for row in rows]
    train_index, test_index = next(splitter.split(texts, labels, groups))

    train_texts = [texts[index] for index in train_index]
    train_labels = [labels[index] for index in train_index]
    test_texts = [texts[index] for index in test_index]
    test_labels = [labels[index] for index in test_index]

    if len(set(train_labels)) < 2:
        raise ValueError("training split contains fewer than two labels")

    model = build_tfidf_baseline()
    model.fit(train_texts, train_labels)
    predictions = model.predict(test_texts)

    return ClassificationResult(
        train_size=len(train_index),
        test_size=len(test_index),
        accuracy=float(accuracy_score(test_labels, predictions)),
        macro_f1=float(f1_score(test_labels, predictions, average="macro")),
    )


def cross_validate_tfidf(
    rows: list[LabeledText],
    *,
    n_splits: int = 4,
    random_state: int = 42,
) -> CrossValidationResult:
    labels = [row.label for row in rows]
    groups = [row.group for row in rows]
    texts = [row.text for row in rows]

    if len(set(labels)) < 2:
        raise ValueError("at least two labels are required")
    if len(set(groups)) < n_splits:
        raise ValueError("not enough source groups for the requested number of folds")

    splitter = StratifiedGroupKFold(
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state,
    )

    accuracies: list[float] = []
    macro_f1_scores: list[float] = []

    for train_index, test_index in splitter.split(texts, labels, groups):
        train_texts = [texts[index] for index in train_index]
        train_labels = [labels[index] for index in train_index]
        test_texts = [texts[index] for index in test_index]
        test_labels = [labels[index] for index in test_index]

        model = build_tfidf_baseline()
        model.fit(train_texts, train_labels)
        predictions = model.predict(test_texts)

        accuracies.append(float(accuracy_score(test_labels, predictions)))
        macro_f1_scores.append(float(f1_score(test_labels, predictions, average="macro")))

    return CrossValidationResult(
        folds=n_splits,
        accuracy_mean=mean(accuracies),
        accuracy_std=pstdev(accuracies),
        macro_f1_mean=mean(macro_f1_scores),
        macro_f1_std=pstdev(macro_f1_scores),
        fold_accuracies=tuple(accuracies),
        fold_macro_f1=tuple(macro_f1_scores),
    )
