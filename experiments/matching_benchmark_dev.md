# Matching benchmark development run

Status: DEVELOPMENT ONLY

Benchmark: `data/matching_benchmark_v1_draft.json`

Review state: `team_review_pending`

These numbers are not final competition results. The benchmark labels were prepared for development and still need team review before we freeze a report version. The purpose of this run is to find weak assumptions in retrieval and allocation before final evaluation.

## Lexical retrieval baseline

Method: character TF-IDF over Turkish query text and responder profile text.

Relevant grade: 2 or 3.

Top K: 3.

| Metric | Development result |
| --- | ---: |
| Precision@3 | 0.4375 |
| Recall@3 | 0.7969 |
| NDCG@3 | 0.8079 |

The result is useful as a baseline, not as a target. Precision is the weakest part. The lexical retriever often finds at least one relevant profile but can still include weak candidates in the top three. This is exactly why the semantic retrieval comparison matters.

## Allocation sensitivity

For this development check, the 32 queries were split into four batches of eight. Each responder had one slot per batch so requests had to compete for capacity.

The table below compares capacity-aware greedy routing with global allocation while changing the minimum lexical topic similarity required before an edge is allowed into allocation.

| Similarity floor | Method | Coverage | Mean reviewed grade | Total reviewed grade |
| ---: | --- | ---: | ---: | ---: |
| 0.00 | Greedy | 0.9375 | 1.558 | 46 |
| 0.00 | Global | 1.0000 | 1.500 | 48 |
| 0.02 | Greedy | 0.8125 | 1.843 | 46 |
| 0.02 | Global | 0.9688 | 1.375 | 42 |
| 0.04 | Greedy | 0.6875 | 2.102 | 46 |
| 0.04 | Global | 0.8125 | 1.857 | 48 |
| 0.06 | Greedy | 0.5625 | 2.338 | 42 |
| 0.06 | Global | 0.6563 | 2.236 | 47 |
| 0.08 | Greedy | 0.4688 | 2.838 | 42 |
| 0.08 | Global | 0.5000 | 2.729 | 42 |
| 0.10 | Greedy | 0.4063 | 2.938 | 38 |
| 0.10 | Global | 0.4063 | 2.938 | 38 |

## What we learned

Global allocation is not a replacement for retrieval quality. When weak candidate edges are allowed into the graph, the optimizer can increase coverage by assigning low-quality matches. That is not a product win.

We therefore changed the runtime pipeline to apply a minimum topic-relevance gate before allocation. The current development default is `0.06`. This is not claimed as a universal optimum. It is a conservative starting point identified by this draft sensitivity run and will be re-evaluated after the benchmark is reviewed.

The final comparison should report the coverage-quality tradeoff rather than selecting the threshold that makes one algorithm look best.

## Next validation step

1. Team review and freeze the relevance labels.
2. Re-run this exact script without changing the benchmark after seeing results.
3. Add ModernBERT-TR-Embed retrieval on the same fixed queries and responder profiles.
4. Compare lexical and semantic retrieval using the same Precision@K, Recall@K and NDCG@K metrics.
5. Run allocation on candidates from the selected retrieval method.
