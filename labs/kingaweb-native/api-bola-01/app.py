"""api-bola-01: object + property authz. Any invoice readable; ssn always leaks (vuln).
Fixed: 403 foreign, ssn owner-only."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "bola-read"
INVOICES = {"INV-1": {"owner": "alice", "total": 42000, "ssn": "111-22-3333"},
            "INV-2": {"owner": "bob", "total": 87000, "ssn": "444-55-6666"}}
TOKENS: dict[str, str] = {}

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _me(self):
        auth = self.headers.get("Authorization", "")
        return TOKENS.get(auth[7:]) if auth.startswith("Bearer ") else None

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True})
        if self.path.startswith("/api/v1/invoices/"):
            me = self._me()
            if not me:
                return self._send(401, {"error": "login first"})
            iid = self.path.split("/")[4].split("?")[0]
            inv = INVOICES.get(iid)
            if not inv:
                return self._send(404, {"error": "no such invoice"})
            if MODE == "fixed":
                if inv["owner"] != me:
                    return self._send(403, {"error": "not your object"})
                return self._send(200, {"id": iid, "owner": me, "total": inv["total"], "ssn": inv["ssn"]})
            out = {"id": iid, **inv}
            if inv["owner"] != me:
                out["flag"] = mint(SID, SEED, OBJ)
            return self._send(200, out)
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/login":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        if data.get("username") in ("alice", "bob"):
            import secrets
            tok = secrets.token_hex(8)
            TOKENS[tok] = data["username"]
            mine = [k for k, v in INVOICES.items() if v["owner"] == data["username"]]
            return self._send(200, {"token": tok, "invoices": mine})
        return self._send(401, {"error": "unknown user (alice|bob)"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
