from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from niyet.allocator import allocate  # noqa: E402
from niyet.optimizer import global_allocate  # noqa: E402
from niyet.types import CandidateMatch, IntentType, Responder  # noqa: E402


with open(
    os.path.join(ROOT, "data", "matching_benchmark_v1_reviewed.json"),
    encoding="utf-8",
) as handle:
    BENCHMARK = json.load(handle)
with open(
    os.path.join(ROOT, "data", "responder_profiles_v1.json"),
    encoding="utf-8",
) as handle:
    RESPONDER_DATA = json.load(handle)

RESPONDER_BY_ID = {item["id"]: item for item in RESPONDER_DATA}


def responder_document(item: dict) -> str:
    return f"{item['profile_text']} Konular: {', '.join(item['topics'])}"


# Fit the lexical development baseline once on the same full corpus used by
# experiments/evaluate_matching_draft.py. The lab then slices the fixed
# similarity matrix by batch. This keeps the interactive demo consistent with
# the recorded benchmark run instead of re-fitting IDF values for each tab.
_ALL_QUERY_TEXTS = [item["text"] for item in BENCHMARK["queries"]]
_ALL_RESPONDER_DOCUMENTS = [responder_document(item) for item in RESPONDER_DATA]
_VECTORIZER = TfidfVectorizer(
    analyzer="char_wb",
    ngram_range=(3, 5),
    sublinear_tf=True,
)
_MATRIX = _VECTORIZER.fit_transform(_ALL_QUERY_TEXTS + _ALL_RESPONDER_DOCUMENTS)
_ALL_SIMILARITIES = cosine_similarity(
    _MATRIX[: len(_ALL_QUERY_TEXTS)],
    _MATRIX[len(_ALL_QUERY_TEXTS) :],
)


def evaluate_batch(batch_index: int, similarity_floor: float) -> dict:
    start = batch_index * 8
    batch = BENCHMARK["queries"][start : start + 8]
    if not batch:
        raise ValueError("batch_index_out_of_range")

    responders = [
        Responder(
            id=item["id"],
            topics=tuple(item["topics"]),
            willing_intents=tuple(IntentType(value) for value in item["willing_intents"]),
            attention_budget=1,
            active=True,
        )
        for item in RESPONDER_DATA
    ]

    matches: list[CandidateMatch] = []
    similarity_by_pair: dict[tuple[str, str], float] = {}
    for local_q_index, query in enumerate(batch):
        global_q_index = start + local_q_index
        intent_type = IntentType(query["intent"])
        for r_index, responder in enumerate(responders):
            if intent_type not in responder.willing_intents:
                continue
            similarity = float(_ALL_SIMILARITIES[global_q_index, r_index])
            if similarity < similarity_floor:
                continue
            matches.append(
                CandidateMatch(
                    intent_id=query["id"],
                    responder_id=responder.id,
                    topic_relevance=similarity,
                    willingness=1.0,
                    availability=1.0,
                )
            )
            similarity_by_pair[(query["id"], responder.id)] = similarity

    query_by_id = {item["id"]: item for item in batch}

    def summarize(name: str, assignments) -> dict:
        rows = []
        grades = []
        for assignment in assignments:
            query = query_by_id[assignment.intent_id]
            responder = RESPONDER_BY_ID[assignment.responder_id]
            grade = int(query["relevance"][assignment.responder_id])
            grades.append(grade)
            rows.append(
                {
                    "query_id": query["id"],
                    "query": query["text"],
                    "intent": query["intent"].upper(),
                    "responder_id": assignment.responder_id,
                    "responder": responder["display_name"],
                    "draft_relevance": grade,
                    "similarity": round(
                        similarity_by_pair[
                            (assignment.intent_id, assignment.responder_id)
                        ],
                        4,
                    ),
                }
            )

        covered = len({item.intent_id for item in assignments})
        return {
            "method": name,
            "coverage": covered / len(batch),
            "assigned": covered,
            "mean_draft_relevance": round(float(np.mean(grades)), 4)
            if grades
            else 0.0,
            "total_draft_relevance": int(sum(grades)),
            "assignments": rows,
        }

    greedy = allocate(matches, responders)
    global_result = global_allocate(matches, responders)

    return {
        "benchmark_version": BENCHMARK["version"],
        "review_status": BENCHMARK["review_status"],
        "batch_index": batch_index,
        "batch_size": len(batch),
        "similarity_floor": similarity_floor,
        "capacity_per_responder": 1,
        "retrieval": "character TF-IDF, fixed full-benchmark corpus",
        "methods": [
            summarize("capacity-aware greedy", greedy),
            summarize("global allocation", global_result),
        ],
        "note": (
            "Draft relevance labels are development data until team review "
            "and benchmark freeze."
        ),
    }


class handler(BaseHTTPRequestHandler):
    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        try:
            query = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = {}
            for item in query.split("&"):
                if not item:
                    continue
                key, _, value = item.partition("=")
                params[key] = value

            batch_index = int(params.get("batch", "0"))
            similarity_floor = float(params.get("floor", "0.06"))
            if batch_index < 0 or batch_index > 3:
                raise ValueError("batch_index_out_of_range")
            if not 0.0 <= similarity_floor <= 1.0:
                raise ValueError("invalid_similarity_floor")

            self._json(200, evaluate_batch(batch_index, similarity_floor))
        except ValueError as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(
                500,
                {"error": "experiment_failed", "detail": type(exc).__name__},
            )
