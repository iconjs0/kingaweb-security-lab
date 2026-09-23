"""web-upload-01: avatar upload. Vuln: any extension served with sniffable type (SVG XSS).
Fixed: png/jpg allowlist, nosniff, download disposition. Uploads live in /tmp (ro fs)."""
import base64
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "upload-xss"
STORE = "/tmp/uploads"
os.makedirs(STORE, exist_ok=True)
TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".html": "text/html"}

class H(BaseHTTPRequestHandler):
    def _send(self, code, obj, ctype="application/json"):
        body = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        if MODE == "fixed":
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Disposition", "attachment")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/healthz":
            return self._send(200, {"ok": True, "accept": [".png", ".jpg"] if MODE == "fixed" else "any"})
        if self.path.startswith("/uploads/"):
            name = os.path.basename(self.path.split("/uploads/", 1)[1].split("?")[0])
            if "/" in name or name.startswith("."):
                return self._send(403, {"error": "bad name"})
            ext = os.path.splitext(name)[1].lower()
            if MODE == "fixed" and ext not in (".png", ".jpg"):
                return self._send(403, {"error": "type not allowed"})
            try:
                with open(os.path.join(STORE, name), "rb") as f:
                    data = f.read(262144)
            except FileNotFoundError:
                return self._send(404, {"error": "no such upload"})
            return self._send(200, data, TYPES.get(ext, "application/octet-stream"))
        if self.path.startswith("/flag"):
            from urllib.parse import urlparse, parse_qs
            marker = parse_qs(urlparse(self.path).query).get("marker", [""])[0]
            probe = f"<script>{marker}</script>" if marker else ""
            if MODE == "vuln" and probe:
                for fn in os.listdir(STORE):
                    if fn.endswith(".svg"):
                        with open(os.path.join(STORE, fn), "rb") as f:
                            if probe.encode() in f.read():
                                return self._send(200, {"flag": mint(SID, SEED, OBJ)})
            return self._send(403, {"error": "no live SVG marker served"})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/avatar":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0) or 0)
        try:
            data = json.loads(self.rfile.read(min(n, 262144)) or b"{}")
        except Exception:
            data = {}
        name = os.path.basename(str(data.get("filename", "")))
        ext = os.path.splitext(name)[1].lower()
        if not name or "/" in name:
            return self._send(400, {"error": "bad filename"})
        if MODE == "fixed" and ext not in (".png", ".jpg"):
            return self._send(403, {"error": "only .png/.jpg accepted"})
        try:
            raw = base64.b64decode(data.get("content_b64", ""))
        except Exception:
            return self._send(400, {"error": "bad base64"})
        if len(raw) > 200000:
            return self._send(400, {"error": "too large"})
        with open(os.path.join(STORE, name), "wb") as f:
            f.write(raw)
        return self._send(201, {"file": f"/uploads/{name}"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
