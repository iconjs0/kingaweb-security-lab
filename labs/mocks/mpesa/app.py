"""M-Pesa MOCK for authorized training only. No real money, no real telco, in-memory."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, hmac, hashlib, os

CALLBACK_SECRET = os.environ.get("MPESA_CALLBACK_SECRET", "dev-only-mock-secret")
BALANCES = {"255700000001": 50000, "255700000002": 12000}  # KES, test MSISDNs only

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
            return self._send(200, {"ok": True, "service": "mpesa-mock"})
        if self.path == "/rates":
            return self._send(200, {"currency": "KES", "balances": BALANCES})
        return self._send(404, {"error": "not found"})
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, {"error": "bad json"})
        if self.path == "/c2b/validate":
            # VULN version (training target): trusts client-supplied `account` without binding to auth user.
            # Remediation exercise: bind account to session user server-side.
            acct = str(data.get("account", ""))
            amount = int(data.get("amount", 0) or 0)
            if acct not in BALANCES:
                return self._send(404, {"error": "unknown test account"})
            if amount <= 0 or amount > 100000:
                return self._send(400, {"error": "amount out of mock bounds (1..100000)"})
            return self._send(200, {"ok": True, "account": acct, "amount": amount,
                                    "note": "MOCK: no real charge. Vuln: server did not verify account ownership."})
        if self.path == "/stk/callback":
            # Correct behavior: require HMAC; vuln image skips this check (lab task 2: forge then fix).
            sig = self.headers.get("X-Mock-Signature", "")
            raw = json.dumps(data, sort_keys=True).encode()
            good = hmac.new(CALLBACK_SECRET.encode(), raw, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, good):
                return self._send(200, {"ok": False, "reason": "invalid signature (mock correctly rejected)",
                                        "hint": "vuln version would accept this — your job: forge then enforce verify"})
            return self._send(200, {"ok": True, "result": "payment confirmed (MOCK)"})
        return self._send(404, {"error": "not found"})
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 5009), H).serve_forever()
