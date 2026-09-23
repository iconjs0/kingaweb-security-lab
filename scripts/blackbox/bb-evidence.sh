#!/usr/bin/env bash
# Blackbox: evidence workspace. Findings validation, notes, report exports.
# Usage: ./scripts/blackbox/bb-evidence.sh [base_url]
set -u
BASE="${1:-http://localhost:8000}"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }
J() { python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }

echo "== evidence blackbox @ $BASE =="
A=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"learner@lab.dev"}' | J "d['token']") || A=""
B=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"instructor@lab.dev"}' | J "d['token']") || B=""
S=$(curl -s -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d '{"lab":"web-http-01@0.1.0"}' | J "d['id']") || S=""
[ -n "${S:-}" ] && ok "session ($S)" || { bad "launch"; echo "== $PASS passed, $FAIL failed =="; exit 1; }

[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions/$S/findings" -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d '{"title":"x"}')" = "422" ] && ok "thin finding 422" || bad "thin finding"
THIN=$(python3 -c "import json;print(json.dumps(dict(title='t',description='substantive description here',evidence='x',impact='substantive impact here',cwe='CWE-639',remediation='substantive remediation here',retest='substantive retest here')))")
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions/$S/findings" -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d "$THIN")" = "422" ] && ok "thin evidence 422" || bad "thin evidence"
FULL=$(python3 -c "import json;print(json.dumps({k:f'substantive {k} content here' for k in ['title','description','evidence','impact','cwe','remediation','retest']}))")
F=$(curl -s -X POST "$BASE/v1/sessions/$S/findings" -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d "$FULL" | J "d['id']") || F=""
[ -n "${F:-}" ] && ok "finding recorded (#$F)" || bad "finding create"
[ "$(curl -s "$BASE/v1/sessions/$S/findings" -H "Authorization: Bearer $A" | J "len(d)")" = "1" ] && ok "finding listed" || bad "finding list"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/v1/sessions/$S/findings" -H "Authorization: Bearer $B")" = "403" ] && ok "cross-user findings 403" || bad "cross-user findings"

curl -s -X PUT "$BASE/v1/sessions/$S/notes" -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d '{"body":"override at X-HTTP-Method-Override"}' | grep -q saved && ok "notes saved" || bad "notes save"
curl -s "$BASE/v1/sessions/$S/notes" -H "Authorization: Bearer $A" | grep -q "override at" && ok "notes roundtrip" || bad "notes read"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/v1/sessions/$S/notes" -H "Authorization: Bearer $B")" = "403" ] && ok "cross-user notes 403" || bad "cross-user notes"

curl -s "$BASE/v1/sessions/$S/report" -H "Authorization: Bearer $A" | grep -q "web-http-01" && ok "report JSON" || bad "report JSON"
H=$(curl -s -w '\n%{content_type}:%{http_code}' "$BASE/v1/sessions/$S/report.html" -H "Authorization: Bearer $A")
echo "$H" | grep -q "text/html" && echo "$H" | grep -q "substantive description content here" && ok "report HTML printable" || bad "report HTML"
curl -s -X DELETE "$BASE/v1/sessions/$S/findings/$F" -H "Authorization: Bearer $A" | grep -q deleted && ok "finding deleted" || bad "finding delete"
curl -s -X DELETE "$BASE/v1/sessions/$S" -H "Authorization: Bearer $A" > /dev/null
ok "cleanup destroys"
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
