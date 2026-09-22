"""Control plane: auth/RBAC, catalogue, sessions, scoring, audit. No Docker socket here."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .db import Base, SessionLocal, engine
from .models import User  # noqa: F401  (register tables)
from .models import Team, Membership, Lab, Session, Submission, Competition, Enrollment, Audit  # noqa: F401
from .routers import router
from .seed import seed_labs

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_labs(db, find_labs_root())
    finally:
        db.close()
    yield

def find_labs_root() -> str:
    env = os.environ.get("LABS_ROOT", "")
    if env and os.path.exists(env):
        return env
    cur = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    for _ in range(6):
        if os.path.exists(os.path.join(cur, "labs", "kingaweb-native")):
            return os.path.join(cur, "labs")
        cur = os.path.dirname(cur)
    return os.path.join(os.getcwd(), "labs")

app = FastAPI(title="KingaWeb Security Lab API", version="0.2.0", lifespan=lifespan)
app.include_router(router)

@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "api"}
