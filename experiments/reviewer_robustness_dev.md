# Retrieval robustness across independent reviewers

Two team members independently graded all 256 query-responder pairs on the 0-3 relevance scale. Raw reviewer files are not published in this repository. This note reports only aggregate retrieval results before third-person adjudication.

Inter-rater agreement before adjudication:

- exact agreement: 243 / 256 = 94.92%
- quadratic weighted Cohen's kappa: 0.9756
- disagreements awaiting adjudication: 13

We evaluated the same fixed top-3 rankings against each reviewer label set separately. Relevance grade >= 2 is treated as relevant for Precision@3 and Recall@3; NDCG@3 uses the full 0-3 grades.

| Label set | Retriever | Precision@3 | Recall@3 | NDCG@3 |
| --- | --- | ---: | ---: | ---: |
| R1 | Weighted lexical TF-IDF | 0.4479 | 0.8438 | 0.8403 |
| R1 | ModernBERT-TR-Embed | **0.5208** | **0.9583** | **0.9061** |
| R2 | Weighted lexical TF-IDF | 0.4792 | 0.8177 | 0.8286 |
| R2 | ModernBERT-TR-Embed | **0.5521** | **0.9271** | **0.8919** |

The semantic retriever is better on all three retrieval metrics under both independent reviewer label sets. This is useful robustness evidence, but it is still pre-adjudication. We will report one final benchmark table only after the third team member resolves the 13 disagreements and the reviewed benchmark is frozen.

No reviewer labels were changed based on model rankings or scores.
