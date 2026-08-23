# Response-needed gate seed v1

This is a development check on `data/response_gate_seed_v1.csv`. The rows are controlled seed examples and team review is still pending, so the numbers below are not final competition results.

Setup:
- 96 Turkish examples
- 48 `RESPONSE` posts
- 48 `NONE` posts
- grouped examples are kept in the same fold
- word TF-IDF 1-2 grams
- character TF-IDF 3-5 grams
- balanced Logistic Regression
- 4-fold StratifiedGroupKFold

Development result:
- mean accuracy: 0.917
- accuracy standard deviation: 0.042
- mean Macro F1: 0.916
- Macro F1 standard deviation: 0.043

Fold Macro F1 values:
- 0.873
- 0.958
- 0.958
- 0.873

Across the four held-out folds, all 48 response-seeking examples were detected. Eight `NONE` examples were false positives. That error direction is important for the product because a false positive can create an unnecessary routing suggestion.

The gate should therefore not silently send a post to responders. In the product flow the author confirms or disables the detected intent before routing starts.

Next checks:
- team review of labels
- harder negative examples that contain questions but do not seek help
- promotional and spam-like posts
- ambiguous mixed posts
- precision/recall reporting for the `RESPONSE` class
- threshold tuning once we move to a probabilistic gate
