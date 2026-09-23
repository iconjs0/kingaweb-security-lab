"""web-traversal-01: file read with ../ escape (vuln). Fixed: basename jail + allowlist.
Flag when secret.txt content (seed-derived) is proven read."""
import json
import os
import posixpath
from http.server import BaseHTTPRequestHandler, HTTPServer
from flag import mint

SEED = os.environ.get("SESSION_SEED", "dev-seed")
SID = os.environ.get("SESSION_ID", "dev-session")
MODE = os.environ.get("LAB_MODE", "vuln")
OBJ = "traverse-read"
FILES = {"public.txt": "Welcome to the file server.", "secret.txt": "SECRET-" + SEED[:8]}

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
            return self._send(200, {"ok": True, "files": ["public.txt"]})
        if self.path.startswith("/files"):
            from urllib.parse import urlparse, parse_qs
            name = parse_qs(urlparse(self.path).query).get("name", [""])[0]
            if MODE == "fixed":
                # jail: exact public allowlist, no separators, no dots-up
                if name != "public.txt":
                    return self._send(403, {"error": "path not allowed"})
                return self._send(200, {"name": name, "content": FILES[name]})
            # VULN: resolves inside a fake tree — ../ walks out of /files/
            norm = posixpath.normpath("/files/" + name)
            for f, content in FILES.items():
                if norm == f"/{f}" or norm.endswith(f"/{f}"):
                    out = {"name": f, "content": content}
                    if f == "secret.txt":
                        out["flag"] = mint(SID, SEED, OBJ)
                    return self._send(200, out)
            return self._send(404, {"error": "no such file"})
        return self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8080"))), H).serve_forever()
