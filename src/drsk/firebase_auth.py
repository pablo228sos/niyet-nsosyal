from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .firebase_backend import verify_firebase_token


@dataclass(frozen=True)
class AuthenticatedUser:
    uid: str
    email: str | None
    display_name: str | None
    photo_url: str | None
    provider_ids: tuple[str, ...]
    claims: Mapping[str, Any]


class AuthError(RuntimeError):
    def __init__(self, code: str, status: int = 401) -> None:
        super().__init__(code)
        self.code = code
        self.status = status


def _provider_ids(claims: Mapping[str, Any]) -> tuple[str, ...]:
    firebase = claims.get("firebase")
    if not isinstance(firebase, Mapping):
        return ()
    providers: list[str] = []
    sign_in_provider = firebase.get("sign_in_provider")
    if isinstance(sign_in_provider, str) and sign_in_provider:
        providers.append(sign_in_provider)
    identities = firebase.get("identities")
    if isinstance(identities, Mapping):
        providers.extend(str(value) for value in identities if value)
    return tuple(dict.fromkeys(providers))


def authenticate_authorization_header(
    authorization: str | None,
    verifier: Callable[[str], Mapping[str, Any]] = verify_firebase_token,
) -> AuthenticatedUser:
    if not authorization:
        raise AuthError("auth_token_missing")
    scheme, separator, token = authorization.strip().partition(" ")
    if not separator or scheme.lower() != "bearer" or not token.strip():
        raise AuthError("auth_token_malformed")
    try:
        claims = verifier(token.strip())
    except Exception as exc:
        raise AuthError("auth_token_invalid") from exc
    uid = claims.get("uid") or claims.get("sub")
    if not isinstance(uid, str) or not uid:
        raise AuthError("auth_token_invalid")
    return AuthenticatedUser(
        uid=uid,
        email=claims.get("email") if isinstance(claims.get("email"), str) else None,
        display_name=claims.get("name") if isinstance(claims.get("name"), str) else None,
        photo_url=claims.get("picture") if isinstance(claims.get("picture"), str) else None,
        provider_ids=_provider_ids(claims),
        claims=claims,
    )
