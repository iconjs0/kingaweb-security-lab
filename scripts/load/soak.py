#!/usr/bin/env python3
"""Soak: N parallel learners launch -> dev-mint -> submit -> destroy (mpesa lab).
Reports p50/p95/max launch latency + failures. Verifies zero kw-* leftovers.
Usage: python3 scripts/load/soak.py --users 5 --rounds 2 [--lab web-http-01@0.1.0]
"""
import argparse
import json
import statistics
import subprocess
import sys
import threading
import time
import urllib.request

BASE = "http://localhost:8000"
LOCK = threading.Lock()
LAUNCH_TIMES: list[float] = []
ERRORS: list[str] = []

def call(method, path, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", **(
                                     {"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read()[:200].decode("utf-8", "replace")}
    except Exception as e:
        return 0, {"detail": f"{type(e).__name__}: {e}"}

IDENTITIES = ["learner@lab.dev", "instructor@lab.dev", "author@lab.dev", "admin@lab.dev"]

def learner(uid: int, lab: str, obj: str, rounds: int):
    _, b = call("POST", "/v1/auth/login", body={"email": IDENTITIES[uid % len(IDENTITIES)]})
    tok = b.get("token", "")
    for _ in range(rounds):
        t0 = time.time()
        code, sess = call("POST", "/v1/sessions", token=tok, body={"lab": lab})
        if code != 201 or "id" not in sess:
            with LOCK:
                ERRORS.append(f"u{uid} launch {code} {sess}")
            return
        with LOCK:
            LAUNCH_TIMES.append(time.time() - t0)
        sid = sess["id"]
        _, m = call("POST", f"/v1/dev/mint?session_id={sid}&objective_id={obj}", token=tok)
        code, sub = call("POST", f"/v1/sessions/{sid}/submissions", token=tok,
                         body={"objective_id": obj, "flag": m.get("flag", "")})
        if not sub.get("correct"):
            with LOCK:
                ERRORS.append(f"u{uid} solve failed {sub}")
        call("DELETE", f"/v1/sessions/{sid}", token=tok)

def leftovers() -> list[str]:
    out = subprocess.run(["docker", "network", "ls", "--format", "{{.Name}}"],
                         capture_output=True, text=True)
    return [l for l in out.stdout.splitlines() if l.startswith("kw-")]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--users", type=int, default=5)
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--lab", default="mpesa-bola-01@0.1.0")
    ap.add_argument("--objective", default="read-foreign-balance")
    a = ap.parse_args()
    print(f"soak: {a.users} users x {a.rounds} rounds on {a.lab}", flush=True)
    t0 = time.time()
    threads = [threading.Thread(target=learner, args=(i, a.lab, a.objective, a.rounds))
               for i in range(a.users)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall = time.time() - t0
    total = a.users * a.rounds
    print(f"launches ok: {len(LAUNCH_TIMES)}/{total}  errors: {len(ERRORS)}  wall: {wall:.1f}s")
    for e in ERRORS[:5]:
        print("  ERR", e)
    if LAUNCH_TIMES:
        s = sorted(LAUNCH_TIMES)
        idx = max(0, int(len(s) * 0.95) - 1)
        print(f"launch p50={statistics.median(s):.1f}s p95={s[idx]:.1f}s max={s[-1]:.1f}s")
    left = leftovers()
    print(f"leftovers: {left if left else 'none'}")
    return 1 if ERRORS or len(LAUNCH_TIMES) != total or left else 0

if __name__ == "__main__":
    sys.exit(main())
