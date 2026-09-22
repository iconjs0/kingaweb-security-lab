"""web-cookies-01: session trust. Vuln: unsigned base64 JSON cookie. Fixed: HMAC-signed."""
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
OBJ = "become-admin"
SIGN_KEY = os.environ.get("COOKIE_KEY", "boot-random-" + os.urandom(4).hex())

def encode(sess: dict) -> str:
    raw = base64.urlsafe_b64encode(json.dumps(sess).encode()).decode()
    if MODE == "fixed":
        sig = hmac.new(SIGN_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()[:32]
        return raw + "." + sig
    return raw

def decode(cookie: str) -> dict | None:
    try:
        if MODE == "fixed":
            raw, sig = cookie.split(".", 1)
            good = hmac.new(SIGN_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()[:32]
            if not hmac.compare_digest(sig, good):
                return None
        else:
            raw = cookie.split(".", 1)[0]
        return json.loads(base64.urlsafe_b64decode(raw + "==").decode())
    except Exception:
        return None

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

    def _sess(self):
        for part in (self.headers.get("Cookie", "") or "").split(";"):
            if part.strip().startswith("session="):
                return decode(part.strip()[8:])
        return None

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True})
        if self.path == "/login":
            return self._send(200, {"hint": "cookie set; try reading it"},
                               {"Set-Cookie": f"session={encode({'user': 'guest'})}; HttpOnly; Path=/"})
        if self.path == "/admin":
            s = self._sess()
            if s and s.get("user") == "admin":
                return self._send(200, {"flag": mint(SID, SEED, OBJ)})
            return self._send(403, {"error": "admins only"})
        return self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
