"""api-ratelimit-01: business-flow abuse. Coupon redeemable forever (vuln).
Fixed: 2 redemptions per coupon. Flag at 5 redemptions."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "abuse-redeem"
COUPONS = {"WELCOME10": {"uses": 0, "credit": 10}}
BALANCES: dict[str, int] = {}
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
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        if self.path == "/login":
            if data.get("username") == "user" and data.get("password") == "user":
                import secrets
                tok = secrets.token_hex(8)
                TOKENS[tok] = "user"
                BALANCES.setdefault("user", 0)
                return self._send(200, {"token": tok, "balance": 0})
            return self._send(401, {"error": "bad creds"})
        if self.path == "/api/v1/coupons/redeem":
            me = self._me()
            if not me:
                return self._send(401, {"error": "login first"})
            c = COUPONS.get(data.get("code", ""))
            if not c:
                return self._send(404, {"error": "no such coupon"})
            if MODE == "fixed" and c["uses"] >= 2:
                return self._send(429, {"error": "coupon exhausted (max 2 redemptions)"})
            c["uses"] += 1
            BALANCES[me] += c["credit"]
            out = {"balance": BALANCES[me], "uses": c["uses"]}
            if c["uses"] >= 5:
                out["flag"] = mint(SID, SEED, OBJ)
            return self._send(200, out)
        return self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
