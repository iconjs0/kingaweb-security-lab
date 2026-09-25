"""GraphQL golden: foreign ssn + deep nesting succeed (vuln), blocked (fixed)."""
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "packages", "lab-sdk"))
from flag import verify  # noqa: E402

SEED, SID, PORT = "golden-seed-1234", "s-golden", 41241

def req(path, method="GET", body=None, headers=None):
    r = urllib.request.Request(f"http://127.0.0.1:{PORT}{path}", method=method,
                               data=json.dumps(body).encode() if body is not None else None,
                               headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")

def start(mode):
    env = dict(os.environ, SESSION_SEED=SEED, SESSION_ID=SID, LAB_MODE=mode,
               PORT=str(PORT), PYTHONPATH=os.path.join(REPO, "packages", "lab-sdk"))
    p = subprocess.Popen([sys.executable, os.path.join(REPO, "labs", "kingaweb-native", "api-graphql-01", "app.py")],
                         env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            if req("/healthz")[0] == 200:
                return p
        except Exception:
            pass
        time.sleep(0.2)
    p.kill()
    raise RuntimeError("graphql did not start")

def stop(p):
    p.terminate()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()

def gql(port, tok, query):
    return req("/graphql", method="POST", body={"query": query},
               headers={"Authorization": f"Bearer {tok}"})

def login(port):
    _, b = req("/login", method="POST", body={"username": "alice"})
    return b["token"]

def test_graphql():
    p = start("vuln")
    try:
        tok = login(PORT)
        s, b = gql(PORT, tok, 'query{user(id:"2"){id ssn}}')
        assert s == 200 and verify(b["data"]["user"]["flag_ssn"], SID, SEED, "graphql-ssn")
        deep = "query" + "{user" * 6 + '(id:"1"){id}' + "}" * 6
        s, b = gql(PORT, tok, deep)
        assert s == 200 and verify(b["data"]["user"]["flag_deep"], SID, SEED, "graphql-deep")
    finally:
        stop(p)

def test_graphql_fixed():
    p = start("fixed")
    try:
        tok = login(PORT)
        assert gql(PORT, tok, 'query{user(id:"2"){id ssn}}')[0] == 403
        deep = "query" + "{user" * 6 + '(id:"1"){id}' + "}" * 6
        assert gql(PORT, tok, deep)[0] == 400
        s, b = gql(PORT, tok, 'query{user(id:"1"){id name}}')
        assert s == 200 and "flag_ssn" not in b["data"]["user"]
    finally:
        stop(p)
