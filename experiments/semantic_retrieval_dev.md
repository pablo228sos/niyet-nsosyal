# Turkish semantic retrieval development run

Status: DEVELOPMENT ONLY

Benchmark: `data/matching_benchmark_v1_draft.json`

Review state: `team_review_pending`

We compared the lightweight lexical responder retriever with `ytu-ce-cosmos/modernbert-tr-embed` on the same 32 Turkish requests, the same 8 responder profiles, the same intent-eligibility rules and the same draft relevance labels.

The semantic model is external work from Yildiz Technical University COSMOS. We only report measurements produced by our evaluation script on our benchmark.

## Same-benchmark retrieval comparison

| Retriever | Precision@3 | Recall@3 | NDCG@3 |
| --- | ---: | ---: | ---: |
| Weighted lexical TF-IDF | 0.4687 | 0.8438 | 0.8384 |
| ModernBERT-TR-Embed | **0.5312** | **0.9427** | **0.8968** |

Absolute improvement of the semantic retriever over the lexical baseline:

- Precision@3: +0.0625
- Recall@3: +0.0989
- NDCG@3: +0.0584

The result supports using the Turkish semantic encoder as the leading retrieval candidate for the next prototype iteration. It does not yet justify a final competition claim because the benchmark labels are still pending team review.

## Reproduction

The measured semantic run was executed in GitHub Actions with:

```bash
pip install -e '.[embeddings]' pytest
python experiments/evaluate_modernbert_retrieval.py
```

The run loaded `ytu-ce-cosmos/modernbert-tr-embed` and evaluated it directly rather than copying model-card benchmark values.

## Decision rule

We will freeze the reviewed relevance labels before the final model comparison. After the benchmark is frozen, both retrieval methods are re-run without changing labels in response to the result. The selected production candidate should then be chosen from the frozen comparison together with latency and deployment-cost constraints.
