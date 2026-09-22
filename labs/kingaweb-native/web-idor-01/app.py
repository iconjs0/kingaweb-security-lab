"""web-idor-01: real target. Login, own orders; foreign order readable (vuln). Fixed: ownership check."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "read-other-order"
USERS = {"amina": "shopper", "juma": "shopper"}
ORDERS = {"101": {"owner": "amina", "items": ["kitenge"]},
          "102": {"owner": "juma", "items": ["kahawa"]}}
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
        if self.path.startswith("/orders/"):
            me = self._me()
            if not me:
                return self._send(401, {"error": "login first"})
            oid = self.path.split("/")[2].split("?")[0]
            o = ORDERS.get(oid)
            if not o:
                return self._send(404, {"error": "no such order"})
            # VULN: no ownership check. Fixed: 403 for foreign orders.
            if MODE == "fixed" and o["owner"] != me:
                return self._send(403, {"error": "not your order"})
            if o["owner"] != me:
                return self._send(200, {**o, "flag": mint(SID, SEED, OBJ)})
            return self._send(200, o)
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/login":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        if USERS.get(data.get("username")) == data.get("password"):
            import secrets
            tok = secrets.token_hex(8)
            TOKENS[tok] = data["username"]
            return self._send(200, {"token": tok, "orders": [k for k, v in ORDERS.items() if v["owner"] == data["username"]]})
        return self._send(401, {"error": "bad creds"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
