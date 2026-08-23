# Turkish embedding model choice

For semantic candidate retrieval we plan to test `ytu-ce-cosmos/modernbert-tr-embed` as the Turkish-first embedding model.

The model is published by the COSMOS research group at Yildiz Technical University. Its model card describes it as a 150M-parameter Turkish text embedding model and provides Sentence Transformers and ONNX usage. The license is Apache-2.0.

Source:
- https://huggingface.co/ytu-ce-cosmos/modernbert-tr-embed

## Why it fits this prototype

- Turkish is the main language we need to handle well
- the model is designed for text embeddings and retrieval
- it can be run locally instead of requiring a closed embedding API
- the model is substantially smaller than multi-billion-parameter embedding models
- it gives us a Turkish local-technology component without pretending that the model itself is our work

## Attribution boundary

The embedding model is external work from Yildiz Technical University COSMOS.

Our project code covers:
- responder eligibility
- responder profile representation
- candidate retrieval integration
- pair scoring
- attention capacity
- global allocation
- evaluation and product flow

The report should state this boundary clearly.

## Evaluation rule

We will not copy the model card's benchmark score and present it as a NIYET result.

Our own experiment needs to compare retrieval methods on the same NIYET matching benchmark, for example:
- lexical/topic baseline
- TF-IDF profile similarity
- ModernBERT-TR-Embed similarity

Useful retrieval metrics will include Precision@K and NDCG@K once the responder relevance labels are ready.

## Deployment options

For the prototype we can use Sentence Transformers.

For a lighter deployment path, the model repository also provides ONNX variants. A production decision should be based on measured latency, memory and hardware instead of assuming one backend is best.
