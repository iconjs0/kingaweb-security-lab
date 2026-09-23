"""web-crypto-01: predictable reset tokens (vuln: base64 user:timestamp, no auth).
Fixed: HMAC-signed random tokens with expiry. Flag on admin password change."""
import base64
import hashlib
import hmac
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "forge-reset"
SIGN_KEY = os.urandom(16)
PW = {"admin": "start-pw", "user": "user"}

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _issue(self, user):
        if MODE == "fixed":
            import secrets
            tok = secrets.token_hex(12)
            sig = hmac.new(SIGN_KEY, f"{user}:{tok}:{int(time.time())}".encode(), hashlib.sha256).hexdigest()
            FIXED_TOKENS[f"{tok}.{sig}"] = (user, time.time() + 600)
            return f"{tok}.{sig}"
        return base64.urlsafe_b64encode(f"{user}:{int(time.time())}".encode()).decode()

    def _check(self, token):
        if MODE == "fixed":
            try:
                tok, sig = token.split(".", 1)
            except ValueError:
                return None
            rec = FIXED_TOKENS.get(token)
            if not rec:
                return None
            user, exp = rec
            if time.time() > exp:
                return None
            return user
        try:
            user, _ = base64.urlsafe_b64decode(token + "==").decode().split(":", 1)
            return user if user in PW else None
        except Exception:
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
        if self.path == "/reset/request":
            if data.get("username") not in PW:
                return self._send(404, {"error": "no such user"})
            return self._send(200, {"token": self._issue(data["username"])})
        if self.path == "/reset/confirm":
            user = self._check(data.get("token", ""))
            if not user:
                return self._send(403, {"error": "bad token"})
            PW[user] = data.get("new_password", PW[user])
            out = {"user": user, "changed": True}
            if user == "admin":
                out["flag"] = mint(SID, SEED, OBJ)
            return self._send(200, out)
        return self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass

FIXED_TOKENS: dict[str, tuple[str, float]] = {}

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
