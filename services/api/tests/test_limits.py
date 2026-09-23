"""Edge guards: bursts 429, quotas enforced, headers present, metrics gated."""
import os
os.environ.setdefault("FLAG_HMAC_SECRET", "test-secret-32-bytes-minimum-ok")
os.environ.setdefault("ALLOW_DEV_MINT", "true")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, SessionLocal, engine
from app.models import Session, User
from app.seed import seed_labs
from app import limits

@pytest.fixture(autouse=True)
def _isolate():
    limits._buckets.clear()
    yield
    limits._buckets.clear()

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
Base.metadata.create_all(bind=engine)
_db = SessionLocal()
try:
    seed_labs(_db, os.path.join(REPO, "labs"))
finally:
    _db.close()
c = TestClient(app, raise_server_exceptions=False)

def token(email):
    return c.post("/v1/auth/login", json={"email": email}).json()["token"]

def auth(t):
    return {"Authorization": f"Bearer {t}"}

def test_login_burst_429_and_headers(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_LOGIN_PER_MIN", "20")
    for _ in range(25):
        c.post("/v1/auth/login", json={"email": "learner@lab.dev"})
    r = c.post("/v1/auth/login", json={"email": "learner@lab.dev"})
    assert r.status_code == 429
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors" in r.headers.get("Content-Security-Policy", "")
    assert "Strict-Transport-Security" not in r.headers  # no TLS locally
    limits._buckets.clear()

def test_session_quotas(monkeypatch):
    monkeypatch.setenv("MAX_ACTIVE_PER_USER", "2")
    # start from zero regardless of what earlier files left behind
    db = SessionLocal()
    try:
        me = db.query(User).filter(User.email == "instructor@lab.dev").first()
        if me:
            db.query(Session).filter(Session.owner_id == me.id,
                                     Session.status == "active").update({"status": "destroyed"})
            db.commit()
    finally:
        db.close()
    t = token("instructor@lab.dev")
    ids = []
    for _ in range(2):
        r = c.post("/v1/sessions", json={"lab": "mpesa-bola-01@0.1.0"}, headers=auth(t))
        assert r.status_code == 201
        ids.append(r.json()["id"])
    over = c.post("/v1/sessions", json={"lab": "mpesa-bola-01@0.1.0"}, headers=auth(t))
    assert over.status_code == 429
    for sid in ids:
        c.delete(f"/v1/sessions/{sid}", headers=auth(t))
    ok = c.post("/v1/sessions", json={"lab": "mpesa-bola-01@0.1.0"}, headers=auth(t))
    assert ok.status_code == 201
    c.delete(f"/v1/sessions/{ok.json()['id']}", headers=auth(t))
    limits._buckets.clear()

def test_metrics_admin_only():
    t, admin = token("learner@lab.dev"), token("admin@lab.dev")
    assert c.get("/v1/metrics", headers=auth(t)).status_code == 403
    m = c.get("/v1/metrics", headers=auth(admin)).json()
    assert m["requests"] > 0 and "active_sessions" in m
