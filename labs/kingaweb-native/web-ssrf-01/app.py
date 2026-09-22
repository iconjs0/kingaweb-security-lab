"""web-ssrf-01 fetcher: GET /fetch?url=. Vuln: any http URL. Fixed: allowlist only.
Flag when the internal mock secret is retrieved (expected derived from seed)."""
import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "fetch-secret"
META = os.environ.get("META_HOST", "mock-metadata:8081")
EXPECTED = "META-" + SEED[:8]
ALLOW = {"mock-metadata:8081", "localhost:8080", "127.0.0.1:8080"}

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
        if self.path.startswith("/fetch"):
            from urllib.parse import urlparse, parse_qs
            target = parse_qs(urlparse(self.path).query).get("url", [""])[0]
            u = urlparse(target)
            if u.scheme not in ("http",):
                return self._send(400, {"error": "http only"})
            if MODE == "fixed" and u.netloc not in ALLOW:
                return self._send(403, {"error": "host not allowlisted"})
            try:
                with urllib.request.urlopen(target, timeout=4) as r:
                    body = r.read(65536).decode("utf-8", "replace")
            except Exception as e:
                return self._send(502, {"error": f"fetch failed: {type(e).__name__}"})
            if EXPECTED in body:
                return self._send(200, {"fetched": body[:200], "flag": mint(SID, SEED, OBJ)})
            return self._send(200, {"fetched": body[:200]})
        return self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
