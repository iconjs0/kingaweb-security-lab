"""Contract + isolation tests: run with .venv/bin/pytest (ALLOW_DEV_MINT=true)."""
import os
os.environ.setdefault("FLAG_HMAC_SECRET", "test-secret-32-bytes-minimum-ok")
os.environ.setdefault("ALLOW_DEV_MINT", "true")
_DB = "/tmp/opencode-test-lab.db"
if os.path.exists(_DB):
    os.remove(_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB}"

from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, SessionLocal, engine
from app.seed import seed_labs

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_db = SessionLocal()
try:
    assert seed_labs(_db, os.path.join(REPO, "labs")) >= 2
finally:
    _db.close()
c = TestClient(app, raise_server_exceptions=False)

def token(email):
    r = c.post("/v1/auth/login", json={"email": email})
    assert r.status_code == 200, r.text
    return r.json()["token"]

def auth(t):
    return {"Authorization": f"Bearer {t}"}

def test_seed_and_catalogue():
    t = token("learner@lab.dev")
    r = c.get("/v1/labs", headers=auth(t))
    assert r.status_code == 200
    slugs = {l["slug"] for l in r.json()}
    assert {"web-idor-01", "mpesa-bola-01"} <= slugs

def test_session_isolation_and_idempotency():
    a, b = token("learner@lab.dev"), token("instructor@lab.dev")
    h = {"Idempotency-Key": "k-iso-1", **auth(a)}
    r1 = c.post("/v1/sessions", json={"lab": "web-idor-01@0.1.0"}, headers=h)
    assert r1.status_code == 201
    r2 = c.post("/v1/sessions", json={"lab": "web-idor-01@0.1.0"}, headers=h)
    assert r2.json().get("deduplicated") is True and r2.json()["id"] == r1.json()["id"]
    sid = r1.json()["id"]
    assert c.get(f"/v1/sessions/{sid}", headers=auth(b)).status_code == 403  # cross-user denied
    assert c.get(f"/v1/sessions/{sid}", headers=auth(a)).status_code == 200

def test_flag_roundtrip_and_ratelimit():
    t = token("learner@lab.dev")
    sid = c.post("/v1/sessions", json={"lab": "web-idor-01@0.1.0"}, headers=auth(t)).json()["id"]
    bad = c.post(f"/v1/sessions/{sid}/submissions",
                 json={"objective_id": "read-other-order", "flag": "KW{nope}"}, headers=auth(t))
    assert bad.json()["correct"] is False
    flag = c.post("/v1/dev/mint", params={"session_id": sid, "objective_id": "read-other-order"},
                  headers=auth(t)).json()["flag"]
    good = c.post(f"/v1/sessions/{sid}/submissions",
                  json={"objective_id": "read-other-order", "flag": flag, "remediation_done": True},
                  headers=auth(t))
    assert good.json()["correct"] is True and good.json()["points"] > 400
    p = c.get("/v1/progress", headers=auth(t)).json()
    assert p["solves"] >= 1

def test_console_allowlist_and_rbac():
    t = token("learner@lab.dev")
    sid = c.post("/v1/sessions", json={"lab": "web-idor-01@0.1.0"}, headers=auth(t)).json()["id"]
    evil = c.post(f"/v1/sessions/{sid}/requests",
                  json={"method": "GET", "host": "169.254.169.254", "path": "/"}, headers=auth(t))
    assert evil.status_code == 403  # SSRF host denied
    assert c.get("/v1/audit", headers=auth(t)).status_code == 403  # learners can't read audit
    admin = token("admin@lab.dev")
    assert c.get("/v1/audit", headers=auth(admin)).status_code == 200

def test_competition_rbac():
    learner = token("learner@lab.dev")
    assert c.post("/v1/competitions", json={"name": "x"}, headers=auth(learner)).status_code == 403
    inst = token("instructor@lab.dev")
    cid = c.post("/v1/competitions", json={"name": "friday"}, headers=auth(inst)).json()["id"]
    assert c.post(f"/v1/competitions/{cid}/join", headers=auth(learner)).status_code == 200
    assert c.get(f"/v1/competitions/{cid}/leaderboard", headers=auth(learner)).status_code == 200
