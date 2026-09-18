from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one replacement anchor, found {count}")
    return text.replace(old, new, 1)


path = Path("src/drsk/niyet_persistence.py")
text = path.read_text(encoding="utf-8")

text = replace_once(
    text,
    '''            post = self.posts.get(request["post_id"])
            if post is not None:
                post.update(resolution=resolution, updated_at=now)
            self._event("ANSWERED", actor_uid=uid, request_id=request["id"], assignment_id=assignment_id)
            return copy.deepcopy(assignment)
''',
    '''            post = self.posts.get(request["post_id"])
            if post is not None:
                post.update(resolution=resolution, updated_at=now)
            profile = self.profiles.get(uid)
            if profile is not None:
                profile["capacity_remaining"] = min(
                    int(profile["capacity_total"]), int(profile["capacity_remaining"]) + 1
                )
                profile["updated_at"] = now
            self._event("ANSWERED", actor_uid=uid, request_id=request["id"], assignment_id=assignment_id)
            return copy.deepcopy(assignment)
''',
    "memory answer capacity release",
)

text = replace_once(
    text,
    '''            post_ref = self.client.collection("posts").document(request["post_id"])
            resolution = {
''',
    '''            post_ref = self.client.collection("posts").document(request["post_id"])
            profile_ref = self.client.collection("responder_profiles").document(uid)
            profile_snapshot = profile_ref.get(transaction=transaction)
            if not profile_snapshot.exists:
                raise DomainError("responder_profile_not_found", 404)
            profile = profile_snapshot.to_dict() or {}
            resolution = {
''',
    "firestore answer profile read",
)

text = replace_once(
    text,
    '''            transaction.update(post_ref, {
                "resolution": resolution,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            transaction.set(event_ref, {
''',
    '''            transaction.update(post_ref, {
                "resolution": resolution,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            capacity_total = int(profile.get("capacity_total", 0))
            capacity_remaining = int(profile.get("capacity_remaining", 0))
            transaction.update(profile_ref, {
                "capacity_remaining": min(capacity_total, capacity_remaining + 1),
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            transaction.set(event_ref, {
''',
    "firestore answer capacity release",
)

text = replace_once(
    text,
    '''        if not clean_answer or len(clean_answer) > 4000:
            raise DomainError("invalid_answer")
        return self.repository.answer(actor.uid, assignment_id, clean_answer)
''',
    '''        if not clean_answer or len(clean_answer) > 4000:
            raise DomainError("invalid_answer")
        assignment = self.repository.answer(actor.uid, assignment_id, clean_answer)
        self._allocate_open_requests()
        return assignment
''',
    "service answer reallocation",
)

path.write_text(text, encoding="utf-8")

test_path = Path("tests/test_niyet_persistence.py")
tests = test_path.read_text(encoding="utf-8")
tests = replace_once(
    tests,
    '''    with pytest.raises(DomainError, match="permission_denied"):
        service.answer(actor("intruder"), assignment_id, "Unsafe answer")

    first = service.answer(actor("responder"), assignment_id, "Use a transaction.")
    duplicate = service.answer(actor("responder"), assignment_id, "Use a transaction.")
    assert first["status"] == duplicate["status"] == "ANSWERED"
''',
    '''    with pytest.raises(DomainError, match="permission_denied"):
        service.answer(actor("intruder"), assignment_id, "Unsafe answer")

    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 1
    first = service.answer(actor("responder"), assignment_id, "Use a transaction.")
    duplicate = service.answer(actor("responder"), assignment_id, "Use a transaction.")
    assert first["status"] == duplicate["status"] == "ANSWERED"
    assert service.get_responder_profile(actor("responder"))["capacity_remaining"] == 2
''',
    "capacity release regression test",
)
test_path.write_text(tests, encoding="utf-8")
