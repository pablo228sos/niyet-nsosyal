# Intent seed v1 baseline

This is a development check on `data/intent_seed_v1.csv`. The dataset is still a controlled seed set and team review is pending, so these numbers are not final competition results.

Setup:
- 96 Turkish examples
- 4 balanced classes
- 48 source groups
- word TF-IDF 1-2 grams
- character TF-IDF 3-5 grams
- Logistic Regression with balanced class weights
- 4-fold StratifiedGroupKFold
- related paraphrases kept in the same group

Development result:
- mean accuracy: 0.875
- accuracy standard deviation: 0.029
- mean Macro F1: 0.872
- Macro F1 standard deviation: 0.030

Fold Macro F1 values:
- 0.871
- 0.916
- 0.831
- 0.871

The result is useful because the full pipeline now runs with group-safe evaluation. It should not be interpreted as real NSosyal accuracy. The current examples are cleaner and more balanced than a normal feed.

Next checks:
- add posts that do not ask for a response
- add ambiguous and mixed-intent cases
- review labels
- compare against a Turkish embedding model
- inspect per-class errors instead of optimizing only one aggregate number
