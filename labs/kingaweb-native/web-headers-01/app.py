"""web-headers-01: transport + CORS. Vuln: ACAO * with credentials, no security headers.
Fixed: locked Origin allowlist + HSTS/CSP/frame options."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "cors-steal"
ALLOW = {"https://app.kingaweb.example"}

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj, origin=""):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if MODE == "vuln":
            self.send_header("Access-Control-Allow-Origin", origin or "*")
            self.send_header("Access-Control-Allow-Credentials", "true")
        else:
            if origin in ALLOW:
                self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
            self.send_header("Content-Security-Policy", "default-src 'self'")
            self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def _handle(self):
        origin = self.headers.get("Origin", "")
        if self.path == "/healthz":
            return self._send(200, {"ok": True}, origin)
        if self.path == "/api/data":
            return self._send(200, {"balance": 12000, "currency": "KES"}, origin)
        if self.path == "/cors/flag":
            creds = self.headers.get("Cookie", "")
            if MODE == "vuln" and origin and origin not in ALLOW and creds:
                return self._send(200, {"flag": mint(SID, SEED, OBJ)}, origin)
            return self._send(403, {"error": "origin not allowed"}, origin)
        return self._send(404, {"error": "not found"}, origin)

    do_GET = lambda self: self._handle()
    do_POST = lambda self: self._handle()

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
