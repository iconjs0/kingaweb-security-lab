"""Teams classroom: assignments, cohort progress, verifiable certificates."""
import os
os.environ.setdefault("FLAG_HMAC_SECRET", "test-secret-32-bytes-minimum-ok")
os.environ.setdefault("ALLOW_DEV_MINT", "true")

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

def test_assignment_flow_and_cohort():
    inst, learn = token("instructor@lab.dev"), token("learner@lab.dev")
    tid = c.post("/v1/teams", json={"name": "class"}, headers=auth(inst)).json()["id"]
    assert c.post(f"/v1/teams/{tid}/join", headers=auth(learn)).status_code == 200
    # learner cannot create assignments
    assert c.post("/v1/assignments", json={"team_id": tid, "title": "x", "labs": []},
                  headers=auth(learn)).status_code == 403
    a = c.post("/v1/assignments", json={"team_id": tid, "title": "week1",
                                        "labs": ["web-http-01@0.1.0"]}, headers=auth(inst)).json()
    assert c.post("/v1/assignments", json={"team_id": tid, "title": "bad",
                                           "labs": ["nope"]}, headers=auth(inst)).status_code == 422
    sid = c.post("/v1/sessions", json={"lab": "web-http-01@0.1.0"}, headers=auth(learn)).json()["id"]
    # wrong lab rejected
    sid2 = c.post("/v1/sessions", json={"lab": "web-cookies-01@0.1.0"}, headers=auth(learn)).json()["id"]
    assert c.post(f"/v1/assignments/{a['id']}/submit", json={"session_id": sid2},
                  headers=auth(learn)).status_code == 422
    assert c.post(f"/v1/assignments/{a['id']}/submit", json={"session_id": sid},
                  headers=auth(learn)).json()["session"] == sid
    p = c.get(f"/v1/teams/{tid}/progress", headers=auth(inst)).json()
    assert any(m["user"] == "u-learner" for m in p["cohort"])
    d = c.get(f"/v1/teams/{tid}", headers=auth(learn)).json()
    assert any(x["id"] == a["id"] for x in d["assignments"])
    c.delete(f"/v1/sessions/{sid}", headers=auth(learn))
    c.delete(f"/v1/sessions/{sid2}", headers=auth(learn))

def test_certificates_verified():
    inst, learn = token("instructor@lab.dev"), token("learner@lab.dev")
    assert c.get("/v1/certificates/KW-CERT-NOPE").status_code == 404
    # no solves for a fresh identity -> 422 (author logs in but never solves)
    token("author@lab.dev")
    assert c.post("/v1/certificates/issue", json={"user_email": "author@lab.dev"},
                  headers=auth(inst)).status_code == 422
    cert = c.post("/v1/certificates/issue", json={"user_email": "learner@lab.dev"},
                  headers=auth(inst)).json()
    assert cert["code"].startswith("KW-CERT-")
    pub = c.get(f"/v1/certificates/{cert['code']}")
    assert pub.status_code == 200 and pub.json()["learner"] == "learner@lab.dev"
    # learner cannot issue
    assert c.post("/v1/certificates/issue", json={"user_email": "learner@lab.dev"},
                  headers=auth(learn)).status_code == 403
