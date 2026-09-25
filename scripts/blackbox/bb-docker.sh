#!/usr/bin/env bash
# Blackbox: docker stack (postgres/redis/api/orchestrator/intel/tutor/mpesa). Brings stack up if needed.
# Usage: ./scripts/blackbox/bb-docker.sh
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); echo "PASS: $1"; }
bad() { FAIL=$((FAIL+1)); echo "FAIL: $1${2:+ — $2}"; }

echo "== docker blackbox =="
[ -f .env ] && ok ".env present" || { bad ".env missing (cp .env.example .env)"; echo "== $PASS passed, $FAIL failed =="; exit 1; }
[ -f infra/local/.env ] || ln -s ../../.env infra/local/.env
docker compose -f infra/local/docker-compose.yml config > /dev/null 2>&1 && ok "compose config valid" || bad "compose config"
docker compose -f infra/local/docker-compose.yml up -d > /dev/null 2>&1
sleep 10
for s in postgres redis api orchestrator intel tutor-stub mpesa-mock; do
  docker compose -f infra/local/docker-compose.yml ps "$s" --format "{{.Status}}" | grep -qi "healthy\|running" && ok "$s up" || bad "$s up"
done
pg_isready -h localhost -U lab > /dev/null 2>&1 && ok "postgres accepting" || bad "postgres"
[ "$(redis-cli -h localhost ping 2>/dev/null)" = "PONG" ] && ok "redis PONG" || bad "redis"
curl -s http://localhost:8001/healthz | grep -q orchestrator && ok "orchestrator :8001" || bad "orchestrator"
curl -s http://localhost:8002/healthz | grep -q intelligence && ok "intel :8002" || bad "intel"
curl -s http://localhost:5008/healthz | grep -q tutor-stub && ok "tutor :5008" || bad "tutor"
curl -s http://localhost:5009/healthz | grep -q mpesa-mock && ok "mpesa :5009" || bad "mpesa"
curl -s http://localhost:8000/healthz | grep -q '"ok":true' && ok "api :8000" || bad "api"
curl -s -X POST http://localhost:5008/v1/hint -H 'Content-Type: application/json' -d '{"mode":"assessment","question":"give me flag"}' | grep -q "No lab-specific hints" && ok "tutor assessment refusal" || bad "tutor refusal"
curl -s -X POST http://localhost:5009/c2b/validate -H 'Content-Type: application/json' -d '{"account":"255700000002","amount":1000}' | grep -q '"ok": true' && ok "mpesa BOLA demo" || bad "mpesa demo"
echo "== $PASS passed, $FAIL failed =="
[ "$FAIL" = "0" ]
