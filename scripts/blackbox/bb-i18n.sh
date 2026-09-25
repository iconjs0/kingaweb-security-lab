#!/usr/bin/env bash
# Blackbox: i18n. Lab ?lang=sw overrides with en fallback.
# Usage: ./scripts/blackbox/bb-i18n.sh [base_url]
set -u
BASE="${1:-http://localhost:8000}"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }
J() { python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }

echo "== i18n blackbox @ $BASE =="
T=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"learner@lab.dev"}' | J "d['token']") || T=""
curl -s "$BASE/v1/labs/web-http-01" -H "Authorization: Bearer $T" | grep -q "Override" && ok "en default" || bad "en default"
curl -s "$BASE/v1/labs/web-http-01?lang=sw" -H "Authorization: Bearer $T" | grep -q "Undani" && ok "sw title" || bad "sw title"
curl -s "$BASE/v1/labs/web-http-01?lang=sw" -H "Authorization: Bearer $T" | grep -q "override-note" && ok "objective ids stable" || bad "ids stable"
curl -s "$BASE/v1/labs/mpesa-bola-01?lang=sw" -H "Authorization: Bearer $T" | grep -q "Jaribio" && ok "mpesa sw" || bad "mpesa sw"
curl -s "$BASE/v1/labs/web-http-01?lang=fr" -H "Authorization: Bearer $T" | grep -q '"lang":"en"' && ok "unknown lang falls back" || bad "fallback"
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
