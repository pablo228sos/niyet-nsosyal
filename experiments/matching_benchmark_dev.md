# Matching benchmark development run

Status: DEVELOPMENT ONLY

Benchmark: `data/matching_benchmark_v1_draft.json`

Review state: `team_review_pending`

These numbers are not final competition results. The benchmark labels were prepared for development and still need team review before we freeze a report version. The purpose of this run is to find weak assumptions in retrieval and allocation before final evaluation.

## Lexical retrieval baseline

The current deployment baseline uses character TF-IDF with two explicit sources:

- declared responder topics: weight 0.80
- free profile text: weight 0.20

The topic list receives more weight because it is explicit opt-in routing metadata. The fixed weights are a transparent development choice and were not learned from the benchmark labels.

Relevant grade: 2 or 3.

Top K: 3.

| Metric | Development result |
| --- | ---: |
| Precision@3 | 0.4687 |
| Recall@3 | 0.8438 |
| NDCG@3 | 0.8384 |

Compared with the earlier single-document lexical baseline, all three retrieval metrics increased on the same draft labels. The most useful change was removing cases where generic words in profile prose could outrank an explicit topic such as `FastAPI` or `PID`.

These metrics remain development diagnostics until the relevance labels are reviewed and frozen.

## Allocation sensitivity

For this development check, the 32 queries were split into four batches of eight. Each responder had one slot per batch so requests had to compete for capacity.

The table compares capacity-aware greedy routing with global allocation while changing the minimum lexical similarity required before an edge is allowed into allocation.

| Similarity floor | Method | Coverage | Mean draft relevance | Total draft relevance |
| ---: | --- | ---: | ---: | ---: |
| 0.00 | Greedy | 0.9375 | 1.6333 | 49 |
| 0.00 | Global | 1.0000 | 1.5625 | 50 |
| 0.02 | Greedy | 0.6562 | 2.1429 | 45 |
| 0.02 | Global | 0.7812 | 2.0400 | 51 |
| 0.04 | Greedy | 0.5000 | 2.5625 | 41 |
| 0.04 | Global | 0.5312 | 2.5294 | 43 |
| 0.06 | Greedy | 0.4375 | 2.7143 | 38 |
| 0.06 | Global | 0.4375 | 2.7143 | 38 |
| 0.08 | Greedy | 0.4062 | 2.9231 | 38 |
| 0.08 | Global | 0.4062 | 2.9231 | 38 |
| 0.10 | Greedy | 0.3125 | 2.9000 | 29 |
| 0.10 | Global | 0.3125 | 2.9000 | 29 |

## What we learned

Global allocation is not a replacement for retrieval quality. At a completely open floor, both methods cover almost every request but average relevance is weak.

At `0.02`, the draft benchmark shows the clearest capacity-allocation tradeoff: global allocation covers 78.12% of requests versus 65.62% for greedy and increases total relevance from 45 to 51, while mean relevance changes from 2.14 to 2.04.

At `0.06` and above, the candidate graph becomes sparse enough that the two allocation methods often receive the same feasible choices, so the advantage of global assignment disappears.

The live prototype currently keeps a conservative topic gate. The Allocation Lab exposes the threshold sweep instead of hiding settings where global allocation does not improve the result. After human review, the operating threshold should be selected again from the frozen labels.

## Next validation step

1. Two reviewers independently label the 256 query-responder pairs without seeing the draft grades.
2. A third team member adjudicates disagreements and freezes the relevance labels.
3. Re-run this exact script without changing the benchmark after seeing the frozen results.
4. Run ModernBERT-TR-Embed on the same queries and responder profiles if the model can be executed reproducibly before submission.
5. Compare lexical and semantic retrieval using the same Precision@K, Recall@K and NDCG@K metrics.
6. Run greedy and global allocation on candidates from the selected retrieval method.
