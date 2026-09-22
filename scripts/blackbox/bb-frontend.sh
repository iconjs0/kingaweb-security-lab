#!/usr/bin/env bash
# Blackbox: Next.js frontend. Starts prod server if :3000 is down; stops it if it started it.
# Usage: ./scripts/blackbox/bb-frontend.sh [--skip-build]
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }
STARTED=0

if [ "${1:-}" != "--skip-build" ]; then
  (npm run build --workspace=web > /tmp/opencode/bb-web-build.log 2>&1) || { echo "FAIL: web build (see /tmp/opencode/bb-web-build.log)"; exit 1; }
  ok "web production build"
fi
if ! curl -s -o /dev/null --max-time 3 http://localhost:3000/; then
  (setsid nohup npm run start --workspace=web > /tmp/opencode/bb-web.log 2>&1 < /dev/null &) ; sleep 8; STARTED=1
fi
code() { curl -s -o /tmp/opencode/bb-page.html -w "%{http_code}" "http://localhost:3000$1"; }
has()  { grep -q "$1" /tmp/opencode/bb-page.html; }

echo "== frontend blackbox =="
for p in / /login /labs /labs/web-idor-01 /labs/mpesa-bola-01 /workspace /gallery; do
  [ "$(code "$p")" = "200" ] && ok "GET $p 200" || bad "GET $p"
done
code / > /dev/null;          has "Skip to content" && ok "skip link" || bad "skip link"
code /gallery > /dev/null;   has "Component gallery" && has "LabTable" && ok "gallery documents components" || bad "gallery"
code /labs > /dev/null;      has "mpesa-bola-01" && ok "catalogue lists TZ lab" || bad "catalogue content"
code /workspace > /dev/null; has "HTTP console" && ok "workspace console panel" || bad "workspace"
code /login > /dev/null;     has "acceptable-use" && ok "AUP consent on login" || bad "login AUP"
[ "$(code /labs/nope)" = "404" ] && ok "unknown slug 404" || bad "unknown slug"

if [ "$STARTED" = "1" ]; then fuser -k 3000/tcp > /dev/null 2>&1; sleep 2; ok "server stopped"; fi
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
