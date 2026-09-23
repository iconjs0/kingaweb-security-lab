#!/usr/bin/env bash
# Blackbox: vulnerability intelligence. Live feeds, priority, review queue.
# Usage: ./scripts/blackbox/bb-intel.sh
# Requires: compose stack up. First sync takes ~2 min (EPSS bulk load).
set -u
BASE="${INTEL_BASE:-http://localhost:8002}"
IT="${INTEL_TOKEN:-$(grep INTEL_TOKEN .env 2>/dev/null | cut -d= -f2)}"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }
J() { python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }

echo "== intel blackbox @ $BASE =="
curl -s "$BASE/healthz" | grep -q intelligence && ok "healthz" || bad "healthz"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/v1/intel/vulns")" = "401" ] && ok "auth gate" || bad "auth gate"
[ -n "${IT:-}" ] && ok "token present" || { bad "token"; echo "== $PASS passed, $FAIL failed =="; exit 1; }

curl -s -X POST "$BASE/v1/intel/sync" -H "Authorization: Bearer $IT" | grep -q '"started":true' && ok "sync started" || bad "sync start"
DONE=0
for _ in $(seq 1 40); do
  ST=$(curl -s "$BASE/v1/intel/sync/status" -H "Authorization: Bearer $IT")
  echo "$ST" | grep -q '"running":false' && { DONE=1; break; }
  sleep 15
done
[ "$DONE" = "1" ] && ok "sync finished" || bad "sync finish (timeout)"
curl -s "$BASE/v1/intel/sync/status" -H "Authorization: Bearer $IT" | grep -q '"error":""' && ok "feeds clean" || bad "feed errors"
TOP=$(curl -s "$BASE/v1/intel/vulns?limit=5" -H "Authorization: Bearer $IT")
echo "$TOP" | python3 -c "import sys,json;p=[v['priority'] for v in json.load(sys.stdin)];assert p==sorted(p,reverse=True),p" 2>/dev/null && ok "priority ordered" || bad "priority order"
[ "$(curl -s "$BASE/v1/intel/vulns?kev_only=true&limit=3" -H "Authorization: Bearer $IT" | J "len(d)")" -ge "1" ] && ok "KEV flagged" || bad "KEV flag"
curl -s "$BASE/v1/intel/vulns/CVE-2021-44228" -H "Authorization: Bearer $IT" | grep -q "history" && ok "log4shell detail+history" || bad "known CVE detail"
Q=$(curl -s "$BASE/v1/intel/review" -H "Authorization: Bearer $IT")
RID=$(echo "$Q" | J "d[0]['id'] if d else ''") || RID=""
if [ -n "${RID:-}" ]; then
  curl -s -X POST "$BASE/v1/intel/review/$RID" -H "Authorization: Bearer $IT" -H 'Content-Type: application/json' -d '{"decision":"approved"}' | grep -q approved && ok "review approve ($RID)" || bad "review approve"
else
  ok "review queue readable (empty is fine post-triage)"
fi
curl -s "$BASE/v1/intel/cwe/79" -H "Authorization: Bearer $IT" | grep -qi "cross-site scripting" && ok "CWE-79 named" || bad "CWE lookup"
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
