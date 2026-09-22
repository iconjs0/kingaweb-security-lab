"""Orchestrator client (control plane -> orchestrator). Best-effort with audit trail.
Empty ORCHESTRATOR_URL = orchestrator bypassed (static manifest targets)."""
import json
import os
import urllib.request

def base() -> str:
    return os.environ.get("ORCHESTRATOR_URL", "").rstrip("/")

def _call(method: str, path: str, body: dict | None = None, timeout: int = 40) -> tuple[int, dict]:
    tok = os.environ.get("ORCHESTRATOR_TOKEN", "")
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(base() + path, data=data if body is not None or method in ("POST",) else None,
                                 method=method, headers={"Content-Type": "application/json",
                                                         "Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {"detail": str(e)}
    except Exception as e:
        raise ConnectionError(str(e))

def provision(sid: str, slug: str, version: str, ttl: int, seed_hex: str = "") -> tuple[int, dict]:
    return _call("POST", "/v1/orch/sessions",
                 {"session_id": sid, "lab_slug": slug, "lab_version": version,
                  "ttl_minutes": ttl, "seed_hex": seed_hex}, timeout=90)

def extend(sid: str, minutes: int) -> tuple[int, dict]:
    return _call("POST", f"/v1/orch/sessions/{sid}/extend?minutes={minutes}", {})

def reset(sid: str, slug: str, version: str, ttl: int, seed_hex: str = "") -> tuple[int, dict]:
    return _call("POST", f"/v1/orch/sessions/{sid}/reset?lab_slug={slug}&lab_version={version}&ttl_minutes={ttl}&seed_hex={seed_hex}", {})

def destroy(sid: str) -> tuple[int, dict]:
    return _call("DELETE", f"/v1/orch/sessions/{sid}", None)
