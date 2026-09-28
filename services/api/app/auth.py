"""Authentication boundary: local dev identities or verified production OIDC JWTs."""
import hashlib
import json
import os
import urllib.request
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session as DBSession
from .db import get_db
from .models import User

bearer = HTTPBearer(auto_error=False)

SEEDED = {
    "learner@lab.dev": "learner",
    "instructor@lab.dev": "instructor",
    "author@lab.dev": "content-author",
    "admin@lab.dev": "platform-admin",
}

def _ensure_user(db: DBSession, email: str, role: str) -> User:
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(id=f"u-{email.split('@')[0]}", email=email, role=role)
        db.add(u)
        db.commit()
        db.refresh(u)
    return u

def _dev_auth_enabled() -> bool:
    value = os.environ.get("ALLOW_DEV_AUTH", os.environ.get("ALLOW_DEV_MINT", "false"))
    return value.lower() == "true"

def login_dev(db: DBSession, email: str) -> str:
    if not _dev_auth_enabled():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "development login is disabled")
    role = SEEDED.get(email)
    if not role:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown dev identity")
    _ensure_user(db, email, role)
    return f"dev-{role}"

@lru_cache(maxsize=4)
def _jwks_client(issuer: str) -> jwt.PyJWKClient:
    with urllib.request.urlopen(f"{issuer}/.well-known/openid-configuration", timeout=5) as response:
        discovery = json.load(response)
    return jwt.PyJWKClient(discovery["jwks_uri"], cache_keys=True)

def _oidc_claims(token: str) -> dict:
    issuer = os.environ.get("OIDC_ISSUER_URL", "").rstrip("/")
    audience = os.environ.get("OIDC_AUDIENCE") or os.environ.get("OIDC_CLIENT_ID", "")
    if not issuer or not audience:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "OIDC is not configured")
    try:
        signing_key = _jwks_client(issuer).get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256", "ES256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid identity token") from exc

def _ensure_oidc_user(db: DBSession, claims: dict) -> User:
    subject = str(claims.get("sub", ""))
    if not subject:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "identity token has no subject")
    issuer = os.environ.get("OIDC_ISSUER_URL", "")
    user_id = "oidc-" + hashlib.sha256(f"{issuer}|{subject}".encode()).hexdigest()[:48]
    email = str(claims.get("email") or f"{user_id}@oidc.invalid")[:255]
    role_claim = os.environ.get("OIDC_ROLE_CLAIM", "kingaweb_role")
    requested_role = claims.get(role_claim, "learner")
    allowed_roles = {"learner", "instructor", "content-author", "platform-admin"}
    role = requested_role if requested_role in allowed_roles else "learner"
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email=email, role=role)
        db.add(user)
    else:
        user.email = email
        user.role = role
    db.commit()
    db.refresh(user)
    return user

def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: DBSession = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "authentication required")
    token = creds.credentials
    if token.startswith("dev-"):
        if not _dev_auth_enabled():
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "development tokens are disabled")
        role = token.removeprefix("dev-")
        email = next((e for e, r in SEEDED.items() if r == role), None)
        if not email:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown development role")
        return _ensure_user(db, email, role)
    return _ensure_oidc_user(db, _oidc_claims(token))

def require_roles(*roles: str):
    def check(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"requires role in {list(roles)}")
        return user
    return check
