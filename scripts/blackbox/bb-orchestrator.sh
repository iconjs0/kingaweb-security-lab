#!/usr/bin/env bash
# Blackbox: orchestrator isolation via the API. Only HTTP + docker labels.
# Usage: ./scripts/blackbox/bb-orchestrator.sh
# Requires: compose stack up (bb-docker.sh). Slow-ish (~60s, two provisions).
set -u
API="${API:-http://localhost:8000}"
ORCH="${ORCH:-http://localhost:8001}"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }
jget() { python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }

echo "== orchestrator blackbox =="
curl -s "$ORCH/healthz" | grep -q orchestrator && ok "orch healthz" || bad "orch healthz"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$ORCH/v1/orch/events" -H 'Authorization: Bearer wrong')" = "401" ] && ok "orch token gate" || bad "orch token gate"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$ORCH/v1/orch/events")" = "401" ] && ok "orch missing token 401" || bad "orch missing token"
BEFORE=$(docker network ls --format "{{.Name}}" | grep -c "^kw-" || true)

A=$(curl -s -X POST "$API/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"learner@lab.dev"}' | jget "d['token']") || A=""
B=$(curl -s -X POST "$API/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"instructor@lab.dev"}' | jget "d['token']") || B=""
SA=$(curl -s -X POST "$API/v1/sessions" -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d '{"lab":"mpesa-bola-01@0.1.0"}')
SB=$(curl -s -X POST "$API/v1/sessions" -H "Authorization: Bearer $B" -H 'Content-Type: application/json' -d '{"lab":"mpesa-bola-01@0.1.0"}')
IDA=$(echo "$SA" | jget "d['id']"); PA=$(echo "$SA" | jget "d['targets'][0]['port']")
IDB=$(echo "$SB" | jget "d['id']"); PB=$(echo "$SB" | jget "d['targets'][0]['port']")
echo "$SA" | grep -q '"provisioned":true' && ok "A provisioned ($IDA :$PA)" || bad "A provision" "$SA"
echo "$SB" | grep -q '"provisioned":true' && ok "B provisioned ($IDB :$PB)" || bad "B provision" "$SB"
[ -n "$PA" ] && [ -n "$PB" ] && [ "$PA" != "$PB" ] && ok "distinct relay ports" || bad "distinct relays" "$PA vs $PB"
curl -s "http://127.0.0.1:$PA/rates" | grep -q KES && curl -s "http://127.0.0.1:$PB/rates" | grep -q KES && ok "both relays serve" || bad "relays serve"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$API/v1/sessions/$IDA" -H "Authorization: Bearer $B")" = "403" ] && ok "cross-learner session 403" || bad "cross-learner"

REF=$(curl -s -X POST "$API/v1/sessions" -H "Authorization: Bearer $A" -H 'Content-Type: application/json' -d '{"lab":"web-idor-01@0.1.0"}')
echo "$REF" | grep -q '"provisioned":true' && ok "idor retired-placeholder now launches" || bad "idor launch" "$REF"
RID=$(echo "$REF" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
curl -s -X DELETE "$API/v1/sessions/$RID" -H "Authorization: Bearer $A" > /dev/null
OT=$(grep ORCHESTRATOR_TOKEN .env 2>/dev/null | cut -d= -f2 || echo "")
if [ -n "$OT" ]; then
  [ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$ORCH/v1/orch/sessions" -H "Authorization: Bearer $OT" -H 'Content-Type: application/json' -d '{"session_id":"bb-evil","lab_slug":"nope","lab_version":"9.9.9","ttl_minutes":60}')" = "403" ] && ok "orch unknown manifest refused" || bad "orch manifest gate"
fi

curl -s -X DELETE "$API/v1/sessions/$IDA" -H "Authorization: Bearer $A" | grep -q destroyed && ok "A destroyed" || bad "A destroy"
sleep 2
curl -s --max-time 4 "http://127.0.0.1:$PA/rates" > /dev/null 2>&1 && bad "A relay dead" || ok "A relay dead"
curl -s --max-time 4 "http://127.0.0.1:$PB/rates" | grep -q KES && ok "B unaffected" || bad "B unaffected"
docker network ls --format "{{.Name}}" | grep -q "kw-$IDA" && bad "A network removed" || ok "A network removed"
curl -s -X DELETE "$API/v1/sessions/$IDB" -H "Authorization: Bearer $B" > /dev/null
AFTER=$(docker network ls --format "{{.Name}}" | grep -c "^kw-" || true)
[ "$AFTER" -le "$BEFORE" ] && ok "no new session leftovers" || bad "session leftovers" "before=$BEFORE after=$AFTER"
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
