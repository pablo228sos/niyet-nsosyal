# Matching benchmark development run

Status: DEVELOPMENT ONLY

Benchmark: `data/matching_benchmark_v1_draft.json`

Review state: `team_review_pending`

These numbers are not final competition results. The benchmark labels were prepared for development and still need team review before we freeze an evaluation version. The purpose of this run is to find weak assumptions in retrieval and allocation before final evaluation.

## Lexical retrieval baseline

Method: character TF-IDF over Turkish query text and responder profile text.

Relevant grade: 2 or 3.

Top K: 3.

| Metric | Development result |
| --- | ---: |
| Precision@3 | 0.4375 |
| Recall@3 | 0.7969 |
| NDCG@3 | 0.8079 |

The result is useful as a baseline, not as a target. Precision is the weakest part. The lexical retriever often finds at least one relevant profile but can still include weak candidates in the top three. This is why the semantic retrieval comparison matters.

## Allocation sensitivity

For this development check, the 32 queries were split into four batches of eight. Each responder had one slot per batch so requests had to compete for capacity.

Willingness is applied as an eligibility rule before these assignments. Every remaining benchmark edge therefore has willingness enabled. Availability is also fixed to 1.0 in this controlled experiment because every responder starts each batch with one available slot. Under these conditions the current utility `(topic relevance + availability) / 2` ranks edges monotonically by the same lexical similarity used in the original sweep, so the assignment table below remains valid after the scoring cleanup.

| Similarity floor | Method | Coverage | Mean draft relevance | Total draft relevance |
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

We therefore apply a minimum topic-relevance gate before allocation. The current development default is `0.06`. It is not presented as a universal optimum and will be re-evaluated after the labels are reviewed.

At that floor, global allocation serves more requests and produces more total draft relevance than greedy, while average assigned relevance is slightly lower. That coverage-quality tradeoff is more useful than a single winner claim.

## Next validation step

1. Team review and freeze the relevance labels.
2. Re-run the same evaluation without changing the benchmark after seeing the reviewed results.
3. Run ModernBERT-TR-Embed on the same fixed queries and responder profiles.
4. Compare lexical and semantic retrieval using Precision@K, Recall@K and NDCG@K.
5. Run allocation on candidates from the selected retrieval method.

Until steps 1-2 are complete, the values in this file remain development diagnostics.
