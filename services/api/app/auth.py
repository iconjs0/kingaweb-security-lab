"""Auth: seeded dev tokens (Authorization: Bearer dev-<role>), OIDC stubbed for prod.
Login returns a dev token for known seeded identities. Never accepts caller-supplied roles."""
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

def login_dev(db: DBSession, email: str) -> str:
    role = SEEDED.get(email)
    if not role:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown dev identity")
    _ensure_user(db, email, role)
    return f"dev-{role}"

def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: DBSession = Depends(get_db),
) -> User:
    if not creds or not creds.credentials.startswith("dev-"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing or invalid bearer token (dev: dev-learner|dev-instructor|dev-admin)")
    role = creds.credentials.removeprefix("dev-")
    email = next((e for e, r in SEEDED.items() if r == role), None)
    if not email:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown dev role")
    return _ensure_user(db, email, role)

def require_roles(*roles: str):
    def check(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"requires role in {list(roles)}")
        return user
    return check
