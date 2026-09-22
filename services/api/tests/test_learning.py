"""Learning modes, hint economy, finalize locks. Shares suite DB with test_api."""
import os
os.environ.setdefault("FLAG_HMAC_SECRET", "test-secret-32-bytes-minimum-ok")
os.environ.setdefault("ALLOW_DEV_MINT", "true")

from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, SessionLocal, engine
from app.seed import seed_labs

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

def launch(t, lab="mpesa-bola-01@0.1.0", mode="guided"):
    r = c.post("/v1/sessions", json={"lab": lab, "mode": mode}, headers=auth(t))
    assert r.status_code == 201, r.text
    return r.json()["id"]

def test_guided_hints_sequential_and_priced():
    t = token("learner@lab.dev")
    sid = launch(t)
    h1 = c.post(f"/v1/sessions/{sid}/hints/unlock", headers=auth(t)).json()
    assert h1["level"] == 1 and h1["cost"] == 5 and "account" in h1["text"].lower()
    h2 = c.post(f"/v1/sessions/{sid}/hints/unlock", headers=auth(t)).json()
    assert h2["level"] == 2 and h2["cost"] == 15
    assert c.post(f"/v1/sessions/{sid}/hints/unlock", headers=auth(t)).status_code == 404

def test_hint_cost_deducted_from_score():
    t = token("learner@lab.dev")
    plain, hinted = launch(t), launch(t)
    obj = "read-foreign-balance"
    f1 = c.post("/v1/dev/mint", params={"session_id": plain, "objective_id": obj}, headers=auth(t)).json()["flag"]
    p1 = c.post(f"/v1/sessions/{plain}/submissions", json={"objective_id": obj, "flag": f1}, headers=auth(t)).json()["points"]
    c.post(f"/v1/sessions/{hinted}/hints/unlock", headers=auth(t))
    c.post(f"/v1/sessions/{hinted}/hints/unlock", headers=auth(t))
    f2 = c.post("/v1/dev/mint", params={"session_id": hinted, "objective_id": obj}, headers=auth(t)).json()["flag"]
    r2 = c.post(f"/v1/sessions/{hinted}/submissions", json={"objective_id": obj, "flag": f2}, headers=auth(t)).json()
    assert r2["hint_cost"] == 20
    assert r2["points"] == p1 - 20 or r2["points"] < p1  # decay may differ; cost must bite

def test_assessment_cap_finalize_lock_and_ttl():
    t = token("learner@lab.dev")
    sid = launch(t, mode="assessment")
    s = c.get(f"/v1/sessions/{sid}", headers=auth(t)).json()
    assert s["mode"] == "assessment"
    exp = datetime.fromisoformat(s["expires_at"])
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    assert (exp - datetime.now(timezone.utc)).total_seconds() <= 31 * 60
    assert c.post(f"/v1/sessions/{sid}/hints/unlock", headers=auth(t)).status_code == 200
    assert c.post(f"/v1/sessions/{sid}/hints/unlock", headers=auth(t)).status_code == 403
    fin = c.post(f"/v1/sessions/{sid}/finalize", headers=auth(t)).json()
    assert fin["immutable"] is True and fin["time_bonus"] >= 0
    assert c.post(f"/v1/sessions/{sid}/finalize", headers=auth(t)).status_code == 409
    flag = c.post("/v1/dev/mint", params={"session_id": sid, "objective_id": "read-foreign-balance"}, headers=auth(t)).json()["flag"]
    sub = c.post(f"/v1/sessions/{sid}/submissions", json={"objective_id": "read-foreign-balance", "flag": flag}, headers=auth(t))
    assert sub.status_code == 409
    assert c.post(f"/v1/sessions/{sid}/reset", headers=auth(t)).status_code == 409

def test_invalid_mode_and_demo_free():
    t = token("learner@lab.dev")
    assert c.post("/v1/sessions", json={"lab": "mpesa-bola-01@0.1.0", "mode": "speedrun"}, headers=auth(t)).status_code == 422
    sid = launch(t, mode="demo")
    h = c.post(f"/v1/sessions/{sid}/hints/unlock", headers=auth(t)).json()
    assert h["cost"] == 0 and h["free"] is True
