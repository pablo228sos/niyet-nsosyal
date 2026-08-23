from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .classifier import build_tfidf_baseline, load_labeled_texts
from .optimizer import global_allocate
from .scoring import pair_score
from .types import CandidateMatch, Intent, IntentType, Responder


@dataclass(frozen=True)
class RuntimeResponder:
    responder: Responder
    display_name: str
    profile_text: str
    daily_budget: int
    remaining_slots: int


@dataclass(frozen=True)
class RouteDecision:
    response_needed: bool
    intent: str | None
    responder_id: str | None
    responder_name: str | None
    reason: tuple[str, ...]
    development_utility: float | None
    retrieval_similarity: float | None
    request_id: str | None = None


class NiyetRuntime:
    """End-to-end runtime used by the live prototype.

    The deployed runtime stays intentionally lightweight and reproducible. It
    uses the committed TF-IDF classification and retrieval baselines. The
    allocation layer can route one request or a bounded batch of open requests.
    Responder capacity can be supplied by the browser session so sequential
    prototype actions use the same state.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        root = Path(__file__).resolve().parents[2]
        self.data_dir = Path(data_dir) if data_dir is not None else root / "data"

        gate_rows = load_labeled_texts(self.data_dir / "response_gate_seed_v1.csv")
        intent_rows = load_labeled_texts(self.data_dir / "intent_seed_v1.csv")

        self.gate_model = build_tfidf_baseline()
        self.gate_model.fit(
            [row.text for row in gate_rows],
            [row.label for row in gate_rows],
        )

        self.intent_model = build_tfidf_baseline()
        self.intent_model.fit(
            [row.text for row in intent_rows],
            [row.label for row in intent_rows],
        )

        self.responders = self._load_responders(
            self.data_dir / "responder_profiles_v1.json"
        )
        self.responder_by_id = {item.responder.id: item for item in self.responders}

    @staticmethod
    def _load_responders(path: Path) -> tuple[RuntimeResponder, ...]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        responders: list[RuntimeResponder] = []

        for item in raw:
            remaining_slots = max(0, int(item["remaining_slots"]))
            daily_budget = max(1, int(item["daily_budget"]))
            responder = Responder(
                id=item["id"],
                topics=tuple(item["topics"]),
                willing_intents=tuple(
                    IntentType(value) for value in item["willing_intents"]
                ),
                attention_budget=remaining_slots,
                active=remaining_slots > 0,
            )
            responders.append(
                RuntimeResponder(
                    responder=responder,
                    display_name=item["display_name"],
                    profile_text=item["profile_text"],
                    daily_budget=daily_budget,
                    remaining_slots=remaining_slots,
                )
            )

        return tuple(responders)

    def default_responder_state(self) -> dict[str, dict[str, int | bool]]:
        return {
            item.responder.id: {
                "remaining_slots": item.remaining_slots,
                "active": item.responder.active,
            }
            for item in self.responders
        }

    def normalize_responder_state(
        self, state: dict | None
    ) -> dict[str, dict[str, int | bool]]:
        normalized = self.default_responder_state()
        if not isinstance(state, dict):
            return normalized

        for responder_id, values in state.items():
            base = self.responder_by_id.get(str(responder_id))
            if base is None or not isinstance(values, dict):
                continue
            slots = values.get("remaining_slots", base.remaining_slots)
            try:
                slots = int(slots)
            except (TypeError, ValueError):
                slots = base.remaining_slots
            slots = max(0, min(base.daily_budget, slots))
            active = bool(values.get("active", True)) and slots > 0
            normalized[base.responder.id] = {
                "remaining_slots": slots,
                "active": active,
            }
        return normalized

    def _responders_for_state(
        self, state: dict | None
    ) -> tuple[RuntimeResponder, ...]:
        normalized = self.normalize_responder_state(state)
        output: list[RuntimeResponder] = []
        for base in self.responders:
            current = normalized[base.responder.id]
            remaining_slots = int(current["remaining_slots"])
            active = bool(current["active"]) and remaining_slots > 0
            output.append(
                RuntimeResponder(
                    responder=Responder(
                        id=base.responder.id,
                        topics=base.responder.topics,
                        willing_intents=base.responder.willing_intents,
                        attention_budget=remaining_slots,
                        active=active,
                    ),
                    display_name=base.display_name,
                    profile_text=base.profile_text,
                    daily_budget=base.daily_budget,
                    remaining_slots=remaining_slots,
                )
            )
        return tuple(output)

    def update_responder_state(
        self,
        state: dict | None,
        responder_id: str,
        *,
        action: str,
    ) -> dict[str, dict[str, int | bool]]:
        normalized = self.normalize_responder_state(state)
        if responder_id not in normalized:
            raise ValueError("unknown_responder")

        current = normalized[responder_id]
        if action == "accept":
            current["remaining_slots"] = max(0, int(current["remaining_slots"]) - 1)
            current["active"] = bool(current["active"]) and int(current["remaining_slots"]) > 0
        elif action == "pause":
            current["active"] = False
        elif action == "resume":
            current["active"] = int(current["remaining_slots"]) > 0
        else:
            raise ValueError("invalid_state_action")
        return normalized

    def classify_response_needed(self, text: str) -> bool:
        prediction = str(self.gate_model.predict([text])[0]).upper()
        return prediction == "RESPONSE"

    def classify_intent(self, text: str) -> IntentType:
        prediction = str(self.intent_model.predict([text])[0]).strip().lower()
        return IntentType(prediction)

    @staticmethod
    def _similarity_matrix(queries: list[str], documents: list[str]):
        if not queries or not documents:
            return None
        vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            sublinear_tf=True,
        )
        matrix = vectorizer.fit_transform([*queries, *documents])
        return cosine_similarity(
            matrix[: len(queries)], matrix[len(queries) :]
        )

    def route(
        self,
        text: str,
        *,
        intent_override: IntentType | None = None,
        responder_state: dict | None = None,
        exclude_responder_ids: tuple[str, ...] = (),
        min_similarity: float = 0.06,
        min_score: float = 0.38,
    ) -> RouteDecision:
        request_id = f"demo-{uuid4().hex[:10]}"
        decisions = self.route_many(
            [
                {
                    "id": request_id,
                    "text": text,
                    "intent_override": intent_override,
                    "exclude_responder_ids": exclude_responder_ids,
                }
            ],
            responder_state=responder_state,
            min_similarity=min_similarity,
            min_score=min_score,
        )
        return decisions[0]

    def route_many(
        self,
        requests: list[dict],
        *,
        responder_state: dict | None = None,
        min_similarity: float = 0.06,
        min_score: float = 0.38,
    ) -> list[RouteDecision]:
        if not 0.0 <= min_similarity <= 1.0:
            raise ValueError("min_similarity must be between 0 and 1")
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0 and 1")
        if not requests or len(requests) > 20:
            raise ValueError("batch_size_out_of_range")

        prepared: list[dict] = []
        for index, raw in enumerate(requests):
            clean_text = str(raw.get("text", "")).strip()
            request_id = str(raw.get("id") or f"batch-{index + 1}")
            override_raw = raw.get("intent_override")
            if isinstance(override_raw, IntentType):
                intent_override = override_raw
            elif override_raw:
                intent_override = IntentType(str(override_raw).strip().lower())
            else:
                intent_override = None

            excluded = tuple(str(value) for value in raw.get("exclude_responder_ids", ()))
            manual_activation = intent_override is not None
            response_needed = bool(clean_text) and (
                manual_activation
                or (len(clean_text) >= 8 and self.classify_response_needed(clean_text))
            )
            intent_type = (
                intent_override
                if response_needed and intent_override is not None
                else self.classify_intent(clean_text)
                if response_needed
                else None
            )
            prepared.append(
                {
                    "id": request_id,
                    "text": clean_text,
                    "response_needed": response_needed,
                    "intent_type": intent_type,
                    "excluded": excluded,
                }
            )

        responders = self._responders_for_state(responder_state)
        active_responders = [
            item
            for item in responders
            if item.responder.active and item.remaining_slots > 0
        ]
        routable = [item for item in prepared if item["response_needed"]]

        if not routable or not active_responders:
            return [
                RouteDecision(
                    response_needed=bool(item["response_needed"]),
                    intent=item["intent_type"].value if item["intent_type"] else None,
                    responder_id=None,
                    responder_name=None,
                    reason=(),
                    development_utility=None,
                    retrieval_similarity=None,
                    request_id=item["id"],
                )
                for item in prepared
            ]

        documents = [
            f"{item.profile_text} Konular: {', '.join(item.responder.topics)}"
            for item in active_responders
        ]
        similarities = self._similarity_matrix(
            [item["text"] for item in routable], documents
        )

        matches: list[CandidateMatch] = []
        by_pair: dict[tuple[str, str], tuple[RuntimeResponder, float, CandidateMatch]] = {}
        for q_index, item in enumerate(routable):
            intent_type: IntentType = item["intent_type"]
            for r_index, responder in enumerate(active_responders):
                if responder.responder.id in item["excluded"]:
                    continue
                if intent_type not in responder.responder.willing_intents:
                    continue

                similarity = float(similarities[q_index, r_index])
                if similarity < min_similarity:
                    continue

                availability = responder.remaining_slots / responder.daily_budget
                match = CandidateMatch(
                    intent_id=item["id"],
                    responder_id=responder.responder.id,
                    topic_relevance=similarity,
                    willingness=1.0,
                    availability=availability,
                )
                matches.append(match)
                by_pair[(item["id"], responder.responder.id)] = (
                    responder,
                    similarity,
                    match,
                )

        assignments = global_allocate(
            matches,
            [item.responder for item in active_responders],
            min_score=min_score,
        )
        assignment_by_intent = {item.intent_id: item for item in assignments}

        decisions: list[RouteDecision] = []
        for item in prepared:
            intent_type: IntentType | None = item["intent_type"]
            assignment = assignment_by_intent.get(item["id"])
            if not item["response_needed"] or assignment is None:
                decisions.append(
                    RouteDecision(
                        response_needed=bool(item["response_needed"]),
                        intent=intent_type.value if intent_type else None,
                        responder_id=None,
                        responder_name=None,
                        reason=(),
                        development_utility=None,
                        retrieval_similarity=None,
                        request_id=item["id"],
                    )
                )
                continue

            chosen, similarity, chosen_match = by_pair[
                (item["id"], assignment.responder_id)
            ]
            reason = (
                f"topic profile: {', '.join(chosen.responder.topics[:3])}",
                f"{intent_type.value.upper()} requests enabled",
                f"{chosen.remaining_slots}/{chosen.daily_budget} attention slots available",
            )
            decisions.append(
                RouteDecision(
                    response_needed=True,
                    intent=intent_type.value,
                    responder_id=chosen.responder.id,
                    responder_name=chosen.display_name,
                    reason=reason,
                    development_utility=pair_score(chosen_match),
                    retrieval_similarity=similarity,
                    request_id=item["id"],
                )
            )

        return decisions
