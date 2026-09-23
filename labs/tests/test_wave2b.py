"""Wave 2b golden tests: CSRF, traversal, upload, reset-token crypto."""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "packages", "lab-sdk"))
from flag import verify  # noqa: E402

SEED, SID = "golden-seed-1234", "s-golden"
PORTS = {"web-csrf-01": 41231, "web-traversal-01": 41232, "web-upload-01": 41233, "web-crypto-01": 41234}

def req(port, path, method="GET", body=None, headers=None):
    r = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method,
                               data=json.dumps(body).encode() if body is not None else None,
                               headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return resp.status, dict(resp.headers), json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), json.loads(e.read() or b"{}")

def start(slug, mode):
    port = PORTS[slug]
    env = dict(os.environ, SESSION_SEED=SEED, SESSION_ID=SID, LAB_MODE=mode,
               PORT=str(port), PYTHONPATH=os.path.join(REPO, "packages", "lab-sdk"))
    p = subprocess.Popen([sys.executable, os.path.join(REPO, "labs", "kingaweb-native", slug, "app.py")],
                         env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            if req(port, "/healthz")[0] == 200:
                return p
        except Exception:
            pass
        time.sleep(0.2)
    p.kill()
    raise RuntimeError(f"{slug} did not start")

def stop(p):
    p.terminate()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()

def run(slug, mode, fn):
    p = start(slug, mode)
    try:
        fn(PORTS[slug])
    finally:
        stop(p)

def _cookie(h):
    sc = [v for k, v in h.items() if k.lower() == "set-cookie"][0]
    return sc.split("session=")[1].split(";")[0]

def test_csrf():
    def vuln(port):
        s, h, b = req(port, "/login", method="POST", body={"username": "victim", "password": "victim"})
        assert s == 200 and b["csrf_token"]
        ck = _cookie(h)
        s, _, b = req(port, "/api/transfer", method="POST", body={"to": "attacker", "amount": 100},
                       headers={"Cookie": f"session={ck}"})
        assert s == 200 and verify(b["flag"], SID, SEED, "csrf-transfer")
    def fixed(port):
        s, h, b = req(port, "/login", method="POST", body={"username": "victim", "password": "victim"})
        ck = _cookie(h)
        assert req(port, "/api/transfer", method="POST", body={"to": "attacker", "amount": 100},
                   headers={"Cookie": f"session={ck}"})[0] == 403
        s, _, b = req(port, "/api/transfer", method="POST",
                       body={"to": "attacker", "amount": 50, "csrf_token": b["csrf_token"]},
                       headers={"Cookie": f"session={ck}"})
        assert s == 200 and "flag" not in b  # under threshold, legit flow works
    run("web-csrf-01", "vuln", vuln)
    run("web-csrf-01", "fixed", fixed)

def test_traversal():
    def vuln(port):
        s, _, b = req(port, "/files?name=../secret.txt")
        assert s == 200 and verify(b["flag"], SID, SEED, "traverse-read")
    def fixed(port):
        assert req(port, "/files?name=../secret.txt")[0] == 403
        s, _, b = req(port, "/files?name=public.txt")
        assert s == 200 and "flag" not in b
    run("web-traversal-01", "vuln", vuln)
    run("web-traversal-01", "fixed", fixed)

def test_upload():
    marker = "<script>UP1</script>"
    b64 = base64.b64encode(marker.encode()).decode()
    def vuln(port):
        s, _, b = req(port, "/avatar", method="POST", body={"filename": "evil.svg", "content_b64": b64})
        assert s == 201
        s, _, b = req(port, "/flag?marker=UP1")
        assert s == 200 and verify(b["flag"], SID, SEED, "upload-xss")
    def fixed(port):
        assert req(port, "/avatar", method="POST", body={"filename": "evil.svg", "content_b64": b64})[0] == 403
        assert req(port, "/flag?marker=UP1")[0] == 403
    run("web-upload-01", "vuln", vuln)
    run("web-upload-01", "fixed", fixed)

def test_crypto():
    def forge():
        import time as _t
        raw = base64.urlsafe_b64encode(f"admin:{int(_t.time())}".encode()).decode()
        return raw
    def vuln(port):
        s, _, b = req(port, "/reset/request", method="POST", body={"username": "user"})
        assert s == 200 and b["token"]
        s, _, b = req(port, "/reset/confirm", method="POST",
                       body={"token": forge(), "new_password": "pwned"})
        assert s == 200 and verify(b["flag"], SID, SEED, "forge-reset")
    def fixed(port):
        s, _, _ = req(port, "/reset/confirm", method="POST",
                       body={"token": forge(), "new_password": "pwned"})
        assert s == 403
    run("web-crypto-01", "vuln", vuln)
    run("web-crypto-01", "fixed", fixed)
