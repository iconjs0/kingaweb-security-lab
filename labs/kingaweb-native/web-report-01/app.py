"""web-report-01: evidence + reporting. No vuln — board mints flag on complete finding."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
OBJ = "write-finding"
REQUIRED = ["description", "evidence", "impact", "cwe", "remediation", "retest"]

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
        if self.path == "/template":
            return self._send(200, {"required": REQUIRED,
                                    "example": {k: "..." for k in REQUIRED}})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/findings":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, {"error": "bad json"})
        missing = [k for k in REQUIRED if not str(data.get(k, "")).strip()]
        thin = [k for k in REQUIRED if k in data and len(str(data[k]).strip()) < 12]
        if missing or thin:
            return self._send(422, {"missing": missing, "too_thin": thin,
                                    "hint": "each field needs substance (>=12 chars)"})
        return self._send(200, {"flag": mint(SID, SEED, OBJ), "grade": "complete"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
