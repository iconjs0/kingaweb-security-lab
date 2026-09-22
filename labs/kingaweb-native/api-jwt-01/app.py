"""api-jwt-01: JWT mistakes. Vuln: alg=none trusted, signature skipped.
Fixed: HS256 verify enforced, none rejected. Hand-rolled (stdlib) on purpose."""
import base64
import hashlib
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "jwt-none"
KEY = os.urandom(16)

def b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def issue(role: str) -> str:
    h = b64e(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    p = b64e(json.dumps({"sub": "user", "role": role}).encode())
    return f"{h}.{p}.{b64e(hmac.new(KEY, f'{h}.{p}'.encode(), hashlib.sha256).digest())}"

def claims(token: str) -> dict | None:
    try:
        h_b, p_b, sig = token.split(".")
        hdr = json.loads(b64d(h_b))
        if MODE == "vuln" and hdr.get("alg") == "none":
            return json.loads(b64d(p_b))  # the mistake
        if hdr.get("alg") != "HS256":
            return None
        good = b64e(hmac.new(KEY, f"{h_b}.{p_b}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, good):
            return None
        return json.loads(b64d(p_b))
    except Exception:
        return None

def none_token(role: str) -> str:
    h = b64e(json.dumps({"alg": "none", "typ": "JWT"}).encode())
    return f"{h}.{b64e(json.dumps({'sub': 'user', 'role': role}).encode())}."

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True})
        if self.path == "/admin/flag":
            auth = self.headers.get("Authorization", "")
            c = claims(auth[7:]) if auth.startswith("Bearer ") else None
            if c and c.get("role") == "admin":
                return self._send(200, {"flag": mint(SID, SEED, OBJ)})
            return self._send(403, {"error": "admin token required"})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/login":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        if data.get("username") == "user" and data.get("password") == "user":
            return self._send(200, {"token": issue("user")})
        return self._send(401, {"error": "bad creds"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
