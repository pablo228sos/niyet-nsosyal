from pathlib import Path


PATH = Path("src/drsk/niyet_persistence.py")
text = PATH.read_text(encoding="utf-8")


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one anchor, found {count}")
    text = text.replace(old, new, 1)


replace_once(
    "from niyet.types import CandidateMatch, Responder\n\nfrom .firebase_auth import AuthenticatedUser\n",
    "from niyet.types import CandidateMatch, IntentType, Responder\n\nfrom .firebase_auth import AuthenticatedUser\nfrom .niyet_matching import (\n    MIN_RELEVANCE,\n    SUPPORTED_INTENTS,\n    dynamic_relevance_matrix,\n    get_text_analyzer,\n)\n",
    "matching imports",
)

replace_once(
    '''                "languages": list(values["languages"]),
                "willing": values["willing"],
''',
    '''                "languages": list(values["languages"]),
                "willing_intents": list(values["willing_intents"]),
                "profile_text": values.get("profile_text", ""),
                "willing": values["willing"],
''',
    "memory profile fields",
)

replace_once(
    '''                "active": values["active"], "paused": bool(previous.get("paused", False)),
                "capacity_total": total, "capacity_remaining": remaining,
''',
    '''                "active": values["active"], "paused": bool(previous.get("paused", False)),
                "willing_intents": list(values["willing_intents"]),
                "profile_text": values.get("profile_text", ""),
                "capacity_total": total, "capacity_remaining": remaining,
''',
    "firestore profile fields",
)

replace_once(
    '''                "social_context": metadata.get("social_context"),
                "evidence_context": metadata.get("evidence_context"),
                "created_at": now, "updated_at": now,
''',
    '''                "social_context": metadata.get("social_context"),
                "evidence_context": metadata.get("evidence_context"),
                "language": metadata.get("language"),
                "created_at": now, "updated_at": now,
''',
    "memory post language",
)

replace_once(
    '''                "resolution": metadata.get("resolution"),
                "status": "OPEN",
''',
    '''                "resolution": metadata.get("resolution"),
                "language": metadata.get("language"),
                "response_needed_prediction": metadata.get("response_needed_prediction"),
                "intent_source": metadata.get("intent_source"),
                "status": "OPEN",
''',
    "memory request analysis metadata",
)

replace_once(
    '''                "social_context": metadata.get("social_context"),
                "evidence_context": metadata.get("evidence_context"),
                "created_at": firestore.SERVER_TIMESTAMP, "updated_at": firestore.SERVER_TIMESTAMP,
''',
    '''                "social_context": metadata.get("social_context"),
                "evidence_context": metadata.get("evidence_context"),
                "language": metadata.get("language"),
                "created_at": firestore.SERVER_TIMESTAMP, "updated_at": firestore.SERVER_TIMESTAMP,
''',
    "firestore post language",
)

replace_once(
    '''                "resolution": metadata.get("resolution"),
                "status": "OPEN", "current_assignment_id": None,
''',
    '''                "resolution": metadata.get("resolution"),
                "language": metadata.get("language"),
                "response_needed_prediction": metadata.get("response_needed_prediction"),
                "intent_source": metadata.get("intent_source"),
                "status": "OPEN", "current_assignment_id": None,
''',
    "firestore request analysis metadata",
)

replace_once(
    '''        payload = {
            "topics": topics,
            "languages": languages,
            "willing": bool(values.get("willing", False)),
''',
    '''        willing_intents = self._string_list(
            values.get("willing_intents", list(SUPPORTED_INTENTS)),
            "willing_intents",
        )
        if any(value not in SUPPORTED_INTENTS for value in willing_intents):
            raise DomainError("invalid_willing_intents")
        raw_profile_text = values.get("profile_text", "")
        if not isinstance(raw_profile_text, str) or len(raw_profile_text.strip()) > 500:
            raise DomainError("invalid_profile_text")
        payload = {
            "topics": topics,
            "languages": languages,
            "willing_intents": willing_intents,
            "profile_text": raw_profile_text.strip(),
            "willing": bool(values.get("willing", False)),
''',
    "service profile validation",
)

replace_once(
    '''        intent: str,
        idempotency_key: str | None = None,
        metadata: dict[str, Any] | None = None,
''',
    '''        intent: str | None = None,
        language: str | None = None,
        idempotency_key: str | None = None,
        metadata: dict[str, Any] | None = None,
''',
    "create request signature",
)

replace_once(
    '''        clean_intent = intent.strip().lower() if isinstance(intent, str) else ""
        if clean_intent not in {"ask", "feedback", "collaborate", "discuss"}:
            raise DomainError("invalid_intent")
        clean_key = idempotency_key.strip() if isinstance(idempotency_key, str) else _id("idem")
''',
    '''        # Intent is server-derived. Client intent is intentionally not trusted as
        # the routing label; explicit user activation can still request a human even
        # when the response-needed model would not auto-route the text.
        del intent
        try:
            analysis = get_text_analyzer().analyze(clean_text, language_hint=language)
        except ValueError as exc:
            raise DomainError(str(exc)) from exc
        clean_intent = analysis.intent
        clean_key = idempotency_key.strip() if isinstance(idempotency_key, str) else _id("idem")
''',
    "server intent classification",
)

replace_once(
    '''        request = self.repository.create_request(
            actor.uid,
            clean_text,
            clean_intent,
            clean_key,
            metadata or {},
        )
''',
    '''        request_metadata = dict(metadata or {})
        request_metadata.update({
            "language": analysis.language,
            "response_needed_prediction": analysis.response_needed,
            "intent_source": "niyet_tfidf_classifier",
        })
        request = self.repository.create_request(
            actor.uid,
            clean_text,
            clean_intent,
            clean_key,
            request_metadata,
        )
''',
    "persist classified request metadata",
)

start = text.index("    def _allocate(\n")
end = text.index("    def list_inbox(\n", start)
old_allocate = text[start:end]
new_allocate = '''    def _allocate(
        self,
        request: dict[str, Any],
        *,
        reallocated_from_assignment_id: str | None = None,
    ) -> dict[str, Any] | None:
        reallocation_sources = (
            {request["id"]: reallocated_from_assignment_id}
            if reallocated_from_assignment_id
            else None
        )
        self._allocate_window(reallocation_sources=reallocation_sources)
        refreshed = self.repository.get_request(request["id"])
        assignment_id = refreshed.get("current_assignment_id") if refreshed else None
        return self.repository.get_assignment(assignment_id) if assignment_id else None

    def _allocate_window(
        self,
        *,
        reallocation_sources: dict[str, str] | None = None,
    ) -> None:
        """Globally allocate the current open request window under hard constraints."""

        reallocation_sources = reallocation_sources or {}
        # A bounded retry absorbs transaction races without turning allocation
        # into an unbounded background loop in a serverless request.
        for _ in range(3):
            requests = self.repository.list_open_requests(limit=100)
            profiles = self.repository.eligible_profiles()
            if not requests or not profiles:
                return

            relevance = dynamic_relevance_matrix(requests, profiles)
            responders: list[Responder] = []
            available_by_uid: dict[str, int] = {}
            for profile in profiles:
                available = int(profile["capacity_remaining"]) - int(profile.get("pending_assignments", 0))
                if available <= 0:
                    continue
                uid = profile["uid"]
                available_by_uid[uid] = available
                responders.append(
                    Responder(
                        id=uid,
                        topics=tuple(profile.get("topics", [])),
                        willing_intents=tuple(IntentType(value) for value in profile.get("willing_intents", SUPPORTED_INTENTS)),
                        attention_budget=available,
                        active=True,
                    )
                )
            if not responders:
                return

            matches: list[CandidateMatch] = []
            relevance_by_pair: dict[tuple[str, str], float] = {}
            for request_index, request in enumerate(requests):
                excluded = set(request.get("excluded_responder_ids", []))
                request_intent = request.get("intent")
                request_language = request.get("language")
                for profile_index, profile in enumerate(profiles):
                    uid = profile["uid"]
                    available = available_by_uid.get(uid, 0)
                    if available <= 0 or uid == request["author_uid"] or uid in excluded:
                        continue
                    if request_intent not in profile.get("willing_intents", SUPPORTED_INTENTS):
                        continue
                    profile_languages = set(profile.get("languages", []))
                    if request_language and request_language not in profile_languages:
                        continue
                    score = float(relevance[request_index, profile_index])
                    if score < MIN_RELEVANCE:
                        continue
                    relevance_by_pair[(request["id"], uid)] = score
                    matches.append(
                        CandidateMatch(
                            request["id"],
                            uid,
                            min(1.0, score),
                            1.0,
                            available / max(1, int(profile["capacity_total"])),
                        )
                    )

            planned = global_allocate(matches, responders, min_score=0.0)
            if not planned:
                return

            applied = 0
            for candidate in planned:
                pair = (candidate.intent_id, candidate.responder_id)
                metadata: dict[str, Any] = {
                    "relevance": relevance_by_pair[pair],
                    "score": candidate.score,
                    "strategy": "niyet_global_allocate_dynamic_v1",
                }
                source = reallocation_sources.get(candidate.intent_id)
                if source:
                    metadata["reallocated_from_assignment_id"] = source
                assignment = self.repository.try_assign(
                    candidate.intent_id,
                    candidate.responder_id,
                    metadata,
                )
                if assignment:
                    applied += 1
            if applied == 0:
                return

'''
text = text[:start] + new_allocate + text[end:]

old_skip = '''        request = self.repository.get_request(assignment["request_id"])
        if request:
            replacement = self._allocate(
                request,
                reallocated_from_assignment_id=assignment_id,
            )
            if replacement:
                assignment["reallocated_assignment_id"] = replacement["id"]
        return assignment
'''
new_skip = '''        request = self.repository.get_request(assignment["request_id"])
        if request:
            replacement = self._allocate(
                request,
                reallocated_from_assignment_id=assignment_id,
            )
            if replacement:
                assignment["reallocated_assignment_id"] = replacement["id"]
        return assignment
'''
# The method body remains API-compatible; _allocate now evaluates the full window.
if text.count(old_skip) != 1:
    raise SystemExit("skip allocation anchor missing")

old_reallocate = '''    def _reallocate_released(self, released: list[dict[str, Any]]) -> None:
        for assignment in released:
            request = self.repository.get_request(assignment["request_id"])
            if request:
                self._allocate(
                    request,
                    reallocated_from_assignment_id=assignment["id"],
                )
'''
new_reallocate = '''    def _reallocate_released(self, released: list[dict[str, Any]]) -> None:
        if not released:
            return
        sources = {
            assignment["request_id"]: assignment["id"]
            for assignment in released
        }
        self._allocate_window(reallocation_sources=sources)
'''
replace_once(old_reallocate, new_reallocate, "global reallocation window")

old_open = '''    def _allocate_open_requests(self) -> None:
        for request in self.repository.list_open_requests():
            self._allocate(request)
'''
new_open = '''    def _allocate_open_requests(self) -> None:
        self._allocate_window()
'''
replace_once(old_open, new_open, "global open request allocation")

PATH.write_text(text, encoding="utf-8")
