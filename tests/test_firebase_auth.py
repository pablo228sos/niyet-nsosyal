from __future__ import annotations

import pytest

from drsk.firebase_auth import AuthError, authenticate_authorization_header


def test_missing_bearer_token_is_rejected() -> None:
    with pytest.raises(AuthError) as caught:
        authenticate_authorization_header(None, lambda token: {})
    assert caught.value.code == "auth_token_missing"
    assert caught.value.status == 401


def test_invalid_bearer_token_is_rejected() -> None:
    def reject(_: str) -> dict:
        raise ValueError("expired")

    with pytest.raises(AuthError) as caught:
        authenticate_authorization_header("Bearer expired", reject)
    assert caught.value.code == "auth_token_invalid"
    assert caught.value.status == 401


def test_verified_identity_comes_only_from_token_claims() -> None:
    actor = authenticate_authorization_header(
        "Bearer signed-token",
        lambda token: {
            "uid": "verified-user",
            "email": "person@example.test",
            "name": "Verified Person",
            "picture": "https://example.test/photo.png",
            "firebase": {"sign_in_provider": "google.com"},
        },
    )

    assert actor.uid == "verified-user"
    assert actor.provider_ids == ("google.com",)
