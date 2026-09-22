"""Orchestrator: sole Docker socket holder. Bearer-gated, narrow schema."""
import os
import threading
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from . import dockerx, store
from . import relay as relay_mod
from .policy import PolicyError, check_manifest, load_manifest, resolve_image

def token() -> str:
    t = os.environ.get("ORCHESTRATOR_TOKEN", "")
    if len(t) < 8:
        raise RuntimeError("ORCHESTRATOR_TOKEN missing or too short")
    return t

def authed(creds: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False))):
    import hmac as _hm
    if not creds or not _hm.compare_digest(creds.credentials, token()):
        raise HTTPException(401, "bad orchestrator token")
    return True

def reaper() -> None:
    while True:
        time.sleep(15)
        try:
            cli = dockerx.client()
        except Exception:
            continue
        for sid in store.expired():
            try:
                dockerx.destroy_session(cli, sid)
            finally:
                store.drop(sid, "expired")
        try:
            dockerx.reconcile(cli, store.live())
        except Exception:
            pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        dockerx.reconcile(dockerx.client(), store.live())  # post-crash sweep
    except Exception:
        pass
    th = threading.Thread(target=reaper, daemon=True)
    th.start()
    yield

app = FastAPI(title="KingaWeb Orchestrator", version="0.1.0", lifespan=lifespan)

class ProvisionIn(BaseModel):
    session_id: str
    lab_slug: str
    lab_version: str
    ttl_minutes: int = 60

@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "orchestrator"}

@app.post("/v1/orch/sessions", status_code=201)
def provision(body: ProvisionIn, _=Depends(authed)):
    try:
        manifest = load_manifest(body.lab_slug, body.lab_version)
        check_manifest(manifest)
    except PolicyError as e:
        raise HTTPException(403, f"manifest rejected: {e}")
    ttl = min(body.ttl_minutes, int(manifest.get("session", {}).get("ttlMinutes", 60)))
    targets = []
    try:
        for t in manifest.get("targets", []):
            runtime, pinned, dev = resolve_image(t["image"])
            targets.append({"name": t["name"], "runtime_image": runtime,
                            "ports": t.get("ports", []), "health": t.get("healthcheck", {}),
                            "resources": t.get("resources", {}), "dev_digest": dev})
    except PolicyError as e:
        raise HTTPException(403, f"image rejected: {e}")
    try:
        cli = dockerx.client()
    except Exception as e:
        raise HTTPException(503, f"docker unavailable: {e}")
    # register lease BEFORE touching docker: the reaper/reconcile would
    # otherwise garbage-collect our containers mid-provisioning
    store.upsert(body.session_id, f"{body.lab_slug}@{body.lab_version}", ttl, [])
    dockerx.destroy_session(cli, body.session_id)  # idempotent re-provision
    store.drop(body.session_id, "reprovision")  # closes any stale relays
    store.upsert(body.session_id, f"{body.lab_slug}@{body.lab_version}", ttl, [])
    net = dockerx.create_network(cli, body.session_id)
    exposed = []
    relays = []
    try:
        for t in targets:
            c = dockerx.run_target(cli, body.session_id, net, t, t.get("resources"))
            ip = None
            for _ in range(30):
                ip = dockerx.container_ip(c, net.name)
                if ip:
                    break
                time.sleep(1)
            if not ip:
                raise RuntimeError(f"no container IP for {t['name']}")
            health = t.get("health") or {}
            hpath = health.get("path", "/healthz")
            first_port = int(t["ports"][0]) if t.get("ports") else 80
            if not dockerx.wait_ready(f"http://{ip}:{first_port}{hpath}"):
                raise RuntimeError(f"readiness failed for {t['name']}")
            # NOTE (local dev): relays bind 0.0.0.0 so the API container can reach
            # them via the bridge gateway; learners use 127.0.0.1. Bind to a
            # firewall or Tailnet in shared environments. Prod uses ingress.
            srv, rport = relay_mod.start("0.0.0.0", ip, first_port)
            relays.append(srv)
            exposed.append({"name": t["name"], "url": f"http://127.0.0.1:{rport}{hpath}",
                            "host": "127.0.0.1", "port": rport, "dev_digest": t["dev_digest"]})
    except Exception as e:
        for srv in relays:
            relay_mod.stop(srv)
        dockerx.destroy_session(cli, body.session_id)
        store.drop(body.session_id, "provision-failed")
        raise HTTPException(502, f"provision failed: {e}")
    store.add_relays(body.session_id, relays)
    exp = store.upsert(body.session_id, f"{body.lab_slug}@{body.lab_version}", ttl, exposed)
    return {"session_id": body.session_id, "network": net.name, "targets": exposed, "expires_at": exp}

@app.get("/v1/orch/sessions/{sid}")
def status(sid: str, _=Depends(authed)):
    live = sid in store.live()
    return {"session_id": sid, "live": live}

@app.post("/v1/orch/sessions/{sid}/extend")
def extend(sid: str, minutes: int = 30, _=Depends(authed)):
    exp = store.touch(sid, min(minutes, 30))
    if exp is None:
        raise HTTPException(404, "unknown session lease")
    return {"session_id": sid, "expires_at": exp}

@app.post("/v1/orch/sessions/{sid}/reset")
def reset(sid: str, lab_slug: str, lab_version: str, ttl_minutes: int = 60, _=Depends(authed)):
    try:
        cli = dockerx.client()
        dockerx.destroy_session(cli, sid)
    except Exception as e:
        raise HTTPException(503, f"docker unavailable: {e}")
    store.drop(sid, "reset")
    return provision(ProvisionIn(session_id=sid, lab_slug=lab_slug, lab_version=lab_version, ttl_minutes=ttl_minutes), True)

@app.delete("/v1/orch/sessions/{sid}")
def destroy(sid: str, _=Depends(authed)):
    try:
        removed = dockerx.destroy_session(dockerx.client(), sid)
    except Exception as e:
        raise HTTPException(503, f"docker unavailable: {e}")
    store.drop(sid, "destroyed")
    return {"session_id": sid, "removed": removed}

@app.get("/v1/orch/events")
def events(_=Depends(authed)):
    return store.events()
