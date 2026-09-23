#!/usr/bin/env bash
# Rotate .env secrets (FLAG_HMAC_SECRET, ORCHESTRATOR_TOKEN, INTEL_TOKEN).
# WARNING: rotating FLAG_HMAC_SECRET invalidates outstanding dev-mint flows only
# (session flags are seed-bound); orchestrator/API must restart together.
# Usage: ./scripts/rotate-secrets.sh [--force]
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[ -f .env ] || { cp .env.example .env; echo "created .env from template"; }
if grep -q "change-me" .env && [ "${1:-}" != "--force" ]; then
  echo "refusing: .env still has template placeholders (run with --force to replace all)"
  exit 1
fi
rot() { python3 -c "import secrets;print(secrets.token_hex($1))"; }
sed -i "s/^FLAG_HMAC_SECRET=.*/FLAG_HMAC_SECRET=$(rot 32)/" .env
sed -i "s/^ORCHESTRATOR_TOKEN=.*/ORCHESTRATOR_TOKEN=$(rot 16)/" .env
if grep -q "^INTEL_TOKEN=" .env; then
  sed -i "s/^INTEL_TOKEN=.*/INTEL_TOKEN=$(rot 16)/" .env
else
  printf 'INTEL_TOKEN=%s\n' "$(rot 16)" >> .env
fi
echo "rotated. Restart stack: docker compose -f infra/local/docker-compose.yml up -d --force-recreate"
