"""api-graphql-01: hand-rolled tiny GraphQL. Vulns: cross-user ssn field + unbounded
nesting depth (expensive resolver). Fixed: owner-only ssn, depth cap 4."""
import json
import os
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
USERS = {"alice": {"id": "1", "name": "alice", "email": "alice@lab.dev", "ssn": "111-22-3333"},
         "bob": {"id": "2", "name": "bob", "email": "bob@lab.dev", "ssn": "444-55-6666"}}
TOKENS: dict[str, str] = {}

def depth_of(query: str) -> int:
    depth = max_depth = 0
    for ch in query:
        if ch == "{":
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch == "}":
            depth -= 1
    return max_depth

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _me(self):
        auth = self.headers.get("Authorization", "")
        return TOKENS.get(auth[7:]) if auth.startswith("Bearer ") else None

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True, "schema": "query{user(id){id name email ssn}}"})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        if self.path == "/login":
            if data.get("username") in USERS:
                import secrets
                tok = secrets.token_hex(8)
                TOKENS[tok] = data["username"]
                return self._send(200, {"token": tok})
            return self._send(401, {"error": "unknown user (alice|bob)"})
        if self.path != "/graphql":
            return self._send(404, {"error": "not found"})
        me = self._me()
        if not me:
            return self._send(401, {"error": "login first"})
        query = data.get("query", "")
        m = re.search(r"user\s*\(\s*id\s*:\s*\"?(\w+)\"?\s*\)", query)
        if not m:
            return self._send(400, {"error": "try query{user(id:\"1\"){id name}}"})
        target = next((u for u in USERS.values() if u["id"] == m.group(1)), None)
        if not target:
            return self._send(404, {"error": "no such user"})
        depth = depth_of(query)
        # expensive nested resolver: simulated cost per extra level
        if depth > 4:
            if MODE == "fixed":
                return self._send(400, {"error": "query too deep (max 4)"})
            time.sleep(min(depth - 4, 3) * 0.5)
        fields = set(re.findall(r"\b(id|name|email|ssn)\b", query))
        out: dict = {"id": target["id"]}
        if "name" in fields:
            out["name"] = target["name"]
        if "email" in fields:
            out["email"] = target["email"]
        if "ssn" in fields:
            # VULN: any caller reads ssn. Fixed: owner only.
            if MODE == "fixed" and target["name"] != me:
                return self._send(403, {"error": "ssn is owner-only"})
            out["ssn"] = target["ssn"]
            if target["name"] != me and MODE == "vuln":
                out["flag_ssn"] = mint(SID, SEED, "graphql-ssn")
        if depth > 5 and MODE == "vuln":
            out["flag_deep"] = mint(SID, SEED, "graphql-deep")
        return self._send(200, {"data": {"user": out}})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
