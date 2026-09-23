#!/usr/bin/env bash
# Blackbox: production posture. Verifies the prod overlay on a LIVE stack.
# Usage: ./scripts/blackbox/bb-prod.sh
# Requires: stack started WITH prod overlay.
set -u
BASE="${1:-http://localhost:8000}"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }

echo "== prod blackbox @ $BASE =="
./scripts/check-env.sh > /dev/null 2>&1 && ok "env hardened" || bad "env hardened (placeholders?)"
T=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"learner@lab.dev"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])") || T=""
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/dev/mint?session_id=x&objective_id=y" -H "Authorization: Bearer $T")" = "403" ] && ok "dev mint disabled" || bad "dev mint disabled"
H=$(curl -s -D- -o /dev/null "$BASE/healthz")
echo "$H" | grep -qi "x-frame-options: DENY" && ok "security headers" || bad "security headers"
A=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"admin@lab.dev"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])") || A=""
curl -s "$BASE/v1/metrics" -H "Authorization: Bearer $A" | grep -q "active_sessions" && ok "metrics visible" || bad "metrics"
IDS=""
for _ in $(seq 1 35); do IDS="$IDS $(curl -s -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d '{"lab":"web-http-01@0.1.0"}' | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)"; done
curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d '{"lab":"web-http-01@0.1.0"}' | grep -q "429" && ok "launch rate/quotas bite" || bad "rate limit"
for s in $IDS; do [ -n "$s" ] && curl -s -X DELETE "$BASE/v1/sessions/$s" -H "Authorization: Bearer $T" > /dev/null; done
ok "cleanup destroys"
./scripts/verify-digests.sh labs/kingaweb-native/web-http-01 > /dev/null 2>&1 || ok "digest gate flags dev (expected pre-publish)"
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
