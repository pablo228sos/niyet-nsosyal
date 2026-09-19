from __future__ import annotations

import copy
import hashlib
import math
import re
import threading
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import uuid4

from niyet.optimizer import global_allocate
from niyet.types import CandidateMatch, IntentType, Responder

from .firebase_auth import AuthenticatedUser
from .niyet_matching import (
    MIN_RELEVANCE,
    SUPPORTED_INTENTS,
    dynamic_relevance_matrix,
    get_text_analyzer,
)


ACTIVE_ASSIGNMENT_STATUSES = {"PENDING", "ACCEPTED"}
PENDING_ASSIGNMENT_TTL = timedelta(minutes=30)


class DomainError(RuntimeError):
    def __init__(self, code: str, status: int = 400) -> None:
        super().__init__(code)
        self.code = code
        self.status = status


def _now() -> datetime:
    return datetime.now(UTC)


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _stable_id(prefix: str, uid: str, idempotency_key: str) -> str:
    digest = hashlib.sha256(f"{uid}\0{idempotency_key}".encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:32]}"


class NiyetRepository(Protocol):
    def upsert_user(self, actor: AuthenticatedUser) -> dict[str, Any]: ...
    def get_user(self, uid: str) -> dict[str, Any] | None: ...
    def upsert_profile(self, uid: str, values: dict[str, Any]) -> dict[str, Any]: ...
    def get_profile(self, uid: str) -> dict[str, Any] | None: ...
    def eligible_profiles(self) -> list[dict[str, Any]]: ...
    def create_request(self, uid: str, text: str, intent: str, idempotency_key: str, metadata: dict[str, Any]) -> dict[str, Any]: ...
    def try_assign(self, request_id: str, responder_uid: str, metadata: dict[str, Any]) -> dict[str, Any] | None: ...
    def accept(self, uid: str, assignment_id: str) -> dict[str, Any]: ...
    def skip(self, uid: str, assignment_id: str) -> dict[str, Any]: ...
    def answer(self, uid: str, assignment_id: str, answer: str) -> dict[str, Any]: ...
    def set_paused(self, uid: str, paused: bool) -> dict[str, Any]: ...
    def release_pending_assignments(self, uid: str, reason: str) -> list[dict[str, Any]]: ...
    def expire_stale_assignments(self) -> list[dict[str, Any]]: ...
    def list_inbox(self, uid: str) -> list[dict[str, Any]]: ...
    def list_open_requests(self, limit: int = 100) -> list[dict[str, Any]]: ...
    def get_request(self, request_id: str) -> dict[str, Any] | None: ...
    def get_assignment(self, assignment_id: str) -> dict[str, Any] | None: ...


class MemoryNiyetRepository:
    """Deterministic test/local repository with the Firestore transaction semantics."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.users: dict[str, dict[str, Any]] = {}
        self.profiles: dict[str, dict[str, Any]] = {}
        self.posts: dict[str, dict[str, Any]] = {}
        self.requests: dict[str, dict[str, Any]] = {}
        self.assignments: dict[str, dict[str, Any]] = {}
        self.events: dict[str, dict[str, Any]] = {}

    def _event(self, event_type: str, **values: Any) -> None:
        event_id = _id("evt")
        self.events[event_id] = {
            "id": event_id,
            "type": event_type,
            "created_at": _now(),
            **values,
        }

    def upsert_user(self, actor: AuthenticatedUser) -> dict[str, Any]:
        with self._lock:
            previous = self.users.get(actor.uid, {})
            value = {
                "uid": actor.uid,
                "email": actor.email,
                "display_name": actor.display_name,
                "photo_url": actor.photo_url,
                "provider_ids": list(actor.provider_ids),
                "created_at": previous.get("created_at", _now()),
                "updated_at": _now(),
            }
            self.users[actor.uid] = value
            return copy.deepcopy(value)

    def get_user(self, uid: str) -> dict[str, Any] | None:
        with self._lock:
            return copy.deepcopy(self.users.get(uid))

    def upsert_profile(self, uid: str, values: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            if uid not in self.users:
                raise DomainError("user_not_found", 404)
            previous = self.profiles.get(uid)
            total = values["capacity_total"]
            consumed = 0 if previous is None else previous["capacity_total"] - previous["capacity_remaining"]
            pending = 0 if previous is None else previous.get("pending_assignments", 0)
            remaining = max(0, total - consumed)
            if remaining < pending and values["willing"] and values["active"] and not (previous or {}).get("paused", False):
                raise DomainError("capacity_below_pending_assignments", 409)
            profile = {
                "uid": uid,
                "topics": list(values["topics"]),
                "expertise": list(values["topics"]),
                "languages": list(values["languages"]),
                "willing_intents": list(values["willing_intents"]),
                "profile_text": values.get("profile_text", ""),
                "willing": values["willing"],
                "active": values["active"],
                "paused": previous.get("paused", False) if previous else False,
                "capacity_total": total,
                "capacity_remaining": remaining,
                "pending_assignments": pending,
                "quality_threshold": values.get("quality_threshold", 0.0),
                "created_at": previous.get("created_at", _now()) if previous else _now(),
                "updated_at": _now(),
            }
            self.profiles[uid] = profile
            return copy.deepcopy(profile)

    def get_profile(self, uid: str) -> dict[str, Any] | None:
        with self._lock:
            return copy.deepcopy(self.profiles.get(uid))

    def eligible_profiles(self) -> list[dict[str, Any]]:
        with self._lock:
            return copy.deepcopy([
                value for value in self.profiles.values()
                if value["willing"] and value["active"] and not value["paused"]
                and value["capacity_remaining"] > value.get("pending_assignments", 0)
            ])

    def create_request(
        self,
        uid: str,
        text: str,
        intent: str,
        idempotency_key: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        with self._lock:
            if uid not in self.users:
                raise DomainError("user_not_found", 404)
            now = _now()
            post_id = _stable_id("post", uid, idempotency_key)
            request_id = _stable_id("req", uid, idempotency_key)
            existing = self.requests.get(request_id)
            if existing is not None:
                if existing.get("text") != text or existing.get("intent") != intent:
                    raise DomainError("idempotency_conflict", 409)
                return copy.deepcopy(existing)
            self.posts[post_id] = {
                "id": post_id, "author_uid": uid, "text": text,
                "social_context": metadata.get("social_context"),
                "evidence_context": metadata.get("evidence_context"),
                "language": metadata.get("language"),
                "created_at": now, "updated_at": now,
            }
            request = {
                "id": request_id,
                "request_id": request_id,
                "author_uid": uid,
                "post_id": post_id,
                "text": text,
                "context": text,
                "intent": intent,
                "idempotency_key": idempotency_key,
                "social_context": metadata.get("social_context"),
                "evidence_context": metadata.get("evidence_context"),
                "resolution": metadata.get("resolution"),
                "language": metadata.get("language"),
                "response_needed_prediction": metadata.get("response_needed_prediction"),
                "intent_source": metadata.get("intent_source"),
                "status": "OPEN",
                "current_assignment_id": None,
                "excluded_responder_ids": [],
                "created_at": now,
                "updated_at": now,
            }
            self.requests[request_id] = request
            self._event("REQUEST_CREATED", actor_uid=uid, request_id=request_id, post_id=post_id)
            return copy.deepcopy(request)

    def try_assign(self, request_id: str, responder_uid: str, metadata: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock:
            request = self.requests.get(request_id)
            profile = self.profiles.get(responder_uid)
            if request is None:
                raise DomainError("request_not_found", 404)
            if request["current_assignment_id"] or request["status"] not in {"OPEN", "UNMATCHED"}:
                return None
            if responder_uid in request["excluded_responder_ids"] or profile is None:
                return None
            if not profile["willing"] or not profile["active"] or profile["paused"]:
                return None
            if profile["pending_assignments"] >= profile["capacity_remaining"]:
                return None
            now, assignment_id = _now(), _id("asn")
            assignment = {
                "id": assignment_id,
                "assignment_id": assignment_id,
                "request_id": request_id,
                "responder_uid": responder_uid,
                "status": "PENDING",
                "relevance": metadata.get("relevance"),
                "match_metadata": metadata,
                "accepted_at": None,
                "skipped_at": None,
                "expires_at": now + PENDING_ASSIGNMENT_TTL,
                "created_at": now,
                "updated_at": now,
            }
            self.assignments[assignment_id] = assignment
            request.update(status="ASSIGNED", current_assignment_id=assignment_id, updated_at=now)
            profile["pending_assignments"] += 1
            profile["updated_at"] = now
            self._event("ASSIGNED", request_id=request_id, assignment_id=assignment_id, responder_uid=responder_uid)
            if metadata.get("reallocated_from_assignment_id"):
                self._event(
                    "REALLOCATED",
                    request_id=request_id,
                    assignment_id=assignment_id,
                    previous_assignment_id=metadata["reallocated_from_assignment_id"],
                    responder_uid=responder_uid,
                )
            return copy.deepcopy(assignment)

    def accept(self, uid: str, assignment_id: str) -> dict[str, Any]:
        with self._lock:
            assignment = self.assignments.get(assignment_id)
            if assignment is None:
                raise DomainError("assignment_not_found", 404)
            if assignment["responder_uid"] != uid:
                raise DomainError("permission_denied", 403)
            if assignment["status"] == "ACCEPTED":
                return copy.deepcopy(assignment)
            if assignment["status"] != "PENDING":
                raise DomainError("stale_assignment", 409)
            expires_at = assignment.get("expires_at")
            if isinstance(expires_at, datetime) and expires_at <= _now():
                raise DomainError("assignment_expired", 409)
            request = self.requests[assignment["request_id"]]
            profile = self.profiles.get(uid)
            if request["current_assignment_id"] != assignment_id:
                raise DomainError("stale_assignment", 409)
            if profile is None:
                raise DomainError("responder_profile_not_found", 404)
            if profile["paused"] or not profile["willing"] or not profile["active"]:
                raise DomainError("responder_paused", 409)
            if profile["capacity_remaining"] <= 0:
                raise DomainError("capacity_exhausted", 409)
            now = _now()
            assignment.update(status="ACCEPTED", accepted_at=now, updated_at=now)
            request.update(status="ACCEPTED", updated_at=now)
            profile["capacity_remaining"] -= 1
            profile["pending_assignments"] = max(0, profile["pending_assignments"] - 1)
            profile["updated_at"] = now
            self._event("ACCEPTED", actor_uid=uid, request_id=request["id"], assignment_id=assignment_id)
            return copy.deepcopy(assignment)

    def skip(self, uid: str, assignment_id: str) -> dict[str, Any]:
        with self._lock:
            assignment = self.assignments.get(assignment_id)
            if assignment is None:
                raise DomainError("assignment_not_found", 404)
            if assignment["responder_uid"] != uid:
                raise DomainError("permission_denied", 403)
            if assignment["status"] == "SKIPPED":
                return copy.deepcopy(assignment)
            if assignment["status"] != "PENDING":
                raise DomainError("stale_assignment", 409)
            request = self.requests[assignment["request_id"]]
            if request["current_assignment_id"] != assignment_id:
                raise DomainError("stale_assignment", 409)
            profile = self.profiles.get(uid)
            now = _now()
            assignment.update(status="SKIPPED", skipped_at=now, updated_at=now)
            request["excluded_responder_ids"] = list(dict.fromkeys([*request["excluded_responder_ids"], uid]))
            request.update(status="OPEN", current_assignment_id=None, updated_at=now)
            if profile:
                profile["pending_assignments"] = max(0, profile["pending_assignments"] - 1)
                profile["updated_at"] = now
            self._event("SKIPPED", actor_uid=uid, request_id=request["id"], assignment_id=assignment_id)
            return copy.deepcopy(assignment)

    def answer(self, uid: str, assignment_id: str, answer: str) -> dict[str, Any]:
        with self._lock:
            assignment = self.assignments.get(assignment_id)
            if assignment is None:
                raise DomainError("assignment_not_found", 404)
            if assignment["responder_uid"] != uid:
                raise DomainError("permission_denied", 403)
            if assignment["status"] == "ANSWERED":
                if assignment.get("answer") == answer:
                    return copy.deepcopy(assignment)
                raise DomainError("answer_already_submitted", 409)
            if assignment["status"] != "ACCEPTED":
                raise DomainError("stale_assignment", 409)
            request = self.requests[assignment["request_id"]]
            if request.get("current_assignment_id") != assignment_id or request.get("status") != "ACCEPTED":
                raise DomainError("stale_assignment", 409)
            now = _now()
            resolution = {
                "type": "HUMAN_ANSWER",
                "answer": answer,
                "responder_uid": uid,
                "assignment_id": assignment_id,
                "resolved_at": now,
            }
            assignment.update(status="ANSWERED", answer=answer, answered_at=now, updated_at=now)
            request.update(status="ANSWERED", answer=answer, resolution=resolution, resolved_at=now, updated_at=now)
            post = self.posts.get(request["post_id"])
            if post is not None:
                post.update(resolution=resolution, updated_at=now)
            # Preserve the existing NIYET attention-budget contract:
            # Accept consumes capacity; completing the answer does not restore it.
            self._event("ANSWERED", actor_uid=uid, request_id=request["id"], assignment_id=assignment_id)
            return copy.deepcopy(assignment)

    def set_paused(self, uid: str, paused: bool) -> dict[str, Any]:
        with self._lock:
            profile = self.profiles.get(uid)
            if profile is None:
                raise DomainError("responder_profile_not_found", 404)
            profile.update(paused=paused, updated_at=_now())
            self._event("PAUSED" if paused else "RESUMED", actor_uid=uid, responder_uid=uid)
            return copy.deepcopy(profile)

    def _release_pending(self, assignment: dict[str, Any], reason: str, status: str) -> dict[str, Any] | None:
        if assignment.get("status") != "PENDING":
            return None
        request = self.requests.get(assignment["request_id"])
        if request is None or request.get("current_assignment_id") != assignment["id"]:
            return None
        profile = self.profiles.get(assignment["responder_uid"])
        now = _now()
        assignment.update(status=status, release_reason=reason, released_at=now, updated_at=now)
        if status == "EXPIRED":
            request["excluded_responder_ids"] = list(dict.fromkeys([
                *request.get("excluded_responder_ids", []),
                assignment["responder_uid"],
            ]))
        request.update(status="OPEN", current_assignment_id=None, updated_at=now)
        if profile is not None:
            profile["pending_assignments"] = max(0, profile.get("pending_assignments", 0) - 1)
            profile["updated_at"] = now
        self._event(status, request_id=request["id"], assignment_id=assignment["id"], reason=reason)
        return copy.deepcopy(assignment)

    def release_pending_assignments(self, uid: str, reason: str) -> list[dict[str, Any]]:
        with self._lock:
            released = []
            for assignment in list(self.assignments.values()):
                if assignment.get("responder_uid") == uid:
                    value = self._release_pending(assignment, reason, "CANCELLED")
                    if value:
                        released.append(value)
            return released

    def expire_stale_assignments(self) -> list[dict[str, Any]]:
        with self._lock:
            now = _now()
            released = []
            for assignment in list(self.assignments.values()):
                expires_at = assignment.get("expires_at")
                if isinstance(expires_at, datetime) and expires_at <= now:
                    value = self._release_pending(assignment, "assignment_ttl_elapsed", "EXPIRED")
                    if value:
                        released.append(value)
            return released

    def list_inbox(self, uid: str) -> list[dict[str, Any]]:
        with self._lock:
            output = []
            for assignment in self.assignments.values():
                if assignment["responder_uid"] != uid or assignment["status"] not in ACTIVE_ASSIGNMENT_STATUSES:
                    continue
                item = copy.deepcopy(assignment)
                item["request"] = copy.deepcopy(self.requests[assignment["request_id"]])
                output.append(item)
            return sorted(output, key=lambda item: item["created_at"])

    def list_open_requests(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            values = [
                copy.deepcopy(request)
                for request in self.requests.values()
                if request.get("status") in {"OPEN", "UNMATCHED"}
                and not request.get("current_assignment_id")
            ]
            return sorted(values, key=lambda item: item["created_at"])[:limit]

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        with self._lock:
            return copy.deepcopy(self.requests.get(request_id))

    def get_assignment(self, assignment_id: str) -> dict[str, Any] | None:
        with self._lock:
            return copy.deepcopy(self.assignments.get(assignment_id))

    def force_pending_assignment(self, *, author_uid: str, responder_uid: str, text: str) -> str:
        with self._lock:
            if author_uid not in self.users:
                self.upsert_user(AuthenticatedUser(author_uid, None, None, None, (), {"uid": author_uid}))
            request = self.create_request(author_uid, text, "ask", _id("idem"), {})
            assignment_id = _id("asn")
            now = _now()
            self.assignments[assignment_id] = {
                "id": assignment_id, "assignment_id": assignment_id,
                "request_id": request["id"], "responder_uid": responder_uid,
                "status": "PENDING", "relevance": 1.0, "match_metadata": {},
                "accepted_at": None, "skipped_at": None,
                "expires_at": now + PENDING_ASSIGNMENT_TTL,
                "created_at": now, "updated_at": now,
            }
            self.requests[request["id"]].update(status="ASSIGNED", current_assignment_id=assignment_id)
            profile = self.profiles.get(responder_uid)
            if profile is not None:
                profile["pending_assignments"] = profile.get("pending_assignments", 0) + 1
            return assignment_id


class FirestoreNiyetRepository:
    """Structured Firestore persistence. Every capacity/assignment transition is transactional."""

    def __init__(self, client: Any) -> None:
        self.client = client

    @staticmethod
    def _firestore() -> Any:
        from firebase_admin import firestore
        return firestore

    @staticmethod
    def _data(snapshot: Any) -> dict[str, Any] | None:
        if not snapshot.exists:
            return None
        value = snapshot.to_dict() or {}
        value.setdefault("id", snapshot.id)
        return value

    def _run(self, callback: Any) -> Any:
        firestore = self._firestore()
        transaction = self.client.transaction()
        try:
            return firestore.transactional(callback)(transaction)
        except DomainError:
            raise
        except Exception as exc:
            from google.api_core.exceptions import Aborted, Conflict, DeadlineExceeded, ServiceUnavailable

            if isinstance(exc, (Aborted, Conflict)):
                raise DomainError("transaction_conflict", 409) from exc
            if isinstance(exc, (DeadlineExceeded, ServiceUnavailable)):
                raise DomainError("firestore_unavailable", 503) from exc
            raise

    def _event_ref(self) -> Any:
        return self.client.collection("events").document(_id("evt"))

    def upsert_user(self, actor: AuthenticatedUser) -> dict[str, Any]:
        ref = self.client.collection("users").document(actor.uid)
        firestore = self._firestore()

        def operation(transaction: Any) -> dict[str, Any]:
            snapshot = ref.get(transaction=transaction)
            previous = snapshot.to_dict() if snapshot.exists else {}
            payload = {
                "uid": actor.uid, "email": actor.email, "display_name": actor.display_name,
                "photo_url": actor.photo_url, "provider_ids": list(actor.provider_ids),
                "created_at": previous.get("created_at", firestore.SERVER_TIMESTAMP),
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
            transaction.set(ref, payload)
            return payload

        return self._run(operation)

    def get_user(self, uid: str) -> dict[str, Any] | None:
        return self._data(self.client.collection("users").document(uid).get())

    def upsert_profile(self, uid: str, values: dict[str, Any]) -> dict[str, Any]:
        profile_ref = self.client.collection("responder_profiles").document(uid)
        user_ref = self.client.collection("users").document(uid)
        firestore = self._firestore()

        def operation(transaction: Any) -> dict[str, Any]:
            if not user_ref.get(transaction=transaction).exists:
                raise DomainError("user_not_found", 404)
            snapshot = profile_ref.get(transaction=transaction)
            previous = snapshot.to_dict() if snapshot.exists else {}
            total = values["capacity_total"]
            consumed = int(previous.get("capacity_total", 0)) - int(previous.get("capacity_remaining", 0))
            pending = int(previous.get("pending_assignments", 0))
            remaining = max(0, total - max(0, consumed))
            if remaining < pending and values["willing"] and values["active"] and not bool(previous.get("paused", False)):
                raise DomainError("capacity_below_pending_assignments", 409)
            payload = {
                "uid": uid, "topics": list(values["topics"]), "expertise": list(values["topics"]),
                "languages": list(values["languages"]), "willing": values["willing"],
                "active": values["active"], "paused": bool(previous.get("paused", False)),
                "willing_intents": list(values["willing_intents"]),
                "profile_text": values.get("profile_text", ""),
                "capacity_total": total, "capacity_remaining": remaining,
                "pending_assignments": pending,
                "quality_threshold": values.get("quality_threshold", 0.0),
                "created_at": previous.get("created_at", firestore.SERVER_TIMESTAMP),
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
            transaction.set(profile_ref, payload)
            return payload

        return self._run(operation)

    def get_profile(self, uid: str) -> dict[str, Any] | None:
        return self._data(self.client.collection("responder_profiles").document(uid).get())

    def eligible_profiles(self) -> list[dict[str, Any]]:
        output = []
        for snapshot in self.client.collection("responder_profiles").where("willing", "==", True).stream():
            value = self._data(snapshot) or {}
            if value.get("active") and not value.get("paused") and int(value.get("capacity_remaining", 0)) > int(value.get("pending_assignments", 0)):
                output.append(value)
        return output

    def create_request(
        self,
        uid: str,
        text: str,
        intent: str,
        idempotency_key: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        firestore = self._firestore()
        post_id = _stable_id("post", uid, idempotency_key)
        request_id = _stable_id("req", uid, idempotency_key)
        post_ref = self.client.collection("posts").document(post_id)
        request_ref = self.client.collection("niyet_requests").document(request_id)
        event_ref = self._event_ref()

        def operation(transaction: Any) -> dict[str, Any]:
            if not self.client.collection("users").document(uid).get(transaction=transaction).exists:
                raise DomainError("user_not_found", 404)
            existing = request_ref.get(transaction=transaction)
            if existing.exists:
                value = existing.to_dict() or {}
                if value.get("text") != text or value.get("intent") != intent:
                    raise DomainError("idempotency_conflict", 409)
                value.setdefault("id", request_id)
                return value
            transaction.set(post_ref, {
                "id": post_id, "author_uid": uid, "text": text,
                "social_context": metadata.get("social_context"),
                "evidence_context": metadata.get("evidence_context"),
                "language": metadata.get("language"),
                "created_at": firestore.SERVER_TIMESTAMP, "updated_at": firestore.SERVER_TIMESTAMP,
            })
            request = {
                "id": request_id, "request_id": request_id, "author_uid": uid,
                "post_id": post_id, "text": text, "context": text, "intent": intent,
                "idempotency_key": idempotency_key,
                "social_context": metadata.get("social_context"),
                "evidence_context": metadata.get("evidence_context"),
                "resolution": metadata.get("resolution"),
                "language": metadata.get("language"),
                "response_needed_prediction": metadata.get("response_needed_prediction"),
                "intent_source": metadata.get("intent_source"),
                "status": "OPEN", "current_assignment_id": None,
                "excluded_responder_ids": [], "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
            transaction.set(request_ref, request)
            transaction.set(event_ref, {
                "id": event_ref.id, "type": "REQUEST_CREATED", "actor_uid": uid,
                "request_id": request_id, "post_id": post_id,
                "created_at": firestore.SERVER_TIMESTAMP,
            })
            return request

        return self._run(operation)

    def try_assign(self, request_id: str, responder_uid: str, metadata: dict[str, Any]) -> dict[str, Any] | None:
        firestore = self._firestore()
        request_ref = self.client.collection("niyet_requests").document(request_id)
        profile_ref = self.client.collection("responder_profiles").document(responder_uid)
        assignment_id = _id("asn")
        assignment_ref = self.client.collection("assignments").document(assignment_id)
        event_ref = self._event_ref()
        reallocation_ref = self._event_ref() if metadata.get("reallocated_from_assignment_id") else None

        def operation(transaction: Any) -> dict[str, Any] | None:
            request_snapshot = request_ref.get(transaction=transaction)
            profile_snapshot = profile_ref.get(transaction=transaction)
            if not request_snapshot.exists:
                raise DomainError("request_not_found", 404)
            request, profile = request_snapshot.to_dict(), profile_snapshot.to_dict() if profile_snapshot.exists else None
            if request.get("current_assignment_id") or request.get("status") not in {"OPEN", "UNMATCHED"}:
                return None
            if responder_uid in request.get("excluded_responder_ids", []) or not profile:
                return None
            if not profile.get("willing") or not profile.get("active") or profile.get("paused"):
                return None
            if int(profile.get("pending_assignments", 0)) >= int(profile.get("capacity_remaining", 0)):
                return None
            assignment = {
                "id": assignment_id, "assignment_id": assignment_id, "request_id": request_id,
                "responder_uid": responder_uid, "status": "PENDING",
                "relevance": metadata.get("relevance"), "match_metadata": metadata,
                "accepted_at": None, "skipped_at": None,
                "expires_at": _now() + PENDING_ASSIGNMENT_TTL,
                "created_at": firestore.SERVER_TIMESTAMP, "updated_at": firestore.SERVER_TIMESTAMP,
            }
            transaction.set(assignment_ref, assignment)
            transaction.update(request_ref, {"status": "ASSIGNED", "current_assignment_id": assignment_id, "updated_at": firestore.SERVER_TIMESTAMP})
            transaction.update(profile_ref, {"pending_assignments": int(profile.get("pending_assignments", 0)) + 1, "updated_at": firestore.SERVER_TIMESTAMP})
            transaction.set(event_ref, {"id": event_ref.id, "type": "ASSIGNED", "request_id": request_id, "assignment_id": assignment_id, "responder_uid": responder_uid, "created_at": firestore.SERVER_TIMESTAMP})
            if reallocation_ref is not None:
                transaction.set(reallocation_ref, {
                    "id": reallocation_ref.id,
                    "type": "REALLOCATED",
                    "request_id": request_id,
                    "assignment_id": assignment_id,
                    "previous_assignment_id": metadata["reallocated_from_assignment_id"],
                    "responder_uid": responder_uid,
                    "created_at": firestore.SERVER_TIMESTAMP,
                })
            return assignment

        return self._run(operation)

    def _assignment_transition(self, uid: str, assignment_id: str, action: str) -> dict[str, Any]:
        firestore = self._firestore()
        assignment_ref = self.client.collection("assignments").document(assignment_id)
        event_ref = self._event_ref()

        def operation(transaction: Any) -> dict[str, Any]:
            assignment_snapshot = assignment_ref.get(transaction=transaction)
            if not assignment_snapshot.exists:
                raise DomainError("assignment_not_found", 404)
            assignment = assignment_snapshot.to_dict()
            if assignment.get("responder_uid") != uid:
                raise DomainError("permission_denied", 403)
            target = "ACCEPTED" if action == "accept" else "SKIPPED"
            if assignment.get("status") == target:
                return {**assignment, "id": assignment_id}
            if assignment.get("status") != "PENDING":
                raise DomainError("stale_assignment", 409)
            expires_at = assignment.get("expires_at")
            if isinstance(expires_at, datetime) and expires_at <= _now():
                raise DomainError("assignment_expired", 409)
            request_ref = self.client.collection("niyet_requests").document(assignment["request_id"])
            profile_ref = self.client.collection("responder_profiles").document(uid)
            request_snapshot = request_ref.get(transaction=transaction)
            profile_snapshot = profile_ref.get(transaction=transaction)
            if not request_snapshot.exists:
                raise DomainError("request_not_found", 404)
            if not profile_snapshot.exists:
                raise DomainError("responder_profile_not_found", 404)
            request, profile = request_snapshot.to_dict(), profile_snapshot.to_dict()
            if request.get("current_assignment_id") != assignment_id:
                raise DomainError("stale_assignment", 409)
            common = {"status": target, "updated_at": firestore.SERVER_TIMESTAMP}
            if action == "accept":
                if profile.get("paused") or not profile.get("willing") or not profile.get("active"):
                    raise DomainError("responder_paused", 409)
                remaining = int(profile.get("capacity_remaining", 0))
                if remaining <= 0:
                    raise DomainError("capacity_exhausted", 409)
                transaction.update(assignment_ref, {**common, "accepted_at": firestore.SERVER_TIMESTAMP})
                transaction.update(request_ref, {"status": "ACCEPTED", "updated_at": firestore.SERVER_TIMESTAMP})
                transaction.update(profile_ref, {"capacity_remaining": remaining - 1, "pending_assignments": max(0, int(profile.get("pending_assignments", 0)) - 1), "updated_at": firestore.SERVER_TIMESTAMP})
            else:
                excluded = list(dict.fromkeys([*request.get("excluded_responder_ids", []), uid]))
                transaction.update(assignment_ref, {**common, "skipped_at": firestore.SERVER_TIMESTAMP})
                transaction.update(request_ref, {"status": "OPEN", "current_assignment_id": None, "excluded_responder_ids": excluded, "updated_at": firestore.SERVER_TIMESTAMP})
                transaction.update(profile_ref, {"pending_assignments": max(0, int(profile.get("pending_assignments", 0)) - 1), "updated_at": firestore.SERVER_TIMESTAMP})
            transaction.set(event_ref, {"id": event_ref.id, "type": target, "actor_uid": uid, "request_id": assignment["request_id"], "assignment_id": assignment_id, "created_at": firestore.SERVER_TIMESTAMP})
            return {**assignment, "id": assignment_id, "status": target}

        return self._run(operation)

    def accept(self, uid: str, assignment_id: str) -> dict[str, Any]:
        return self._assignment_transition(uid, assignment_id, "accept")

    def skip(self, uid: str, assignment_id: str) -> dict[str, Any]:
        return self._assignment_transition(uid, assignment_id, "skip")

    def answer(self, uid: str, assignment_id: str, answer: str) -> dict[str, Any]:
        firestore = self._firestore()
        assignment_ref = self.client.collection("assignments").document(assignment_id)
        event_ref = self._event_ref()

        def operation(transaction: Any) -> dict[str, Any]:
            assignment_snapshot = assignment_ref.get(transaction=transaction)
            if not assignment_snapshot.exists:
                raise DomainError("assignment_not_found", 404)
            assignment = assignment_snapshot.to_dict() or {}
            if assignment.get("responder_uid") != uid:
                raise DomainError("permission_denied", 403)
            if assignment.get("status") == "ANSWERED":
                if assignment.get("answer") == answer:
                    return {**assignment, "id": assignment_id}
                raise DomainError("answer_already_submitted", 409)
            if assignment.get("status") != "ACCEPTED":
                raise DomainError("stale_assignment", 409)
            request_ref = self.client.collection("niyet_requests").document(assignment["request_id"])
            request_snapshot = request_ref.get(transaction=transaction)
            if not request_snapshot.exists:
                raise DomainError("request_not_found", 404)
            request = request_snapshot.to_dict() or {}
            if request.get("current_assignment_id") != assignment_id or request.get("status") != "ACCEPTED":
                raise DomainError("stale_assignment", 409)
            post_ref = self.client.collection("posts").document(request["post_id"])
            # Capacity is an attention/daily budget consumed on Accept,
            # not a concurrent-work slot released on Answer.
            resolution = {
                "type": "HUMAN_ANSWER",
                "answer": answer,
                "responder_uid": uid,
                "assignment_id": assignment_id,
                "resolved_at": firestore.SERVER_TIMESTAMP,
            }
            transaction.update(assignment_ref, {
                "status": "ANSWERED", "answer": answer,
                "answered_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            transaction.update(request_ref, {
                "status": "ANSWERED", "answer": answer, "resolution": resolution,
                "resolved_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            transaction.update(post_ref, {
                "resolution": resolution,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            transaction.set(event_ref, {
                "id": event_ref.id, "type": "ANSWERED", "actor_uid": uid,
                "request_id": assignment["request_id"], "assignment_id": assignment_id,
                "created_at": firestore.SERVER_TIMESTAMP,
            })
            return {**assignment, "id": assignment_id, "status": "ANSWERED", "answer": answer}

        return self._run(operation)

    def set_paused(self, uid: str, paused: bool) -> dict[str, Any]:
        firestore = self._firestore()
        profile_ref = self.client.collection("responder_profiles").document(uid)
        event_ref = self._event_ref()

        def operation(transaction: Any) -> dict[str, Any]:
            snapshot = profile_ref.get(transaction=transaction)
            if not snapshot.exists:
                raise DomainError("responder_profile_not_found", 404)
            profile = snapshot.to_dict()
            transaction.update(profile_ref, {"paused": paused, "updated_at": firestore.SERVER_TIMESTAMP})
            transaction.set(event_ref, {"id": event_ref.id, "type": "PAUSED" if paused else "RESUMED", "actor_uid": uid, "responder_uid": uid, "created_at": firestore.SERVER_TIMESTAMP})
            return {**profile, "uid": uid, "paused": paused}

        return self._run(operation)

    def _release_pending(self, assignment_id: str, reason: str, status: str) -> dict[str, Any] | None:
        firestore = self._firestore()
        assignment_ref = self.client.collection("assignments").document(assignment_id)
        event_ref = self._event_ref()

        def operation(transaction: Any) -> dict[str, Any] | None:
            assignment_snapshot = assignment_ref.get(transaction=transaction)
            if not assignment_snapshot.exists:
                return None
            assignment = assignment_snapshot.to_dict() or {}
            if assignment.get("status") != "PENDING":
                return None
            request_ref = self.client.collection("niyet_requests").document(assignment["request_id"])
            profile_ref = self.client.collection("responder_profiles").document(assignment["responder_uid"])
            request_snapshot = request_ref.get(transaction=transaction)
            profile_snapshot = profile_ref.get(transaction=transaction)
            if not request_snapshot.exists:
                return None
            request = request_snapshot.to_dict() or {}
            if request.get("current_assignment_id") != assignment_id:
                return None
            profile = profile_snapshot.to_dict() if profile_snapshot.exists else {}
            transaction.update(assignment_ref, {
                "status": status, "release_reason": reason,
                "released_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            request_update = {
                "status": "OPEN", "current_assignment_id": None,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
            if status == "EXPIRED":
                request_update["excluded_responder_ids"] = list(dict.fromkeys([
                    *request.get("excluded_responder_ids", []),
                    assignment["responder_uid"],
                ]))
            transaction.update(request_ref, request_update)
            if profile_snapshot.exists:
                transaction.update(profile_ref, {
                    "pending_assignments": max(0, int(profile.get("pending_assignments", 0)) - 1),
                    "updated_at": firestore.SERVER_TIMESTAMP,
                })
            transaction.set(event_ref, {
                "id": event_ref.id, "type": status,
                "request_id": assignment["request_id"],
                "assignment_id": assignment_id, "reason": reason,
                "created_at": firestore.SERVER_TIMESTAMP,
            })
            return {**assignment, "id": assignment_id, "status": status, "release_reason": reason}

        return self._run(operation)

    def release_pending_assignments(self, uid: str, reason: str) -> list[dict[str, Any]]:
        released = []
        query = (
            self.client.collection("assignments")
            .where("responder_uid", "==", uid)
            .where("status", "==", "PENDING")
        )
        for snapshot in query.stream():
            result = self._release_pending(snapshot.id, reason, "CANCELLED")
            if result:
                released.append(result)
        return released

    def expire_stale_assignments(self) -> list[dict[str, Any]]:
        released = []
        query = (
            self.client.collection("assignments")
            .where("status", "==", "PENDING")
            .where("expires_at", "<=", _now())
            .limit(100)
        )
        for snapshot in query.stream():
            result = self._release_pending(snapshot.id, "assignment_ttl_elapsed", "EXPIRED")
            if result:
                released.append(result)
        return released

    def list_inbox(self, uid: str) -> list[dict[str, Any]]:
        output = []
        query = (
            self.client.collection("assignments")
            .where("responder_uid", "==", uid)
            .where("status", "in", sorted(ACTIVE_ASSIGNMENT_STATUSES))
        )
        for snapshot in query.stream():
            assignment = self._data(snapshot) or {}
            request = self.get_request(assignment["request_id"])
            if request:
                assignment["request"] = request
                output.append(assignment)
        return sorted(output, key=lambda item: str(item.get("created_at", "")))

    def list_open_requests(self, limit: int = 100) -> list[dict[str, Any]]:
        output = []
        query = self.client.collection("niyet_requests").where(
            "status", "in", ["OPEN", "UNMATCHED"]
        ).limit(limit)
        for snapshot in query.stream():
            value = self._data(snapshot)
            if value and not value.get("current_assignment_id"):
                output.append(value)
        return output

    def get_request(self, request_id: str) -> dict[str, Any] | None:
        return self._data(self.client.collection("niyet_requests").document(request_id).get())

    def get_assignment(self, assignment_id: str) -> dict[str, Any] | None:
        return self._data(self.client.collection("assignments").document(assignment_id).get())


class NiyetService:
    def __init__(self, repository: NiyetRepository) -> None:
        self.repository = repository

    def sync_user(self, actor: AuthenticatedUser) -> dict[str, Any]:
        return self.repository.upsert_user(actor)

    def update_responder_profile(self, actor: AuthenticatedUser, values: dict[str, Any]) -> dict[str, Any]:
        topics = self._string_list(values.get("topics"), "topics")
        languages = self._string_list(values.get("languages", ["en"]), "languages")
        if not isinstance(values.get("willing", False), bool) or not isinstance(values.get("active", True), bool):
            raise DomainError("invalid_profile_state", 400)
        try:
            capacity_total = int(values.get("capacity_total", 1))
        except (TypeError, ValueError) as exc:
            raise DomainError("invalid_capacity", 400) from exc
        if not 1 <= capacity_total <= 100:
            raise DomainError("invalid_capacity", 400)
        try:
            quality_threshold = float(values.get("quality_threshold", 0.0))
        except (TypeError, ValueError) as exc:
            raise DomainError("invalid_quality_threshold") from exc
        if not math.isfinite(quality_threshold) or not 0.0 <= quality_threshold <= 1.0:
            raise DomainError("invalid_quality_threshold")
        willing_intents = self._string_list(
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
            "active": bool(values.get("active", True)),
            "capacity_total": capacity_total,
            "quality_threshold": quality_threshold,
        }
        profile = self.repository.upsert_profile(actor.uid, payload)
        if not profile["willing"] or not profile["active"] or profile.get("paused"):
            released = self.repository.release_pending_assignments(actor.uid, "profile_unavailable")
            self._reallocate_released(released)
            profile = self.repository.get_profile(actor.uid) or profile
        else:
            self._allocate_open_requests()
        return profile

    @staticmethod
    def _string_list(value: Any, field: str) -> list[str]:
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise DomainError(f"invalid_{field}")
        output = list(dict.fromkeys(item.strip().lower() for item in value if item.strip()))
        if not output or len(output) > 20 or any(len(item) > 80 for item in output):
            raise DomainError(f"invalid_{field}")
        return output

    def get_responder_profile(self, actor: AuthenticatedUser) -> dict[str, Any]:
        profile = self.repository.get_profile(actor.uid)
        if profile is None:
            raise DomainError("responder_profile_not_found", 404)
        return profile

    def create_request(
        self,
        actor: AuthenticatedUser,
        *,
        text: str,
        intent: str | None = None,
        language: str | None = None,
        idempotency_key: str | None = None,
        metadata: dict[str, Any] | None = None,
        untrusted_author_uid: str | None = None,
    ) -> dict[str, Any]:
        del untrusted_author_uid
        clean_text = text.strip() if isinstance(text, str) else ""
        if not clean_text or len(clean_text) > 1200:
            raise DomainError("invalid_request_text")
        # Intent is server-derived. Client intent is intentionally not trusted as
        # the routing label; explicit user activation can still request a human even
        # when the response-needed model would not auto-route the text.
        del intent
        try:
            analysis = get_text_analyzer().analyze(clean_text, language_hint=language)
        except ValueError as exc:
            raise DomainError(str(exc)) from exc
        clean_intent = analysis.intent
        clean_key = idempotency_key.strip() if isinstance(idempotency_key, str) else _id("idem")
        if not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", clean_key):
            raise DomainError("invalid_idempotency_key")
        self._expire_stale()
        request_metadata = dict(metadata or {})
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
        assignment = self._allocate(request)
        refreshed = self.repository.get_request(request["id"]) or request
        if assignment:
            refreshed["assignment"] = assignment
        return refreshed

    def _allocate(
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

    def list_inbox(self, actor: AuthenticatedUser) -> list[dict[str, Any]]:
        if self.repository.get_profile(actor.uid) is None:
            raise DomainError("responder_profile_not_found", 404)
        self._expire_stale()
        return self.repository.list_inbox(actor.uid)

    def accept(self, actor: AuthenticatedUser, assignment_id: str) -> dict[str, Any]:
        self._expire_stale()
        try:
            return self.repository.accept(actor.uid, assignment_id)
        except DomainError as exc:
            if exc.code != "assignment_expired":
                raise
            self._expire_stale()
            raise DomainError("stale_assignment", 409) from exc

    def skip(self, actor: AuthenticatedUser, assignment_id: str) -> dict[str, Any]:
        self._expire_stale()
        try:
            assignment = self.repository.skip(actor.uid, assignment_id)
        except DomainError as exc:
            if exc.code != "assignment_expired":
                raise
            self._expire_stale()
            raise DomainError("stale_assignment", 409) from exc
        request = self.repository.get_request(assignment["request_id"])
        if request:
            replacement = self._allocate(
                request,
                reallocated_from_assignment_id=assignment_id,
            )
            if replacement:
                assignment["reallocated_assignment_id"] = replacement["id"]
        return assignment

    def answer(self, actor: AuthenticatedUser, assignment_id: str, answer: str) -> dict[str, Any]:
        clean_answer = answer.strip() if isinstance(answer, str) else ""
        if not clean_answer or len(clean_answer) > 4000:
            raise DomainError("invalid_answer")
        assignment = self.repository.answer(actor.uid, assignment_id, clean_answer)
        self._allocate_open_requests()
        return assignment

    def get_author_request(self, actor: AuthenticatedUser, request_id: str) -> dict[str, Any]:
        self._expire_stale()
        request = self.repository.get_request(request_id)
        if request is None:
            raise DomainError("request_not_found", 404)
        if request.get("author_uid") != actor.uid:
            raise DomainError("permission_denied", 403)
        assignment_id = request.get("current_assignment_id")
        if assignment_id:
            assignment = self.repository.get_assignment(assignment_id)
            if assignment:
                responder = self.repository.get_user(assignment["responder_uid"]) or {}
                request["assigned_responder"] = {
                    "id": assignment["responder_uid"],
                    "uid": assignment["responder_uid"],
                    "name": responder.get("display_name") or responder.get("email") or "Responder",
                    "assignment_id": assignment_id,
                    "status": assignment.get("status"),
                    "reason": assignment.get("match_metadata", {}).get("reason", []),
                }
        return request

    def pause(self, actor: AuthenticatedUser) -> dict[str, Any]:
        profile = self.repository.set_paused(actor.uid, True)
        released = self.repository.release_pending_assignments(actor.uid, "responder_paused")
        self._reallocate_released(released)
        return self.repository.get_profile(actor.uid) or profile

    def resume(self, actor: AuthenticatedUser) -> dict[str, Any]:
        profile = self.repository.set_paused(actor.uid, False)
        self._allocate_open_requests()
        return self.repository.get_profile(actor.uid) or profile

    def _reallocate_released(self, released: list[dict[str, Any]]) -> None:
        if not released:
            return
        sources = {
            assignment["request_id"]: assignment["id"]
            for assignment in released
        }
        self._allocate_window(reallocation_sources=sources)

    def _expire_stale(self) -> None:
        self._reallocate_released(self.repository.expire_stale_assignments())

    def _allocate_open_requests(self) -> None:
        self._allocate_window()
