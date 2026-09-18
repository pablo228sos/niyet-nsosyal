# Turkish semantic retrieval model choice

`ytu-ce-cosmos/modernbert-tr-embed` was evaluated as a Turkish-first semantic retrieval candidate. It is external work from the Yildiz Technical University COSMOS group and is not presented as a model created by BEYMAX.

## Why it was evaluated

- Turkish is a primary language for the project.
- The model is designed for embeddings/retrieval.
- It can run locally rather than requiring a closed embedding API.
- It provides a meaningful semantic comparison against the lightweight lexical runtime.

## NIYET matching evaluation

On the same frozen 32-query × 8-responder reviewed benchmark:

| Retriever | Precision@3 | Recall@3 | NDCG@3 |
| --- | ---: | ---: | ---: |
| Weighted lexical TF-IDF | 0.4688 | 0.8438 | 0.8450 |
| ModernBERT-TR-Embed | **0.5417** | **0.9583** | **0.9025** |

The embedding model improved retrieval quality on this controlled reviewed set.

## Deployment decision

The final lightweight runtime intentionally keeps the lexical NIYET retriever. ModernBERT-TR-Embed remains an offline evaluation signal rather than a production dependency.

That separation is deliberate:

- semantic-model value can be measured without pretending it is already deployed;
- deployment cost and latency remain independently measurable;
- the judge demo does not depend on loading a heavier semantic model.

The model repository also provides lighter deployment options such as ONNX, but a production decision should be based on measured latency, memory and hardware.

## Attribution boundary

External model:
- `ytu-ce-cosmos/modernbert-tr-embed`

BEYMAX code/evaluation:
- responder eligibility;
- responder profile representation;
- candidate-retrieval integration;
- pair scoring;
- attention capacity;
- global allocation;
- reviewed benchmark and evaluation;
- DRSK product flow.

External model-card benchmark numbers are not copied into DRSK results.
