from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from niyet.types import IntentType


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_PATH = ROOT / "data" / "matching_benchmark_v1_draft.json"
RESPONDER_PATH = ROOT / "data" / "responder_profiles_v1.json"
MODEL_NAME = "ytu-ce-cosmos/modernbert-tr-embed"
TOP_K = 3
RELEVANT_GRADE = 2


def ndcg_at_k(grades: list[int], ideal_grades: list[int], k: int) -> float:
    def dcg(values: list[int]) -> float:
        return sum(
            ((2**grade) - 1) / np.log2(index + 2)
            for index, grade in enumerate(values[:k])
        )

    ideal = dcg(sorted(ideal_grades, reverse=True))
    if ideal == 0:
        return 0.0
    return float(dcg(grades) / ideal)


def main() -> None:
    benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    responders = json.loads(RESPONDER_PATH.read_text(encoding="utf-8"))

    model = SentenceTransformer(MODEL_NAME)

    responder_documents = [
        f"{item['profile_text']} Konular: {', '.join(item['topics'])}"
        for item in responders
    ]
    query_texts = [item["text"] for item in benchmark["queries"]]

    query_embeddings = model.encode(
        query_texts,
        prompt_name="query",
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    responder_embeddings = model.encode(
        responder_documents,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    similarities = np.asarray(query_embeddings) @ np.asarray(responder_embeddings).T

    precision_values: list[float] = []
    recall_values: list[float] = []
    ndcg_values: list[float] = []

    for q_index, query in enumerate(benchmark["queries"]):
        intent = IntentType(query["intent"])
        eligible = [
            r_index
            for r_index, responder in enumerate(responders)
            if intent.value in responder["willing_intents"]
        ]
        ranked = sorted(
            eligible,
            key=lambda r_index: similarities[q_index, r_index],
            reverse=True,
        )
        top = ranked[:TOP_K]

        top_grades = [
            int(query["relevance"][responders[r_index]["id"]])
            for r_index in top
        ]
        eligible_grades = [
            int(query["relevance"][responders[r_index]["id"]])
            for r_index in eligible
        ]
        relevant_total = sum(grade >= RELEVANT_GRADE for grade in eligible_grades)
        relevant_top = sum(grade >= RELEVANT_GRADE for grade in top_grades)

        precision_values.append(relevant_top / TOP_K)
        recall_values.append(
            relevant_top / relevant_total if relevant_total else 0.0
        )
        ndcg_values.append(ndcg_at_k(top_grades, eligible_grades, TOP_K))

    result = {
        "benchmark_version": benchmark["version"],
        "review_status": benchmark["review_status"],
        "model": MODEL_NAME,
        "queries": len(benchmark["queries"]),
        "responders": len(responders),
        f"precision@{TOP_K}": round(float(np.mean(precision_values)), 4),
        f"recall@{TOP_K}": round(float(np.mean(recall_values)), 4),
        f"ndcg@{TOP_K}": round(float(np.mean(ndcg_values)), 4),
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if benchmark["review_status"] != "reviewed":
        print("\nDEVELOPMENT ONLY: freeze reviewed labels before using these metrics as final competition results.")


if __name__ == "__main__":
    main()
