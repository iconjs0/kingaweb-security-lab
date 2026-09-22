"""web-http-01: HTTP semantics. Vuln: X-HTTP-Method-Override turns GET into state change."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "override-note"
NOTE = {"text": "hello"}

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj, ctype="application/json"):
        body = (json.dumps(obj) if ctype == "application/json" else obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _route(self, method, path, query, body):
        if path == "/healthz":
            return 200, {"ok": True}, "application/json"
        if path == "/note" and method == "GET":
            return 200, NOTE, "application/json"
        if path == "/note" and method == "POST":
            NOTE["text"] = (body.get("text") or NOTE["text"])[:200]
            return 200, NOTE, "application/json"
        if path == "/flag":
            if NOTE["text"] != "hello":
                return 200, {"flag": mint(SID, SEED, OBJ)}, "application/json"
            return 403, {"error": "note untouched — tamper it first"}, "application/json"
        return 404, {"error": "not found"}, "application/json"

    def _handle(self, method):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path)
        override = (self.headers.get("X-HTTP-Method-Override", "") or "").upper()
        # VULN: override honored on safe methods. Fixed: ignored.
        eff = override if (MODE == "vuln" and override) else method
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if eff == "POST" and method == "GET":
            data = {"text": q.get("text", "")}  # state change smuggled in a GET
        code, obj, ct = self._route(eff, u.path, q, data)
        self._send(code, obj, ct)

    do_GET = lambda self: self._handle("GET")
    do_POST = lambda self: self._handle("POST")

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
