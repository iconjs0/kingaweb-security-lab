"""Wave 2 golden tests: IDOR, SQLi, stored XSS, SSRF (fetcher+metadata pair)."""
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
PORTS = {"web-idor-01": 41211, "web-sqli-01": 41212, "web-xss-01": 41213, "web-ssrf-01": 41214}

def req(port, path, method="GET", body=None, headers=None):
    r = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method,
                               data=json.dumps(body).encode() if body is not None else None,
                               headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return resp.status, dict(resp.headers), json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), json.loads(e.read() or b"{}")

def start(slug, mode, port=None, extra=None, app_path=None):
    port = port or PORTS[slug]
    env = dict(os.environ, SESSION_SEED=SEED, SESSION_ID=SID, LAB_MODE=mode,
               PORT=str(port), PYTHONPATH=os.path.join(REPO, "packages", "lab-sdk"), **(extra or {}))
    path = app_path or os.path.join(REPO, "labs", "kingaweb-native", slug, "app.py")
    p = subprocess.Popen([sys.executable, path], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

def test_idor():
    def vuln(port):
        _, _, b = req(port, "/login", method="POST", body={"username": "amina", "password": "shopper"})
        assert b["orders"] == ["101"]
        s, _, b = req(port, "/orders/102", headers={"Authorization": f"Bearer {b['token']}"})
        # need token again: login returns token; re-login for clarity
        _, _, b2 = req(port, "/login", method="POST", body={"username": "amina", "password": "shopper"})
        s, _, b = req(port, "/orders/102", headers={"Authorization": f"Bearer {b2['token']}"})
        assert s == 200 and verify(b["flag"], SID, SEED, "read-other-order")
    def fixed(port):
        _, _, b = req(port, "/login", method="POST", body={"username": "amina", "password": "shopper"})
        assert req(port, "/orders/102", headers={"Authorization": f"Bearer {b['token']}"})[0] == 403
        assert req(port, "/orders/101", headers={"Authorization": f"Bearer {b['token']}"})[0] == 200
    run("web-idor-01", "vuln", vuln)
    run("web-idor-01", "fixed", fixed)

def test_sqli():
    def vuln(port):
        s, _, b = req(port, "/login", method="POST", body={"username": "admin' -- ", "password": "x"})
        assert s == 200 and verify(b["flag"], SID, SEED, "sqli-login")
    def fixed(port):
        assert req(port, "/login", method="POST", body={"username": "admin' -- ", "password": "x"})[0] == 401
        s, _, b = req(port, "/login", method="POST", body={"username": "guest", "password": "guest"})
        assert s == 200 and b["role"] == "user"
    run("web-sqli-01", "vuln", vuln)
    run("web-sqli-01", "fixed", fixed)

def test_xss():
    def vuln(port):
        assert req(port, "/comments", method="POST", body={"text": "<script>M123</script>"})[0] == 201
        s, _, b = req(port, "/flag?marker=M123")
        assert s == 200 and verify(b["flag"], SID, SEED, "stored-xss")
    def fixed(port):
        assert req(port, "/comments", method="POST", body={"text": "<script>M123</script>"})[0] == 201
        assert req(port, "/flag?marker=M123")[0] == 403
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/comments", timeout=5) as r:
            body, csp = r.read().decode(), r.headers.get("Content-Security-Policy", "")
        assert "Content-Security-Policy" in csp or "Content-Security-Policy" in str(r.headers)
        assert "<script>M123</script>" not in body
    run("web-xss-01", "vuln", vuln)
    run("web-xss-01", "fixed", fixed)

def test_ssrf():
    meta_path = os.path.join(REPO, "labs", "mocks", "internal-meta", "app.py")
    for mode, check in (("vuln", True), ("fixed", False)):
        meta = start("meta", mode, port=8081, app_path=meta_path)
        fetcher = start("web-ssrf-01", mode, extra={"META_HOST": "127.0.0.1:8081"})
        try:
            s, _, b = req(PORTS["web-ssrf-01"], "/fetch?url=http://127.0.0.1:8081/secret")
            if check:
                assert s == 200 and verify(b["flag"], SID, SEED, "fetch-secret")
            else:
                assert s == 403
        finally:
            stop(fetcher)
            stop(meta)
