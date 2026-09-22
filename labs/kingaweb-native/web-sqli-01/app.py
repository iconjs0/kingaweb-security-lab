"""web-sqli-01: real sqlite injection. Vuln: string-concatenated login. Fixed: parameterized."""
import json
import os
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "sqli-login"

DB = sqlite3.connect(":memory:", check_same_thread=False)
DB.execute("CREATE TABLE users(username TEXT, password TEXT, role TEXT)")
DB.execute("INSERT INTO users VALUES('admin','s3cr3t-admin-pw','admin')")
DB.execute("INSERT INTO users VALUES('guest','guest','user')")

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
            return self._send(200, {"ok": True, "hint": "POST /login {username, password}"})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/login":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            data = {}
        u, p = data.get("username", ""), data.get("password", "")
        try:
            if MODE == "vuln":
                q = f"SELECT username, role FROM users WHERE username='{u}' AND password='{p}'"
                row = DB.execute(q).fetchone()
            else:
                row = DB.execute("SELECT username, role FROM users WHERE username=? AND password=?", (u, p)).fetchone()
        except Exception:
            return self._send(500, {"error": "query failed"})
        if row and row[1] == "admin":
            return self._send(200, {"flag": mint(SID, SEED, OBJ), "role": "admin"})
        if row:
            return self._send(200, {"role": row[1]})
        return self._send(401, {"error": "bad creds"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
