#!/usr/bin/env bash
# Blackbox: curated wrapper. Launch Juice Shop, verify serving+isolation, destroy.
# Usage: ./scripts/blackbox/bb-curated.sh [base_url]
# Slow (~90s: upstream boot). Requires: stack up + image pulled (see docs/curated-review.md).
set -u
BASE="${1:-http://localhost:8000}"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }
J() { python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }

echo "== curated blackbox @ $BASE =="
T=$(curl -s -X POST "$BASE/v1/auth/login" -H 'Content-Type: application/json' -d '{"email":"learner@lab.dev"}' | J "d['token']") || T=""
L=$(curl -s -X POST "$BASE/v1/sessions" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d '{"lab":"curated-juice-shop@0.1.0"}')
S=$(echo "$L" | J "d.get('id','')"); P=$(echo "$L" | J "d['targets'][0]['port'] if d.get('targets') else ''") || true
echo "$L" | grep -q '"provisioned":true' && ok "wrapper provisioned ($S)" || { bad "provision" "$L"; echo "== $PASS passed, $FAIL failed =="; exit 1; }
curl -s --max-time 10 "http://127.0.0.1:$P/" | grep -qi "juice" && ok "shop serves via relay" || bad "shop serving"
curl -s --max-time 10 "http://127.0.0.1:$P/rest/user/whoami" | grep -q '"user"' && ok "shop API responds" || bad "shop API"
[ "$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/v1/sessions/$S/submissions" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d '{"objective_id":"scoreboard-found","flag":"KW{x}"}')" = "422" ] && ok "evidence-only (no auto flags)" || bad "evidence-only"
F=$(python3 -c "import json;print(json.dumps({k:f'substantive {k} content here' for k in ['title','description','evidence','impact','cwe','remediation','retest']}))")
curl -s -X POST "$BASE/v1/sessions/$S/findings" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' -d "$F" | grep -q '"id"' && ok "evidence recorded as finding" || bad "finding flow"
docker inspect "kw-$S-juiceshop" --format '{{.Config.User}} {{.HostConfig.ReadonlyRootfs}}' | grep -q "65532" && ok "non-root container" || bad "non-root"
NET=$(docker inspect "kw-$S-juiceshop" --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}')
docker network inspect "$NET" --format '{{.Internal}}' | grep -q true && ok "internal session net" || bad "internal net"
curl -s -X DELETE "$BASE/v1/sessions/$S" -H "Authorization: Bearer $T" | grep -q destroyed && ok "destroyed" || bad "destroy"
sleep 3
docker network ls --format "{{.Name}}" | grep -q "kw-$S" && bad "leftovers" || ok "no leftovers"
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
