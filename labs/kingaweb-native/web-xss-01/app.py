"""web-xss-01: stored XSS guestbook. Vuln: raw reflection. Fixed: escaped.
Flag needs YOUR session marker stored unescaped (proves injection, not just typing)."""
import html
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "stored-xss"
COMMENTS: list[str] = []

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj, ctype="application/json"):
        body = (json.dumps(obj) if ctype == "application/json" else obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        if MODE == "fixed":
            self.send_header("Content-Security-Policy", "default-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True})
        if self.path == "/comments":
            items = COMMENTS if MODE == "vuln" else [html.escape(c) for c in COMMENTS]
            page = "<ul>" + "".join(f"<li>{c}</li>" for c in items) + "</ul>"
            return self._send(200, page, "text/html")
        if self.path.startswith("/flag"):
            from urllib.parse import urlparse, parse_qs
            marker = parse_qs(urlparse(self.path).query).get("marker", [""])[0]
            probe = f"<script>{marker}</script>" if marker else ""
            # vuln: raw store + raw render. fixed: escaped render + CSP, never mints.
            if MODE == "vuln" and probe and any(probe in c for c in COMMENTS):
                return self._send(200, {"flag": mint(SID, SEED, OBJ)})
            return self._send(403, {"error": "no unescaped marker stored"})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/comments":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        text = str(data.get("text", ""))[:500]
        if not text:
            return self._send(400, {"error": "empty"})
        COMMENTS.append(text)
        return self._send(201, {"stored": len(COMMENTS)})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
