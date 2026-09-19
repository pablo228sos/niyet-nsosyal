from __future__ import annotations

import numpy as np

from drsk.firebase_auth import AuthenticatedUser
from drsk.niyet_matching import NiyetTextAnalysis
from drsk.niyet_persistence import MemoryNiyetRepository, NiyetService


def actor(uid: str) -> AuthenticatedUser:
    return AuthenticatedUser(
        uid=uid,
        email=f"{uid}@example.test",
        display_name=uid.title(),
        photo_url=None,
        provider_ids=("password",),
        claims={"uid": uid},
    )


class FixedAnalyzer:
    def __init__(self, *, intent: str, language: str = "en", response_needed: bool = True) -> None:
        self.result = NiyetTextAnalysis(response_needed=response_needed, intent=intent, language=language)

    def analyze(self, text: str, *, language_hint: str | None = None) -> NiyetTextAnalysis:
        return NiyetTextAnalysis(
            response_needed=self.result.response_needed,
            intent=self.result.intent,
            language=language_hint or self.result.language,
        )


def profile(service: NiyetService, uid: str, *, intents: list[str], languages: list[str]) -> None:
    service.sync_user(actor(uid))
    service.update_responder_profile(
        actor(uid),
        {
            "topics": ["design", "backend"],
            "languages": languages,
            "willing_intents": intents,
            "profile_text": "Design and backend review",
            "willing": True,
            "active": True,
            "capacity_total": 2,
        },
    )


def test_server_classification_drives_intent_willingness_not_client_payload(monkeypatch) -> None:
    repository = MemoryNiyetRepository()
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    profile(service, "ask-only", intents=["ask"], languages=["en"])
    profile(service, "feedback", intents=["feedback"], languages=["en"])

    monkeypatch.setattr(
        "drsk.niyet_persistence.get_text_analyzer",
        lambda: FixedAnalyzer(intent="feedback"),
    )
    monkeypatch.setattr(
        "drsk.niyet_persistence.dynamic_relevance_matrix",
        lambda requests, profiles: np.ones((len(requests), len(profiles)), dtype=float) * 0.8,
    )

    request = service.create_request(
        actor("author"),
        text="Please review this backend design",
        intent="ask",  # untrusted client hint must not control routing
        language="en",
    )

    assert request["intent"] == "feedback"
    assert request["intent_source"] == "niyet_tfidf_classifier"
    assignment = repository.get_assignment(request["current_assignment_id"])
    assert assignment is not None
    assert assignment["responder_uid"] == "feedback"


def test_responder_language_is_a_hard_eligibility_constraint(monkeypatch) -> None:
    repository = MemoryNiyetRepository()
    service = NiyetService(repository)
    service.sync_user(actor("author"))
    profile(service, "english", intents=["ask"], languages=["en"])
    profile(service, "turkish", intents=["ask"], languages=["tr"])

    monkeypatch.setattr(
        "drsk.niyet_persistence.get_text_analyzer",
        lambda: FixedAnalyzer(intent="ask", language="tr"),
    )
    monkeypatch.setattr(
        "drsk.niyet_persistence.dynamic_relevance_matrix",
        lambda requests, profiles: np.ones((len(requests), len(profiles)), dtype=float) * 0.8,
    )

    request = service.create_request(
        actor("author"),
        text="Python backend konusunda yardım lazım",
        language="tr",
    )
    assignment = repository.get_assignment(request["current_assignment_id"])
    assert assignment is not None
    assert assignment["responder_uid"] == "turkish"


def test_open_window_is_globally_allocated_under_shared_capacity(monkeypatch) -> None:
    repository = MemoryNiyetRepository()
    service = NiyetService(repository)
    for uid in ("author-a", "author-b", "responder-a", "responder-b"):
        service.sync_user(actor(uid))

    values = {
        "topics": ["backend"],
        "languages": ["en"],
        "willing_intents": ["ask"],
        "profile_text": "backend",
        "willing": True,
        "active": True,
        "capacity_total": 1,
    }
    repository.upsert_profile("responder-a", values)
    repository.upsert_profile("responder-b", values)

    first = repository.create_request(
        "author-a", "request one", "ask", "idem-a",
        {"language": "en", "response_needed_prediction": True, "intent_source": "test"},
    )
    second = repository.create_request(
        "author-b", "request two", "ask", "idem-b",
        {"language": "en", "response_needed_prediction": True, "intent_source": "test"},
    )

    # Global optimum: first->B (0.80), second->A (0.85). A sequential
    # first-request greedy assignment would consume A with 0.90 and leave the
    # second request with B at 0.10.
    monkeypatch.setattr(
        "drsk.niyet_persistence.dynamic_relevance_matrix",
        lambda requests, profiles: np.array([[0.90, 0.80], [0.85, 0.10]], dtype=float),
    )

    service._allocate_open_requests()

    first_saved = repository.get_request(first["id"])
    second_saved = repository.get_request(second["id"])
    first_assignment = repository.get_assignment(first_saved["current_assignment_id"])
    second_assignment = repository.get_assignment(second_saved["current_assignment_id"])
    assert first_assignment["responder_uid"] == "responder-b"
    assert second_assignment["responder_uid"] == "responder-a"
