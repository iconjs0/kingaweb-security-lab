"""i18n: ?lang=sw overrides, en/unknown fall back, structure validated by manifest checks."""
import os
os.environ.setdefault("FLAG_HMAC_SECRET", "test-secret-32-bytes-minimum-ok")
os.environ.setdefault("ALLOW_DEV_MINT", "true")
_DB = "/tmp/opencode-test-lab.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB}"

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

def test_sw_override_and_fallback():
    t = token("learner@lab.dev")
    en = c.get("/v1/labs/web-http-01", headers=auth(t)).json()
    assert en["lang"] == "en" and "Override" in en["title"]
    sw = c.get("/v1/labs/web-http-01?lang=sw", headers=auth(t)).json()
    assert sw["lang"] == "sw" and "Undani" in sw["title"]
    assert sw["objectives"][0]["id"] == "override-note"  # ids stable across langs
    assert [h["level"] for h in sw["hint_levels"]] == [1, 2]
    assert c.get("/v1/labs/web-http-01?lang=fr", headers=auth(t)).json()["lang"] == "en"
    mpesa = c.get("/v1/labs/mpesa-bola-01?lang=sw", headers=auth(t)).json()
    assert mpesa["lang"] == "sw" and "Jaribio" in mpesa["title"]
    plain = c.get("/v1/labs/web-cookies-01", headers=auth(t)).json()
    assert plain["hint_levels"] == [{"level": 1, "cost": 5}, {"level": 2, "cost": 15}]
