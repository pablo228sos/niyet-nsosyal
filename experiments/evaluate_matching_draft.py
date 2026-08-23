from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from niyet.allocator import allocate
from niyet.metrics import intent_coverage
from niyet.optimizer import global_allocate
from niyet.types import CandidateMatch, Intent, IntentType, Responder


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_PATH = ROOT / "data" / "matching_benchmark_v1_draft.json"
RESPONDER_PATH = ROOT / "data" / "responder_profiles_v1.json"
RELEVANT_GRADE = 2
TOP_K = 3
SIMILARITY_FLOORS = (0.00, 0.02, 0.04, 0.06, 0.08, 0.10)


@dataclass(frozen=True)
class QueryRow:
    id: str
    intent: IntentType
    text: str
    relevance: dict[str, int]


@dataclass(frozen=True)
class ResponderRow:
    responder: Responder
    profile_text: str


def load_data() -> tuple[dict, list[QueryRow], list[ResponderRow]]:
    benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    raw_responders = json.loads(RESPONDER_PATH.read_text(encoding="utf-8"))

    queries = [
        QueryRow(
            id=item["id"],
            intent=IntentType(item["intent"]),
            text=item["text"],
            relevance={key: int(value) for key, value in item["relevance"].items()},
        )
        for item in benchmark["queries"]
    ]

    responders = []
    for item in raw_responders:
        responder = Responder(
            id=item["id"],
            topics=tuple(item["topics"]),
            willing_intents=tuple(IntentType(value) for value in item["willing_intents"]),
            attention_budget=1,
            active=True,
        )
        document = f"{item['profile_text']} Konular: {', '.join(item['topics'])}"
        responders.append(ResponderRow(responder, document))

    return benchmark, queries, responders


def lexical_similarity_matrix(
    queries: list[QueryRow], responders: list[ResponderRow]
) -> np.ndarray:
    texts = [query.text for query in queries] + [item.profile_text for item in responders]
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(texts)
    q_matrix = matrix[: len(queries)]
    r_matrix = matrix[len(queries) :]
    return cosine_similarity(q_matrix, r_matrix)


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


def retrieval_metrics(
    queries: list[QueryRow],
    responders: list[ResponderRow],
    similarities: np.ndarray,
) -> tuple[float, float, float]:
    precision_values = []
    recall_values = []
    ndcg_values = []

    for q_index, query in enumerate(queries):
        eligible = [
            r_index
            for r_index, item in enumerate(responders)
            if query.intent in item.responder.willing_intents
        ]
        ranked = sorted(
            eligible,
            key=lambda r_index: similarities[q_index, r_index],
            reverse=True,
        )
        top = ranked[:TOP_K]

        top_grades = [query.relevance[responders[index].responder.id] for index in top]
        relevant_total = sum(
            query.relevance[responders[index].responder.id] >= RELEVANT_GRADE
            for index in eligible
        )
        relevant_top = sum(grade >= RELEVANT_GRADE for grade in top_grades)

        precision_values.append(relevant_top / TOP_K)
        recall_values.append(relevant_top / relevant_total if relevant_total else 0.0)
        ideal_grades = [query.relevance[responders[index].responder.id] for index in eligible]
        ndcg_values.append(ndcg_at_k(top_grades, ideal_grades, TOP_K))

    return (
        float(np.mean(precision_values)),
        float(np.mean(recall_values)),
        float(np.mean(ndcg_values)),
    )


def build_batch(
    queries: list[QueryRow],
    responders: list[ResponderRow],
    similarities: np.ndarray,
    query_indices: range,
    similarity_floor: float,
):
    intents = [
        Intent(
            id=queries[index].id,
            author_id=f"author-{queries[index].id}",
            kind=queries[index].intent,
            topic="benchmark",
            text=queries[index].text,
        )
        for index in query_indices
    ]
    responder_objects = [item.responder for item in responders]
    matches = []

    for q_index in query_indices:
        query = queries[q_index]
        for r_index, item in enumerate(responders):
            if query.intent not in item.responder.willing_intents:
                continue
            similarity = float(similarities[q_index, r_index])
            if similarity < similarity_floor:
                continue
            matches.append(
                CandidateMatch(
                    intent_id=query.id,
                    responder_id=item.responder.id,
                    topic_relevance=similarity,
                    willingness=1.0,
                    availability=1.0,
                )
            )

    return intents, responder_objects, matches


def assignment_gold(assignments, query_by_id: dict[str, QueryRow]) -> tuple[float, int]:
    grades = [
        query_by_id[item.intent_id].relevance[item.responder_id]
        for item in assignments
    ]
    if not grades:
        return 0.0, 0
    return float(np.mean(grades)), int(sum(grades))


def allocation_sweep(
    queries: list[QueryRow],
    responders: list[ResponderRow],
    similarities: np.ndarray,
) -> None:
    query_by_id = {query.id: query for query in queries}
    batch_ranges = [range(start, min(start + 8, len(queries))) for start in range(0, len(queries), 8)]

    print("\nAllocation sensitivity")
    print("floor,method,coverage,mean_gold,total_gold")

    for floor in SIMILARITY_FLOORS:
        aggregate = {
            "greedy": {"covered": 0, "intents": 0, "grades": []},
            "global": {"covered": 0, "intents": 0, "grades": []},
        }

        for query_indices in batch_ranges:
            intents, responder_objects, matches = build_batch(
                queries,
                responders,
                similarities,
                query_indices,
                floor,
            )
            methods = {
                "greedy": allocate(matches, responder_objects),
                "global": global_allocate(matches, responder_objects),
            }

            for name, assignments in methods.items():
                aggregate[name]["covered"] += len({item.intent_id for item in assignments})
                aggregate[name]["intents"] += len(intents)
                aggregate[name]["grades"].extend(
                    query_by_id[item.intent_id].relevance[item.responder_id]
                    for item in assignments
                )

        for name in ("greedy", "global"):
            values = aggregate[name]
            grades = values["grades"]
            coverage = values["covered"] / values["intents"] if values["intents"] else 0.0
            mean_gold = float(np.mean(grades)) if grades else 0.0
            total_gold = int(sum(grades))
            print(f"{floor:.2f},{name},{coverage:.4f},{mean_gold:.4f},{total_gold}")


def main() -> None:
    benchmark, queries, responders = load_data()
    similarities = lexical_similarity_matrix(queries, responders)
    precision, recall, ndcg = retrieval_metrics(queries, responders, similarities)

    print(f"benchmark_version: {benchmark['version']}")
    print(f"review_status: {benchmark['review_status']}")
    if benchmark["review_status"] != "reviewed":
        print("result_status: DEVELOPMENT ONLY")

    print(f"queries: {len(queries)}")
    print(f"responders: {len(responders)}")
    print(f"precision@{TOP_K}: {precision:.4f}")
    print(f"recall@{TOP_K}: {recall:.4f}")
    print(f"ndcg@{TOP_K}: {ndcg:.4f}")

    allocation_sweep(queries, responders, similarities)


if __name__ == "__main__":
    main()
