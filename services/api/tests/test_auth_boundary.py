"""Production authentication must never accept local development identities."""
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import current_user, login_dev
from app.db import SessionLocal


def test_development_login_is_disabled_in_production(monkeypatch):
    monkeypatch.setenv("ALLOW_DEV_AUTH", "false")
    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as exc:
            login_dev(db, "admin@lab.dev")
        assert exc.value.status_code == 404
    finally:
        db.close()


def test_development_bearer_token_is_rejected_in_production(monkeypatch):
    monkeypatch.setenv("ALLOW_DEV_AUTH", "false")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dev-platform-admin")
    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as exc:
            current_user(credentials, db)
        assert exc.value.status_code == 401
    finally:
        db.close()


def test_oidc_configuration_is_required(monkeypatch):
    monkeypatch.setenv("ALLOW_DEV_AUTH", "false")
    monkeypatch.delenv("OIDC_ISSUER_URL", raising=False)
    monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
    monkeypatch.delenv("OIDC_CLIENT_ID", raising=False)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="not-a-development-token")
    db = SessionLocal()
    try:
        with pytest.raises(HTTPException) as exc:
            current_user(credentials, db)
        assert exc.value.status_code == 503
    finally:
        db.close()
