from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import re
from typing import Any, Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from niyet.classifier import build_tfidf_baseline, load_labeled_texts
from niyet.types import IntentType


SUPPORTED_INTENTS = tuple(intent.value for intent in IntentType)
SUPPORTED_LANGUAGES = ("en", "tr")
TOPIC_RETRIEVAL_WEIGHT = 0.80
PROFILE_RETRIEVAL_WEIGHT = 0.20
MIN_RELEVANCE = 0.02

_TURKISH_MARKERS = {
    "acaba", "ama", "bana", "ben", "bir", "bu", "da", "de", "icin", "için",
    "ile", "lazim", "lazım", "mi", "mı", "mu", "mü", "nasil", "nasıl", "neden",
    "olan", "olarak", "sen", "siz", "su", "şu", "ve", "yardim", "yardım",
}
_ENGLISH_MARKERS = {
    "a", "an", "and", "are", "can", "could", "for", "help", "how", "i", "is",
    "need", "of", "please", "review", "the", "this", "to", "we", "what", "why", "with",
}
_TURKISH_CHARS = re.compile(r"[çğıöşüÇĞİÖŞÜ]")
_TOKEN_RE = re.compile(r"[^\W_]+", flags=re.UNICODE)


@dataclass(frozen=True)
class NiyetTextAnalysis:
    response_needed: bool
    intent: str
    language: str


class NiyetTextAnalyzer:
    """Production text analysis shared by dynamic Firebase-backed NIYET routing.

    The two classifiers are the same committed, reproducible TF-IDF baselines
    used by the evaluated NIYET runtime. They are trained once per warm process
    from the repository's reviewed development data; responder identity/state
    remains fully dynamic in Firestore.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        root = Path(__file__).resolve().parents[2]
        data = Path(data_dir) if data_dir is not None else root / "data"

        gate_rows = load_labeled_texts(data / "response_gate_seed_v1.csv")
        intent_rows = load_labeled_texts(data / "intent_seed_v1.csv")

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

    def classify_response_needed(self, text: str) -> bool:
        return str(self.gate_model.predict([text])[0]).upper() == "RESPONSE"

    def classify_intent(self, text: str) -> str:
        value = str(self.intent_model.predict([text])[0]).strip().lower()
        return IntentType(value).value

    def analyze(self, text: str, *, language_hint: str | None = None) -> NiyetTextAnalysis:
        return NiyetTextAnalysis(
            response_needed=self.classify_response_needed(text),
            intent=self.classify_intent(text),
            language=normalize_request_language(language_hint, text),
        )


@lru_cache(maxsize=1)
def get_text_analyzer() -> NiyetTextAnalyzer:
    return NiyetTextAnalyzer()


def normalize_request_language(value: str | None, text: str) -> str:
    clean = value.strip().lower() if isinstance(value, str) else ""
    if clean in SUPPORTED_LANGUAGES:
        return clean
    if clean:
        raise ValueError("unsupported_request_language")
    return infer_language(text)


def infer_language(text: str) -> str:
    """Deterministic EN/TR fallback when a client does not provide a UI hint.

    Language is an eligibility constraint, not a hidden user trait. The client
    normally supplies the active UI language; this fallback only keeps API and
    non-UI integrations deterministic.
    """

    if _TURKISH_CHARS.search(text):
        return "tr"
    tokens = {token.lower() for token in _TOKEN_RE.findall(text)}
    tr_score = len(tokens & _TURKISH_MARKERS)
    en_score = len(tokens & _ENGLISH_MARKERS)
    return "tr" if tr_score > en_score else "en"


def _similarity(queries: Sequence[str], documents: Sequence[str]) -> np.ndarray:
    if not queries or not documents:
        return np.zeros((len(queries), len(documents)), dtype=float)
    if not any(document.strip() for document in documents):
        return np.zeros((len(queries), len(documents)), dtype=float)
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform([*queries, *documents])
    return cosine_similarity(matrix[: len(queries)], matrix[len(queries) :])


def dynamic_relevance_matrix(
    requests: Sequence[dict[str, Any]],
    profiles: Sequence[dict[str, Any]],
) -> np.ndarray:
    """Score dynamic Firestore responders with the evaluated lexical policy.

    Explicit topic metadata remains the primary signal. Optional profile prose
    contributes context without being allowed to overwhelm topics.
    """

    queries = [str(request.get("text", "")) for request in requests]
    topic_documents = [" ".join(str(item) for item in profile.get("topics", [])) for profile in profiles]
    profile_documents = [str(profile.get("profile_text", "")) for profile in profiles]
    topic = _similarity(queries, topic_documents)
    prose = _similarity(queries, profile_documents)
    return TOPIC_RETRIEVAL_WEIGHT * topic + PROFILE_RETRIEVAL_WEIGHT * prose
