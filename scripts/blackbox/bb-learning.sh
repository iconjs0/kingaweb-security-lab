#!/usr/bin/env bash
# Blackbox: learning modes + hint economy + finalize. Only HTTP.
# Usage: ./scripts/blackbox/bb-learning.sh [base_url]
# Requires: compose stack up (orchestrator wires real sessions).
set -u
BASE="${1:-http://localhost:8000}"
LAB="mpesa-bola-01@0.1.0"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }
jget() { python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }

echo "== learning blackbox @ $BASE =="
T=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"learner@lab.dev"}' | jget "d['token']") || T=""
G=$(curl -s -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d "{\"lab\":\"$LAB\",\"mode\":\"guided\"}")
GID=$(echo "$G" | jget "d['id']"); echo "$G" | grep -q '"mode":"guided"' && ok "guided launch ($GID)" || bad "guided launch" "$G"
H1=$(curl -s -X POST "$BASE/v1/sessions/$GID/hints/unlock" -H "Authorization: Bearer $T")
echo "$H1" | grep -q '"level":1' && echo "$H1" | grep -q '"cost":5' && ok "hint L1 staged + priced" || bad "hint L1" "$H1"
H2=$(curl -s -X POST "$BASE/v1/sessions/$GID/hints/unlock" -H "Authorization: Bearer $T")
echo "$H2" | grep -q '"level":2' && ok "hint L2 sequential" || bad "hint L2" "$H2"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions/$GID/hints/unlock" -H "Authorization: Bearer $T")" = "404" ] && ok "hints exhausted 404" || bad "hint exhaustion"
[ "$(curl -s -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d "{\"lab\":\"$LAB\",\"mode\":\"speedrun\"}" -o /dev/null -w '%{http_code}')" = "422" ] && ok "bad mode 422" || bad "bad mode"

A=$(curl -s -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d "{\"lab\":\"$LAB\",\"mode\":\"assessment\"}")
AID=$(echo "$A" | jget "d['id']"); echo "$A" | grep -q '"mode":"assessment"' && ok "assessment launch ($AID)" || bad "assessment launch" "$A"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions/$AID/hints/unlock" -H "Authorization: Bearer $T")" = "200" ] && ok "assessment hint 1 allowed" || bad "assessment hint 1"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions/$AID/hints/unlock" -H "Authorization: Bearer $T")" = "403" ] && ok "assessment hint 2 capped" || bad "assessment cap"
F=$(curl -s -X POST "$BASE/v1/sessions/$AID/finalize" -H "Authorization: Bearer $T")
echo "$F" | grep -q '"immutable":true' && ok "finalize freezes score" || bad "finalize" "$F"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions/$AID/finalize" -H "Authorization: Bearer $T")" = "409" ] && ok "double finalize 409" || bad "double finalize"
FLAG=$(curl -s -X POST "$BASE/v1/dev/mint?session_id=$AID&objective_id=read-foreign-balance" -H "Authorization: Bearer $T" | jget "d['flag']") || FLAG=""
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions/$AID/submissions" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d "{\"objective_id\":\"read-foreign-balance\",\"flag\":\"$FLAG\"}")" = "409" ] && ok "post-finalize submit locked" || bad "finalize lock"

D=$(curl -s -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d "{\"lab\":\"$LAB\",\"mode\":\"demo\"}")
DID=$(echo "$D" | jget "d['id']")
curl -s -X POST "$BASE/v1/sessions/$DID/hints/unlock" -H "Authorization: Bearer $T" | grep -q '"free":true' && ok "demo hints free" || bad "demo hints"
for s in "$GID" "$AID" "$DID"; do curl -s -X DELETE "$BASE/v1/sessions/$s" -H "Authorization: Bearer $T" > /dev/null; done
ok "cleanup destroys"
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
