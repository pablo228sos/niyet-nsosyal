from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from typing import Any, Mapping


class FirebaseConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class FirebaseCredentials:
    project_id: str
    client_email: str
    private_key: str

    def certificate(self) -> dict[str, str]:
        return {
            "type": "service_account",
            "project_id": self.project_id,
            "client_email": self.client_email,
            "private_key": self.private_key,
            "token_uri": "https://oauth2.googleapis.com/token",
        }


def firebase_credentials_from_environment(
    environment: Mapping[str, str] | None = None,
) -> FirebaseCredentials:
    values = os.environ if environment is None else environment
    project_id = values.get("FIREBASE_PROJECT_ID", "").strip()
    client_email = values.get("FIREBASE_CLIENT_EMAIL", "").strip()
    private_key = values.get("FIREBASE_PRIVATE_KEY", "").strip().replace("\\n", "\n")
    present = (bool(project_id), bool(client_email), bool(private_key))
    if not any(present):
        raise FirebaseConfigurationError("firebase_configuration_missing")
    if not all(present):
        raise FirebaseConfigurationError("firebase_configuration_incomplete")
    return FirebaseCredentials(project_id, client_email, private_key)


_lock = threading.Lock()
_app: Any | None = None


def get_firebase_app() -> Any:
    global _app
    if _app is not None:
        return _app
    with _lock:
        if _app is not None:
            return _app
        import firebase_admin
        from firebase_admin import credentials

        emulator_project = os.getenv("FIREBASE_PROJECT_ID", "").strip()
        firestore_emulator = bool(os.getenv("FIRESTORE_EMULATOR_HOST", "").strip())
        auth_emulator = bool(os.getenv("FIREBASE_AUTH_EMULATOR_HOST", "").strip())
        if firestore_emulator != auth_emulator:
            raise FirebaseConfigurationError("firebase_emulator_configuration_incomplete")
        emulator_enabled = firestore_emulator and auth_emulator
        try:
            _app = firebase_admin.get_app()
        except ValueError:
            if emulator_enabled and emulator_project:
                _app = firebase_admin.initialize_app(options={"projectId": emulator_project})
            else:
                config = firebase_credentials_from_environment()
                _app = firebase_admin.initialize_app(
                    credentials.Certificate(config.certificate()),
                    {"projectId": config.project_id},
                )
        return _app


def get_firestore_client() -> Any:
    from firebase_admin import firestore

    return firestore.client(app=get_firebase_app())


def verify_firebase_token(token: str, *, check_revoked: bool = True) -> dict[str, Any]:
    from firebase_admin import auth

    return auth.verify_id_token(
        token,
        app=get_firebase_app(),
        check_revoked=check_revoked,
    )


def public_firebase_config(environment: Mapping[str, str] | None = None) -> dict[str, str]:
    values = os.environ if environment is None else environment
    mapping = {
        "apiKey": "FIREBASE_WEB_API_KEY",
        "authDomain": "FIREBASE_AUTH_DOMAIN",
        "projectId": "FIREBASE_PROJECT_ID",
        "storageBucket": "FIREBASE_STORAGE_BUCKET",
        "messagingSenderId": "FIREBASE_MESSAGING_SENDER_ID",
        "appId": "FIREBASE_APP_ID",
    }
    result = {
        output: values.get(source, "").strip()
        for output, source in mapping.items()
        if values.get(source, "").strip()
    }
    required = {"apiKey", "authDomain", "projectId", "appId"}
    if not required.issubset(result):
        raise FirebaseConfigurationError("firebase_web_configuration_incomplete")
    return result
