"""Internal metadata mock for web-ssrf-01 (2nd target in the session net).
Exposes a seed-derived secret. No flag logic — the fetcher mints on retrieval."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

SEED = os.environ.get("SESSION_SEED", "dev-seed")

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
            return self._send(200, {"ok": True, "service": "mock-metadata"})
        if self.path == "/secret":
            return self._send(200, {"internal_secret": "META-" + SEED[:8]})
        return self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8081), H).serve_forever()
