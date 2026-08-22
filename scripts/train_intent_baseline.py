from __future__ import annotations

import argparse

from niyet.classifier import evaluate_tfidf_baseline, load_labeled_texts


parser = argparse.ArgumentParser()
parser.add_argument("path")
args = parser.parse_args()

rows = load_labeled_texts(args.path)
result = evaluate_tfidf_baseline(rows)

print(f"train size: {result.train_size}")
print(f"test size:  {result.test_size}")
print(f"accuracy:   {result.accuracy:.3f}")
print(f"macro F1:   {result.macro_f1:.3f}")
