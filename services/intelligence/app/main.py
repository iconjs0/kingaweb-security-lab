"""Intel API: priority-ordered vulns, severity history, human review queue.
Sync is explicit (admin trigger + daily scheduler) — feeds never deploy labs."""
import hmac
import os
import threading
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from . import db, sync

bearer = HTTPBearer(auto_error=False)

def authed(creds=Depends(bearer)):
    want = os.environ.get("INTEL_TOKEN", "dev-intel-token")
    if not creds or not hmac.compare_digest(creds.credentials, want):
        raise HTTPException(401, "bad intel token")
    return True

def authed_write(creds=Depends(bearer)):
    want = os.environ.get("INTEL_TOKEN", "dev-intel-token")
    admin = {"instructor", "platform-admin"}
    _ = admin  # roles enforced by control plane in prod; dev token gates here
    if not creds or not hmac.compare_digest(creds.credentials, want):
        raise HTTPException(401, "bad intel token")
    return True

def scheduler() -> None:
    interval = int(os.environ.get("SYNC_INTERVAL_HOURS", "24") or 24) * 3600
    while True:
        time.sleep(interval)
        try:
            sync.sync_all()
        except Exception:
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    if os.environ.get("INTEL_AUTOSYNC", "false").lower() == "true":
        threading.Thread(target=lambda: sync.sync_all(), daemon=True).start()
    threading.Thread(target=scheduler, daemon=True).start()
    yield

app = FastAPI(title="KingaWeb Intel", version="0.1.0", lifespan=lifespan)

class ReviewIn(BaseModel):
    decision: str  # approved | dismissed

@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "intelligence"}

@app.post("/v1/intel/sync")
def trigger(_=Depends(authed_write)):
    return sync.sync_all()

@app.get("/v1/intel/sync/runs")
def runs(_=Depends(authed)):
    c = db.conn()
    try:
        return [dict(r) for r in c.execute(
            "SELECT feed,started,finished,records,error FROM sync_runs ORDER BY id DESC LIMIT 20").fetchall()]
    finally:
        c.close()

@app.get("/v1/intel/vulns")
def vulns(q: str = "", kev_only: bool = False, limit: int = 50, _=Depends(authed)):
    c = db.conn()
    try:
        sql = "SELECT cve,published,modified,cvss,severity,kev,epss,priority,labs FROM vulns"
        args: list = []
        wh = []
        if q:
            wh.append("(cve LIKE ? OR description LIKE ?)")
            args += [f"%{q}%", f"%{q}%"]
        if kev_only:
            wh.append("kev=1")
        if wh:
            sql += " WHERE " + " AND ".join(wh)
        sql += " ORDER BY priority DESC LIMIT ?"
        args.append(max(1, min(limit, 200)))
        return [dict(r) for r in c.execute(sql, args).fetchall()]
    finally:
        c.close()

@app.get("/v1/intel/vulns/{cve}")
def detail(cve: str, _=Depends(authed)):
    c = db.conn()
    try:
        row = c.execute("SELECT * FROM vulns WHERE cve=?", (cve,)).fetchone()
        if not row:
            raise HTTPException(404, "unknown cve")
        hist = [dict(r) for r in c.execute(
            "SELECT cvss,severity,reason,at FROM severity_history WHERE cve=? ORDER BY id", (cve,)).fetchall()]
        return {**dict(row), "history": hist}
    finally:
        c.close()

@app.get("/v1/intel/review")
def review(status: str = "open", _=Depends(authed)):
    c = db.conn()
    try:
        return [dict(r) for r in c.execute(
            "SELECT id,cve,reason,status,created_at FROM review_queue WHERE status=? ORDER BY id DESC LIMIT 100",
            (status,)).fetchall()]
    finally:
        c.close()

@app.post("/v1/intel/review/{rid}")
def decide(rid: int, body: ReviewIn, _=Depends(authed_write)):
    if body.decision not in ("approved", "dismissed"):
        raise HTTPException(422, "decision must be approved|dismissed")
    c = db.conn()
    try:
        cur = c.execute("UPDATE review_queue SET status=? WHERE id=?", (body.decision, rid))
        c.commit()
        if not cur.rowcount:
            raise HTTPException(404, "review item not found")
        return {"id": rid, "status": body.decision}
    finally:
        c.close()

@app.get("/v1/intel/cwe/{cid}")
def cwe(cid: str, _=Depends(authed)):
    global _cwe_cache
    try:
        _cwe_cache
    except NameError:
        _cwe_cache = {"at": 0.0, "names": {}}
    import time as _t
    if _t.time() - _cwe_cache["at"] > 86400:
        _cwe_cache = {"at": _t.time(), "names": sync.cwe_names()}
    if cid not in _cwe_cache["names"]:
        raise HTTPException(404, "unknown cwe (sync may still be running)")
    return {"id": cid, "name": _cwe_cache["names"][cid]}
