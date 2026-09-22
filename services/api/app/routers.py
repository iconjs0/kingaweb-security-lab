"""All v1 routers: auth/labs/sessions/submissions/console/progress/teams/competitions/audit + dev mint."""
import json
import os
import time
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DBSession

from .auth import current_user, login_dev, require_roles
from .db import get_db
from . import orch as orch_client
from .flags import flag_hash, mint_flag, new_seed_hex, score_solve, verify_flag
from .models import Audit, Competition, Enrollment, Lab, Membership, Session, Submission, Team, User, HintUnlock

router = APIRouter()
_attempts: dict[str, list[float]] = {}  # session_id -> submit timestamps (rate limit)

def audit(db: DBSession, actor: str, action: str, target: str = "") -> None:
    db.add(Audit(actor_id=actor, action=action, target=target))
    db.commit()

def lab_or_404(db: DBSession, slug: str, version: str | None = None) -> Lab:
    q = db.query(Lab).filter(Lab.slug == slug)
    if version:
        q = q.filter(Lab.version == version)
    lab = q.order_by(Lab.version.desc()).first()
    if not lab:
        raise HTTPException(404, "lab not found")
    return lab

def own_session(db: DBSession, sid: str, user: User) -> Session:
    s = db.query(Session).filter(Session.id == sid).first()
    if not s:
        raise HTTPException(404, "session not found")
    if s.owner_id != user.id and user.role != "platform-admin":
        raise HTTPException(403, "not your session")
    return s

# ---- auth ----
class LoginIn(BaseModel):
    email: str

@router.post("/v1/auth/login")
def login(body: LoginIn, db: DBSession = Depends(get_db)):
    token = login_dev(db, body.email)
    return {"token": token, "token_type": "bearer"}

# ---- labs ----
@router.get("/v1/labs")
def list_labs(db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    return [
        {"slug": l.slug, "version": l.version, "title": l.title, "summary": l.summary,
         "track": l.track, "difficulty": l.difficulty, "time_minutes": l.time_minutes}
        for l in db.query(Lab).order_by(Lab.slug).all()
    ]

@router.get("/v1/labs/{slug}")
def get_lab(slug: str, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    l = lab_or_404(db, slug)
    return {"slug": l.slug, "version": l.version, "title": l.title, "summary": l.summary,
            "track": l.track, "difficulty": l.difficulty, "time_minutes": l.time_minutes,
            "ttl_minutes": l.ttl_minutes, "objectives": json.loads(l.objectives_json),
            "targets": json.loads(l.targets_json),
            "hint_levels": [{"level": h["level"], "cost": h["cost"]} for h in json.loads(l.hints_json or "[]")]}

# ---- sessions ----
MODES = ("guided", "challenge", "assessment", "demo")

class LaunchIn(BaseModel):
    lab: str = Field(pattern=r"^[a-z0-9-]+@[0-9.]+$")
    competition_id: str | None = None
    mode: str = "guided"

def _targets_for(lab: Lab) -> list[dict]:
    return json.loads(lab.targets_json)

@router.post("/v1/sessions", status_code=201)
def launch(body: LaunchIn, db: DBSession = Depends(get_db), user: User = Depends(current_user),
           idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    slug, version = body.lab.split("@", 1)
    lab = lab_or_404(db, slug, version)
    mode = (body.mode or "guided").lower()
    if mode not in MODES:
        raise HTTPException(422, f"mode must be one of {list(MODES)}")
    ttl = lab.ttl_minutes
    if mode == "assessment":
        ttl = min(ttl, 30)
    if idempotency_key:
        dup = db.query(Session).filter(Session.owner_id == user.id, Session.idempotency_key == idempotency_key).first()
        if dup:
            return {"id": dup.id, "deduplicated": True}
    sid = f"s-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)
    s = Session(id=sid, owner_id=user.id, lab_slug=lab.slug, lab_version=lab.version,
                seed_hex=new_seed_hex(), status="active", competition_id=body.competition_id,
                idempotency_key=idempotency_key, targets_json="[]", mode=mode, finalized=0,
                expires_at=now + timedelta(minutes=ttl))
    db.add(s)
    db.commit()
    targets: list[dict] = _targets_for(lab)
    provisioned = False
    if orch_client.base():
        try:
            code, resp = orch_client.provision(sid, lab.slug, lab.version, ttl, s.seed_hex)
            if code in (200, 201):
                targets = resp.get("targets", targets)
                s.targets_json = json.dumps(targets)
                provisioned = True
                audit(db, user.id, "session.provisioned", sid)
            else:
                # policy rejection is authoritative: refuse launch, don't hand out a dead session
                db.delete(s)
                db.commit()
                raise HTTPException(code, f"orchestrator refused: {resp.get('detail', resp)}")
        except HTTPException:
            raise
        except ConnectionError as e:
            audit(db, user.id, "orch.unavailable", f"{sid}:{e}")
        db.commit()
    else:
        audit(db, user.id, "session.launch", sid)
        db.commit()
    return {"id": sid, "lab": f"{lab.slug}@{lab.version}", "status": "active", "mode": mode,
            "expires_at": s.expires_at.isoformat(), "targets": targets, "provisioned": provisioned}

@router.get("/v1/sessions/{sid}")
def get_session(sid: str, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    s = own_session(db, sid, user)
    try:
        targets = json.loads(s.targets_json or "[]") or _targets_for(lab_or_404(db, s.lab_slug, s.lab_version))
    except Exception:
        targets = []
    return {"id": s.id, "lab": f"{s.lab_slug}@{s.lab_version}", "status": s.status,
            "mode": getattr(s, "mode", "guided"), "finalized": bool(getattr(s, "finalized", 0)),
            "expires_at": s.expires_at.isoformat() if s.expires_at else None, "targets": targets}

@router.post("/v1/sessions/{sid}/extend")
def extend(sid: str, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    s = own_session(db, sid, user)
    if s.status != "active" or getattr(s, "finalized", 0):
        raise HTTPException(409, "only active, unfinalized sessions extend")
    minutes = 30
    exp = s.expires_at if getattr(s.expires_at, "tzinfo", None) else s.expires_at.replace(tzinfo=timezone.utc)
    s.expires_at = exp + timedelta(minutes=minutes)
    if orch_client.base():
        try:
            orch_client.extend(sid, minutes)
        except Exception as e:
            audit(db, user.id, "orch.extend-failed", f"{sid}:{e}")
    audit(db, user.id, "session.extend", sid)
    db.commit()
    return {"id": sid, "expires_at": s.expires_at.isoformat()}

@router.post("/v1/sessions/{sid}/reset")
def reset(sid: str, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    s = own_session(db, sid, user)
    if getattr(s, "finalized", 0):
        raise HTTPException(409, "finalized sessions cannot reset")
    s.seed_hex = new_seed_hex()  # flags rotate; destroy+recreate semantics
    s.status = "active"
    if orch_client.base():
        try:
            lab = lab_or_404(db, s.lab_slug, s.lab_version)
            code, resp = orch_client.reset(sid, s.lab_slug, s.lab_version, lab.ttl_minutes, s.seed_hex)
            if code in (200, 201):
                s.targets_json = json.dumps(resp.get("targets", []))
            else:
                raise HTTPException(code, f"orchestrator reset refused: {resp.get('detail', resp)}")
        except HTTPException:
            raise
        except Exception as e:
            audit(db, user.id, "orch.reset-failed", f"{sid}:{e}")
    audit(db, user.id, "session.reset", sid)
    db.commit()
    return {"id": sid, "status": "active", "rotated": True}

@router.delete("/v1/sessions/{sid}")
def destroy(sid: str, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    s = own_session(db, sid, user)
    if orch_client.base() and not getattr(s, "targets_json", "[]") == "[]":
        # provisioned session: never report destroyed while containers may live
        try:
            code, resp = orch_client.destroy(sid)
            if code not in (200, 404):
                raise HTTPException(502, f"orchestrator destroy failed: {resp}")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(502, f"orchestrator unreachable, session kept active: {e}")
    elif orch_client.base():
        try:
            orch_client.destroy(sid)
        except Exception as e:
            audit(db, user.id, "orch.destroy-failed", f"{sid}:{e}")
    s.status = "destroyed"
    audit(db, user.id, "session.destroy", sid)
    db.commit()
    return {"id": sid, "status": "destroyed"}

# ---- submissions ----
class SubmitIn(BaseModel):
    objective_id: str
    flag: str
    remediation_done: bool = False

@router.post("/v1/sessions/{sid}/submissions")
def submit(sid: str, body: SubmitIn, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    s = own_session(db, sid, user)
    if s.status != "active" or getattr(s, "finalized", 0):
        raise HTTPException(409, "session not active or already finalized")
    now = time.time()
    hist = [t for t in _attempts.get(sid, []) if now - t < 60]
    if len(hist) >= 5:
        raise HTTPException(429, "rate limited: 5 submits/min")
    hist.append(now)
    _attempts[sid] = hist
    lab = lab_or_404(db, s.lab_slug, s.lab_version)
    objectives = [o["id"] for o in json.loads(lab.objectives_json)]
    if body.objective_id not in objectives:
        raise HTTPException(404, "unknown objective")
    ok = verify_flag(body.flag, s.id, s.lab_version, body.objective_id, s.seed_hex)
    attempts = db.query(Submission).filter(Submission.session_id == sid, Submission.objective_id == body.objective_id).count() + 1
    hint_cost = sum(u.cost for u in db.query(HintUnlock).filter(HintUnlock.session_id == sid).all())
    points = 0
    if ok:
        solves_before = db.query(Submission).filter(Submission.objective_id == body.objective_id, Submission.correct == 1).count()
        first = solves_before == 0
        points = score_solve(400, solves_before, hint_cost=hint_cost, attempts=attempts,
                             first_blood=first, remediation=body.remediation_done)
    db.add(Submission(session_id=sid, objective_id=body.objective_id, flag_hash=flag_hash(body.flag),
                      correct=1 if ok else 0, points=points))
    audit(db, user.id, f"submit.{'ok' if ok else 'fail'}", f"{sid}:{body.objective_id}")
    db.commit()
    return {"correct": ok, "points": points, "attempts": attempts, "hint_cost": hint_cost}

# ---- hints (staged unlocks, sequential, cost deducted from score) ----
@router.post("/v1/sessions/{sid}/hints/unlock")
def unlock_hint(sid: str, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    s = own_session(db, sid, user)
    if s.status != "active" or getattr(s, "finalized", 0):
        raise HTTPException(409, "session not active or already finalized")
    if getattr(s, "mode", "guided") == "demo":
        hints = json.loads(lab_or_404(db, s.lab_slug, s.lab_version).hints_json or "[]")
        return {"level": 0, "text": "Demo mode: all hints free. " + (hints[0]["text"] if hints else ""), "cost": 0, "free": True}
    done = db.query(HintUnlock).filter(HintUnlock.session_id == sid).count()
    if getattr(s, "mode", "guided") == "assessment" and done >= 1:
        raise HTTPException(403, "assessment allows at most 1 hint")
    hints = sorted(json.loads(lab_or_404(db, s.lab_slug, s.lab_version).hints_json or "[]"), key=lambda h: h["level"])
    if done >= len(hints):
        raise HTTPException(404, "no further hints")
    nxt = hints[done]
    db.add(HintUnlock(session_id=sid, level=nxt["level"], cost=nxt["cost"]))
    audit(db, user.id, "hint.unlock", f"{sid}:L{nxt['level']}")
    db.commit()
    return {"level": nxt["level"], "text": nxt["text"], "cost": nxt["cost"]}

# ---- finalize (assessment lock; immutable scoring) ----
@router.post("/v1/sessions/{sid}/finalize")
def finalize(sid: str, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    s = own_session(db, sid, user)
    if getattr(s, "finalized", 0):
        raise HTTPException(409, "already finalized")
    if s.status != "active":
        raise HTTPException(409, "session not active")
    subs = db.query(Submission).filter(Submission.session_id == sid, Submission.correct == 1).all()
    hints = sum(u.cost for u in db.query(HintUnlock).filter(HintUnlock.session_id == sid).all())
    gross = sum(x.points for x in subs)
    time_bonus = 0
    if getattr(s, "mode", "guided") == "assessment":
        lab = lab_or_404(db, s.lab_slug, s.lab_version)
        used_min = (datetime.now(timezone.utc) - s.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 60
        time_bonus = max(0, min(20, int(lab.time_minutes - used_min)))
    s.finalized = 1
    audit(db, user.id, "session.finalize", sid)
    db.commit()
    return {"session": sid, "solves": len(subs), "gross": gross, "hint_cost": hints,
            "time_bonus": time_bonus, "net": gross + time_bonus, "immutable": True}

# ---- safe console proxy (Phase 7 lite): allowlist + forward to session mocks ----
ALLOWED_HOSTS = {"mpesa-mock": "http://mpesa-mock:5009", "shop": "http://shop:8080"}

class ProxyIn(BaseModel):
    method: str = "GET"
    host: str
    path: str = "/"
    headers: dict[str, str] = {}
    body: str | None = None

@router.post("/v1/sessions/{sid}/requests")
def proxy(sid: str, body: ProxyIn, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    s = own_session(db, sid, user)
    if s.status != "active":
        raise HTTPException(409, "session not active")
    if body.method not in ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"):
        raise HTTPException(400, "method not allowed")
    if not body.path.startswith("/"):
        raise HTTPException(400, "path must start with /")
    lab = lab_or_404(db, s.lab_slug, s.lab_version)
    allowed = {t["allow_host"] for t in json.loads(lab.targets_json)} & set(ALLOWED_HOSTS)
    try:
        orch_targets = json.loads(s.targets_json or "[]")
    except Exception:
        orch_targets = []
    # orchestrator-provisioned loopback relays: exact host+port match only
    relay_ports = {(t.get("host"), int(t.get("port"))) for t in orch_targets
                   if t.get("host") in ("127.0.0.1", "localhost") and t.get("port")}
    url: str
    if body.host in ("127.0.0.1", "localhost"):
        match = [p for _, p in relay_ports]
        if not match:
            raise HTTPException(403, "no relay provisioned for this session")
        # single-target labs need no header; multi-target uses X-Relay-Port
        port = int((body.headers or {}).get("X-Relay-Port", match[0]))
        if port not in match:
            raise HTTPException(403, "relay port not in session allowlist")
        # relays bind host loopback; the API container reaches them via the host gateway
        rh = os.environ.get("RELAY_HOST", "127.0.0.1")
        url = f"http://{rh}:{port}" + body.path
        body.headers = {k: v for k, v in body.headers.items() if k.lower() != "x-relay-port"}
    else:
        if body.host not in allowed:
            raise HTTPException(403, f"host not in session allowlist: {sorted(allowed)}")
        url = ALLOWED_HOSTS[body.host] + body.path
    data = (body.body or "").encode()[:262144]
    req = urllib.request.Request(url, data=data or None, method=body.method,
                                 headers={k: v[:512] for k, v in list(body.headers.items())[:20]})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            raw = r.read(262144)
            return {"status": r.status, "body": raw.decode("utf-8", "replace"), "truncated": len(raw) == 262144}
    except Exception as e:
        raise HTTPException(502, f"upstream error: {type(e).__name__}")

# ---- progress ----
@router.get("/v1/progress")
def progress(db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    subs = db.query(Submission).join(Session, Submission.session_id == Session.id).filter(Session.owner_id == user.id).all()
    sess_ids = {s.session_id for s in subs}
    hints = sum(u.cost for u in db.query(HintUnlock).filter(HintUnlock.session_id.in_(sess_ids)).all()) if sess_ids else 0
    return {"user": user.email, "solves": sum(1 for x in subs if x.correct),
            "points": sum(x.points for x in subs), "hint_cost": hints,
            "net": sum(x.points for x in subs), "attempts": len(subs)}

# ---- teams ----
class TeamIn(BaseModel):
    name: str

@router.post("/v1/teams", status_code=201)
def create_team(body: TeamIn, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    t = Team(id=f"t-{uuid.uuid4().hex[:8]}", name=body.name, owner_id=user.id)
    db.add(t)
    db.add(Membership(team_id=t.id, user_id=user.id))
    audit(db, user.id, "team.create", t.id)
    db.commit()
    return {"id": t.id, "name": t.name}

@router.post("/v1/teams/{tid}/join")
def join_team(tid: str, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    if not db.query(Team).filter(Team.id == tid).first():
        raise HTTPException(404, "team not found")
    if not db.query(Membership).filter(Membership.team_id == tid, Membership.user_id == user.id).first():
        db.add(Membership(team_id=tid, user_id=user.id))
        audit(db, user.id, "team.join", tid)
        db.commit()
    return {"team": tid, "member": user.email}

# ---- competitions ----
class CompIn(BaseModel):
    name: str

@router.post("/v1/competitions", status_code=201)
def create_comp(body: CompIn, db: DBSession = Depends(get_db),
                user: User = Depends(require_roles("instructor", "platform-admin"))):
    c = Competition(id=f"c-{uuid.uuid4().hex[:8]}", name=body.name, owner_id=user.id)
    db.add(c)
    audit(db, user.id, "competition.create", c.id)
    db.commit()
    return {"id": c.id, "name": c.name}

@router.post("/v1/competitions/{cid}/join")
def join_comp(cid: str, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    if not db.query(Competition).filter(Competition.id == cid).first():
        raise HTTPException(404, "competition not found")
    if not db.query(Enrollment).filter(Enrollment.competition_id == cid, Enrollment.user_id == user.id).first():
        db.add(Enrollment(competition_id=cid, user_id=user.id))
        audit(db, user.id, "competition.join", cid)
        db.commit()
    return {"competition": cid, "member": user.email}

@router.get("/v1/competitions/{cid}/leaderboard")
def leaderboard(cid: str, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    c = db.query(Competition).filter(Competition.id == cid).first()
    if not c:
        raise HTTPException(404, "competition not found")
    rows: dict[str, int] = {}
    subs = (db.query(Submission, Session).join(Session, Submission.session_id == Session.id)
            .filter(Session.competition_id == cid, Submission.correct == 1).all())
    for sub, sess in subs:
        rows[sess.owner_id] = rows.get(sess.owner_id, 0) + sub.points
    board = sorted(rows.items(), key=lambda kv: kv[1], reverse=True)
    if c.frozen:
        return {"competition": cid, "frozen": True, "leaderboard": []}
    return {"competition": cid, "frozen": False, "leaderboard": [{"user": u, "points": p} for u, p in board]}

# ---- audit (admin) ----
@router.get("/v1/audit")
def read_audit(db: DBSession = Depends(get_db), user: User = Depends(require_roles("platform-admin"))):
    return [{"actor": a.actor_id, "action": a.action, "target": a.target,
             "at": a.created_at.isoformat() if a.created_at else None}
            for a in db.query(Audit).order_by(Audit.id.desc()).limit(100).all()]

# ---- dev mint (LOCAL ONLY; prod must set ALLOW_DEV_MINT=false) ----
@router.post("/v1/dev/mint")
def dev_mint(session_id: str, objective_id: str, db: DBSession = Depends(get_db), user: User = Depends(current_user)):
    if os.environ.get("ALLOW_DEV_MINT", "false").lower() != "true":
        raise HTTPException(403, "dev mint disabled")
    s = own_session(db, session_id, user)
    return {"flag": mint_flag(s.id, s.lab_version, objective_id, s.seed_hex)}
