"""web-authz-01: function-level authz. Any login can POST role changes (vuln). Fixed: admin-only."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "escalate-role"
USERS = {"user": {"password": "user", "role": "user"}, "admin": {"password": "admin", "role": "admin"}}
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
        if auth.startswith("Bearer "):
            return TOKENS.get(auth[7:])
        return None

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True})
        if self.path == "/admin/flag":
            me = self._me()
            if me and USERS.get(me, {}).get("role") == "admin":
                return self._send(200, {"flag": mint(SID, SEED, OBJ)})
            return self._send(403, {"error": "admins only"})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        if self.path == "/login":
            u = USERS.get(data.get("username", ""))
            if u and u["password"] == data.get("password"):
                import secrets
                tok = secrets.token_hex(8)
                TOKENS[tok] = data["username"]
                return self._send(200, {"token": tok, "role": u["role"]})
            return self._send(401, {"error": "bad creds"})
        if self.path.startswith("/api/users/") and self.path.endswith("/role"):
            me = self._me()
            if not me:
                return self._send(401, {"error": "login first"})
            target = self.path.split("/")[3]
            # VULN: no function-level check. Fixed: admins only.
            if MODE == "fixed" and USERS.get(me, {}).get("role") != "admin":
                return self._send(403, {"error": "function restricted to admins"})
            if target in USERS:
                USERS[target]["role"] = data.get("role", "user")
                return self._send(200, {"user": target, "role": USERS[target]["role"]})
            return self._send(404, {"error": "no such user"})
        return self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
