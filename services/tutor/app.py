"""Tutor stub: mode-aware canned hints. No LLM, no flags, no internet. stdlib only."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

CANNED = {
    "guided": "Nudge: compare your resource URL with another user's. Check hint level {level} in the brief. What status code do you expect after the fix?",
    "challenge": "Methodology only (no exact payload in challenge mode): map authz boundaries with Burp Repeater, one ID at a time, and document evidence.",
    "assessment": "Assessment mode: tutor is limited to time management and tool docs. No lab-specific hints. Keep going — document what you've tried.",
    "demo": "Demo mode: instructor may walk through the full chain. Reset anytime to replay.",
}

DENY_PATTERNS = ("kw{", "flag{", "payload", "exploit ")

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
            return self._send(200, {"ok": True, "service": "tutor-stub"})
        return self._send(404, {"error": "not found"})
    def do_POST(self):
        if self.path != "/v1/hint":
            return self._send(404, {"error": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return self._send(400, {"error": "bad json"})
        mode = str(data.get("mode", "challenge"))
        q = str(data.get("question", ""))[:500]
        level = int(data.get("unlocked_hint_level", 1) or 1)
        # output filter: refuse to repeat anything looking like a flag/payload request verbatim
        if any(p in q.lower() for p in DENY_PATTERNS) and mode in ("challenge", "assessment"):
            return self._send(200, {"mode": mode, "answer": CANNED[mode] if mode in CANNED else CANNED["challenge"], "filtered": True})
        answer = CANNED.get(mode, CANNED["challenge"]).format(level=level)
        return self._send(200, {"mode": mode, "answer": answer, "filtered": False})
    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 5008), H).serve_forever()
