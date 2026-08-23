from __future__ import annotations

import argparse

from niyet.classifier import (
    cross_validate_tfidf,
    evaluate_tfidf_baseline,
    load_labeled_texts,
)


parser = argparse.ArgumentParser()
parser.add_argument("path", nargs="?", default="data/intent_seed_v1.csv")
parser.add_argument("--cv", action="store_true")
args = parser.parse_args()

rows = load_labeled_texts(args.path)

if args.cv:
    result = cross_validate_tfidf(rows)
    print(f"rows:          {len(rows)}")
    print(f"folds:         {result.folds}")
    print(f"accuracy:      {result.accuracy_mean:.3f} +/- {result.accuracy_std:.3f}")
    print(f"macro F1:      {result.macro_f1_mean:.3f} +/- {result.macro_f1_std:.3f}")
    for index, (accuracy, macro_f1) in enumerate(
        zip(result.fold_accuracies, result.fold_macro_f1, strict=True), start=1
    ):
        print(f"fold {index}:       accuracy={accuracy:.3f} macro_f1={macro_f1:.3f}")
else:
    result = evaluate_tfidf_baseline(rows)
    print(f"train size:     {result.train_size}")
    print(f"test size:      {result.test_size}")
    print(f"accuracy:       {result.accuracy:.3f}")
    print(f"macro F1:       {result.macro_f1:.3f}")
