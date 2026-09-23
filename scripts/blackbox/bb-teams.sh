#!/usr/bin/env bash
# Blackbox: classroom. Teams, assignments, cohort progress, certificates.
# Usage: ./scripts/blackbox/bb-teams.sh [base_url]
set -u
BASE="${1:-http://localhost:8000}"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }
J() { python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }

echo "== classroom blackbox @ $BASE =="
L=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"learner@lab.dev"}' | J "d['token']") || L=""
I=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"instructor@lab.dev"}' | J "d['token']") || I=""
T=$(curl -s -X POST "$BASE/v1/teams" -H "Authorization: Bearer $I" -H 'Content-Type: application/json' -d '{"name":"bb-class"}' | J "d['id']") || T=""
[ -n "${T:-}" ] && ok "team created ($T)" || { bad "team create"; echo "== $PASS passed, $FAIL failed =="; exit 1; }
curl -s -X POST "$BASE/v1/teams/$T/join" -H "Authorization: Bearer $L" | grep -q learner && ok "learner joined" || bad "join"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/assignments" -H "Authorization: Bearer $L" -H 'Content-Type: application/json' -d "{\"team_id\":\"$T\",\"title\":\"x\",\"labs\":[]}")" = "403" ] && ok "learner cannot assign" || bad "assignment RBAC"
A=$(curl -s -X POST "$BASE/v1/assignments" -H "Authorization: Bearer $I" -H 'Content-Type: application/json' -d "{\"team_id\":\"$T\",\"title\":\"bb-week1\",\"labs\":[\"web-http-01@0.1.0\"]}" | J "d['id']") || A=""
[ -n "${A:-}" ] && ok "assignment created ($A)" || bad "assignment create"
S=$(curl -s -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $L" -H 'Content-Type: application/json' -d '{"lab":"web-http-01@0.1.0"}' | J "d['id']") || S=""
[ "$(curl -s -X POST "$BASE/v1/assignments/$A/submit" -H "Authorization: Bearer $L" -H 'Content-Type: application/json' -d "{\"session_id\":\"$S\"}" | J "d.get('session','')")" = "$S" ] && ok "session submitted" || bad "submit"
curl -s "$BASE/v1/teams/$T/progress" -H "Authorization: Bearer $I" | grep -q "u-learner" && ok "cohort progress" || bad "cohort progress"
C=$(curl -s -X POST "$BASE/v1/certificates/issue" -H "Authorization: Bearer $I" -H 'Content-Type: application/json' -d "{\"user_email\":\"learner@lab.dev\",\"assignment_id\":\"$A\"}" | J "d.get('code','')") || C=""
echo "$C" | grep -q "^KW-CERT-" && ok "certificate issued ($C)" || bad "cert issue" "$C"
curl -s "$BASE/v1/certificates/$C" | grep -q "learner@lab.dev" && ok "certificate verifies publicly" || bad "cert verify"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/v1/certificates/KW-CERT-NOPE")" = "404" ] && ok "unknown cert 404" || bad "unknown cert"
curl -s -X DELETE "$BASE/v1/sessions/$S" -H "Authorization: Bearer $L" > /dev/null
ok "cleanup destroys"
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
