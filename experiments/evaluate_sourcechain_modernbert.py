from __future__ import annotations

import argparse
import json
import math
import re
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "sourcebench_tr" / "retrieval_ranking_v0.json"
EMBED_MODEL = "ytu-ce-cosmos/modernbert-tr-embed"
RERANK_MODEL = "ytu-ce-cosmos/modernbert-tr-reranker"
TOKEN_RE = re.compile(r"[\wçğıöşüÇĞİÖŞÜ]+", re.UNICODE)


def tokens(text: str) -> set[str]:
    return {t.casefold() for t in TOKEN_RE.findall(text) if len(t) > 2}


def lexical_score(query: str, document: str) -> float:
    q, d = tokens(query), tokens(document)
    if not q or not d:
        return 0.0
    return len(q & d) / math.sqrt(len(q) * len(d))


def metrics(rankings: list[list[str]], relevant: list[str]) -> dict[str, float]:
    rr, hit1, hit3 = [], [], []
    for ranked, target in zip(rankings, relevant, strict=True):
        rank = ranked.index(target) + 1
        rr.append(1.0 / rank)
        hit1.append(rank <= 1)
        hit3.append(rank <= 3)
    return {
        "mrr": round(float(np.mean(rr)), 4),
        "hit@1": round(float(np.mean(hit1)), 4),
        "hit@3": round(float(np.mean(hit3)), 4),
    }


def rank_lexical(queries: list[str], docs: list[dict]) -> list[list[str]]:
    return [
        [d["id"] for d in sorted(docs, key=lambda d: lexical_score(q, d["text"]), reverse=True)]
        for q in queries
    ]


def rank_embed(queries: list[str], docs: list[dict]):
    from sentence_transformers import SentenceTransformer

    started = time.perf_counter()
    model = SentenceTransformer(EMBED_MODEL)
    load_s = time.perf_counter() - started
    started = time.perf_counter()
    q = model.encode(queries, prompt_name="query", normalize_embeddings=True, show_progress_bar=False)
    d = model.encode([x["text"] for x in docs], normalize_embeddings=True, show_progress_bar=False)
    scores = np.asarray(q) @ np.asarray(d).T
    infer_s = time.perf_counter() - started
    rankings = [[docs[i]["id"] for i in np.argsort(-row)] for row in scores]
    return rankings, load_s, infer_s


def rank_reranker(queries: list[str], docs: list[dict]):
    from sentence_transformers import CrossEncoder

    started = time.perf_counter()
    model = CrossEncoder(RERANK_MODEL)
    load_s = time.perf_counter() - started
    rankings, inference = [], 0.0
    for query in queries:
        pairs = [(query, d["text"]) for d in docs]
        started = time.perf_counter()
        scores = np.asarray(model.predict(pairs, show_progress_bar=False)).reshape(-1)
        inference += time.perf_counter() - started
        rankings.append([docs[i]["id"] for i in np.argsort(-scores)])
    return rankings, load_s, inference


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic", action="store_true", help="Load external ModernBERT models.")
    parser.add_argument("--reranker", action="store_true", help="Also evaluate the cross-encoder reranker.")
    args = parser.parse_args()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    queries = [x["claim"] for x in data["queries"]]
    relevant = [x["relevant"] for x in data["queries"]]
    docs = data["passages"]

    started = time.perf_counter()
    lexical = rank_lexical(queries, docs)
    result = {
        "benchmark": data["version"],
        "status": data["status"],
        "queries": len(queries),
        "passages": len(docs),
        "lexical": {**metrics(lexical, relevant), "inference_s": round(time.perf_counter() - started, 4)},
    }
    if args.semantic:
        ranking, load_s, infer_s = rank_embed(queries, docs)
        result["modernbert_embed"] = {**metrics(ranking, relevant), "load_s": round(load_s, 3), "inference_s": round(infer_s, 3)}
    if args.reranker:
        ranking, load_s, infer_s = rank_reranker(queries, docs)
        result["modernbert_reranker"] = {**metrics(ranking, relevant), "load_s": round(load_s, 3), "inference_s": round(infer_s, 3)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
