"""web-csrf-01: state-changing POST authed by cookie alone (vuln).
Fixed: per-session CSRF token required."""
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "csrf-transfer"
BAL = {"victim": 1000, "attacker": 0}
SESSIONS: dict[str, dict] = {}

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj, headers=None):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _me(self):
        for part in (self.headers.get("Cookie", "") or "").split(";"):
            if part.strip().startswith("session="):
                return SESSIONS.get(part.strip()[8:])
        return None

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        if self.path == "/login":
            if data.get("username") == "victim" and data.get("password") == "victim":
                sid, csrf = secrets.token_hex(8), secrets.token_hex(8)
                SESSIONS[sid] = {"user": "victim", "csrf": csrf}
                return self._send(200, {"csrf_token": csrf},
                                   {"Set-Cookie": f"session={sid}; HttpOnly; Path=/"})
            return self._send(401, {"error": "bad creds (victim/victim)"})
        if self.path == "/api/transfer":
            me = self._me()
            if not me:
                return self._send(401, {"error": "login first"})
            # VULN: cookie alone authorizes. Fixed: token must match session.
            if MODE == "fixed" and data.get("csrf_token") != me["csrf"]:
                return self._send(403, {"error": "bad csrf token"})
            to, amt = data.get("to", ""), int(data.get("amount", 0) or 0)
            if to not in BAL or amt <= 0 or amt > BAL["victim"]:
                return self._send(400, {"error": "bad transfer"})
            BAL["victim"] -= amt
            BAL[to] += amt
            out = {"balances": BAL}
            if to == "attacker" and BAL["attacker"] >= 100:
                out["flag"] = mint(SID, SEED, OBJ)
            return self._send(200, out)
        return self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
