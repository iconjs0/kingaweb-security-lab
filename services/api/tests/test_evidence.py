"""Evidence: findings validation, notes roundtrip, report export, isolation."""
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
FULL = {k: f"substantive {k} content here" for k in
        ["title", "description", "evidence", "impact", "cwe", "remediation", "retest"]}

def token(email):
    return c.post("/v1/auth/login", json={"email": email}).json()["token"]

def auth(t):
    return {"Authorization": f"Bearer {t}"}

def test_finding_validation_and_crud():
    t = token("learner@lab.dev")
    sid = c.post("/v1/sessions", json={"lab": "mpesa-bola-01@0.1.0"}, headers=auth(t)).json()["id"]
    assert c.post(f"/v1/sessions/{sid}/findings", json={"title": "x"}, headers=auth(t)).status_code == 422
    thin = dict(FULL, evidence="short")
    assert c.post(f"/v1/sessions/{sid}/findings", json=thin, headers=auth(t)).status_code == 422
    assert c.post(f"/v1/sessions/{sid}/findings", json=dict(FULL, severity="extreme"), headers=auth(t)).status_code == 422
    f = c.post(f"/v1/sessions/{sid}/findings", json=FULL, headers=auth(t)).json()
    assert f["id"] and f["status"] == "draft"
    assert len(c.get(f"/v1/sessions/{sid}/findings", headers=auth(t)).json()) == 1
    assert c.delete(f"/v1/sessions/{sid}/findings/{f['id']}", headers=auth(t)).json() == {"deleted": f["id"]}
    assert c.get(f"/v1/sessions/{sid}/findings", headers=auth(t)).json() == []
    c.delete(f"/v1/sessions/{sid}", headers=auth(t))

def test_notes_roundtrip_and_isolation():
    a, b = token("learner@lab.dev"), token("instructor@lab.dev")
    sid = c.post("/v1/sessions", json={"lab": "mpesa-bola-01@0.1.0"}, headers=auth(a)).json()["id"]
    assert c.put(f"/v1/sessions/{sid}/notes", json={"body": "BOLA at account param"}, headers=auth(a)).json()["saved"] > 0
    assert c.get(f"/v1/sessions/{sid}/notes", headers=auth(a)).json()["body"] == "BOLA at account param"
    assert c.get(f"/v1/sessions/{sid}/notes", headers=auth(b)).status_code == 403
    assert c.post(f"/v1/sessions/{sid}/findings", json=FULL, headers=auth(b)).status_code == 403
    c.delete(f"/v1/sessions/{sid}", headers=auth(a))

def test_report_exports():
    t = token("learner@lab.dev")
    sid = c.post("/v1/sessions", json={"lab": "mpesa-bola-01@0.1.0"}, headers=auth(t)).json()["id"]
    c.post(f"/v1/sessions/{sid}/findings", json=FULL, headers=auth(t))
    c.put(f"/v1/sessions/{sid}/notes", json={"body": "report notes"}, headers=auth(t))
    j = c.get(f"/v1/sessions/{sid}/report", headers=auth(t)).json()
    assert j["lab"] == "mpesa-bola-01@0.1.0" and len(j["findings"]) == 1 and j["notes"] == "report notes"
    h = c.get(f"/v1/sessions/{sid}/report.html", headers=auth(t))
    assert h.status_code == 200 and "text/html" in h.headers["content-type"]
    assert "mpesa-bola-01" in h.text and "substantive description content here" in h.text
    c.delete(f"/v1/sessions/{sid}", headers=auth(t))
