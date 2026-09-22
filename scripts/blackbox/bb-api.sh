#!/usr/bin/env bash
# Blackbox: control-plane API. No source imports, only HTTP.
# Usage: ./scripts/blackbox/bb-api.sh [base_url]
# Requires: compose stack up (./scripts/blackbox/bb-docker.sh), .env present.
set -u
BASE="${1:-http://localhost:8000}"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); echo "PASS: $1"; }
bad()  { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }
jget() { python3 -c "import sys,json;print(json.load(sys.stdin)$1)"; }

echo "== API blackbox @ $BASE =="
H=$(curl -s "$BASE/healthz"); [ "$H" = '{"ok":true,"service":"api"}' ] && ok "healthz" || bad "healthz" "$H"

LT=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"learner@lab.dev"}' | jget "['token']") || LT=""
IT=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"instructor@lab.dev"}' | jget "['token']") || IT=""
AT=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"admin@lab.dev"}' | jget "['token']") || AT=""
[ -n "$LT" ] && [ -n "$IT" ] && [ -n "$AT" ] && ok "dev login x3 roles" || bad "dev login"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"mallory@evil.dev"}')" = "401" ] && ok "unknown identity 401" || bad "unknown identity"

[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/v1/labs")" = "401" ] && ok "unauth catalogue 401" || bad "unauth catalogue"
LABS=$(curl -s "$BASE/v1/labs" -H "Authorization: Bearer $LT")
echo "$LABS" | grep -q web-idor-01 && echo "$LABS" | grep -q mpesa-bola-01 && ok "catalogue seeded (2 labs)" || bad "catalogue seeded" "$LABS"

S1=$(curl -s -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $LT" -H 'Content-Type: application/json' -H 'Idempotency-Key: bb-1' -d '{"lab":"web-idor-01@0.1.0"}' | jget "['id']")
S2=$(curl -s -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $LT" -H 'Content-Type: application/json' -H 'Idempotency-Key: bb-1' -d '{"lab":"web-idor-01@0.1.0"}' | jget "['id']")_
[ -n "$S1" ] && [ "$S1" = "${S2%_}" ] && ok "idempotent launch ($S1)" || bad "idempotent launch" "$S1 vs $S2"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/v1/sessions/$S1" -H "Authorization: Bearer $IT")" = "403" ] && ok "cross-user session 403" || bad "cross-user session"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/v1/sessions/$S1" -H "Authorization: Bearer $LT")" = "200" ] && ok "owner session 200" || bad "owner session"

W=$(curl -s -X POST "$BASE/v1/sessions/$S1/submissions" -H "Authorization: Bearer $LT" -H 'Content-Type: application/json' -d '{"objective_id":"read-other-order","flag":"KW{wrong}"}' | jget "['correct']")
[ "$W" = "False" ] && ok "wrong flag rejected" || bad "wrong flag" "$W"
FLAG=$(curl -s -X POST "$BASE/v1/dev/mint?session_id=$S1&objective_id=read-other-order" -H "Authorization: Bearer $LT" | jget "['flag']") || FLAG=""
G=$(curl -s -X POST "$BASE/v1/sessions/$S1/submissions" -H "Authorization: Bearer $LT" -H 'Content-Type: application/json' -d "{\"objective_id\":\"read-other-order\",\"flag\":\"$FLAG\",\"remediation_done\":true}")
echo "$G" | grep -q '"correct":true' && ok "HMAC flag roundtrip + scored" || bad "flag roundtrip" "$G"
curl -s "$BASE/v1/progress" -H "Authorization: Bearer $LT" | grep -q '"solves":1' && ok "progress counts solve" || bad "progress"

[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions/$S1/requests" -H "Authorization: Bearer $LT" -H 'Content-Type: application/json' -d '{"method":"GET","host":"169.254.169.254","path":"/"}')" = "403" ] && ok "console SSRF host denied" || bad "console SSRF"
ALLOW=$(curl -s -X POST "$BASE/v1/sessions/$S1/requests" -H "Authorization: Bearer $LT" -H 'Content-Type: application/json' -d '{"method":"GET","host":"shop","path":"/nope"}' -o /dev/null -w '%{http_code}')
[ "$ALLOW" = "502" ] && ok "console allowlist forwards (shop unreachable in dev = 502, not 403)" || bad "console allowlist" "$ALLOW"

[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/v1/audit" -H "Authorization: Bearer $LT")" = "403" ] && ok "audit learner-denied" || bad "audit RBAC"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/v1/audit" -H "Authorization: Bearer $AT")" = "200" ] && ok "audit admin-visible" || bad "audit admin"

[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/competitions" -H "Authorization: Bearer $LT" -H 'Content-Type: application/json' -d '{"name":"x"}')" = "403" ] && ok "competition learner-denied" || bad "competition RBAC"
CID=$(curl -s -X POST "$BASE/v1/competitions" -H "Authorization: Bearer $IT" -H 'Content-Type: application/json' -d '{"name":"friday"}' | jget "['id']") || CID=""
[ -n "$CID" ] && [ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/competitions/$CID/join" -H "Authorization: Bearer $LT")" = "200" ] && [ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/v1/competitions/$CID/leaderboard" -H "Authorization: Bearer $LT")" = "200" ] && ok "competition join+board ($CID)" || bad "competition flow"

[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions/$S1/extend" -H "Authorization: Bearer $LT")" = "200" ] && ok "extend" || bad "extend"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions/$S1/reset" -H "Authorization: Bearer $LT")" = "200" ] && ok "reset rotates" || bad "reset"
[ "$(curl -s -X DELETE "$BASE/v1/sessions/$S1" -H "Authorization: Bearer $LT" | jget "['status']")" = "destroyed" ] && ok "destroy" || bad "destroy"

echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
