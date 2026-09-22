"""api-mass-01: mass assignment. PATCH profile applies every key incl. role (vuln).
Fixed: nickname-only allowlist."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "mass-assign"
USERS = {"user": {"password": "user", "nickname": "newbie", "role": "user"}}
TOKENS: dict[str, str] = {}

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
            return self._send(200, {"ok": True})
        if self.path == "/admin/flag":
            me = self._me()
            if me and USERS.get(me, {}).get("role") == "admin":
                return self._send(200, {"flag": mint(SID, SEED, OBJ)})
            return self._send(403, {"error": "admins only"})
        if self.path == "/api/v1/me":
            me = self._me()
            if not me:
                return self._send(401, {"error": "login first"})
            return self._send(200, {"user": me, **USERS[me]})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/login":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        u = USERS.get(data.get("username", ""))
        if u and u["password"] == data.get("password"):
            import secrets
            tok = secrets.token_hex(8)
            TOKENS[tok] = data["username"]
            return self._send(200, {"token": tok})
        return self._send(401, {"error": "bad creds"})

    def do_PATCH(self):
        if self.path != "/api/v1/profile":
            return self._send(404, {"error": "not found"})
        me = self._me()
        if not me:
            return self._send(401, {"error": "login first"})
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        if MODE == "fixed":
            # allowlist: nickname only
            if "nickname" in data:
                USERS[me]["nickname"] = str(data["nickname"])[:50]
        else:
            for k, v in data.items():
                if k != "password":
                    USERS[me][k] = v
        return self._send(200, {"user": me, **USERS[me]})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
