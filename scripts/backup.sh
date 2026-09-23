#!/usr/bin/env bash
# Backup: postgres dump + sqlite DBs + labs/manifests snapshot.
# Usage: ./scripts/backup.sh [outdir]  |  ./scripts/backup.sh --restore <file>
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ "${1:-}" = "--restore" ]; then
  f="${2:?usage: backup.sh --restore <file>}"
  rm -rf /tmp/opencode-restore && mkdir -p /tmp/opencode-restore
  tar -xzf "$f" -C /tmp/opencode-restore
  echo "extracted to /tmp/opencode-restore — restore targets:"
  echo "  postgres: psql \$POSTGRES_URL < /tmp/opencode-restore/postgres.sql"
  echo "  intel.db: cp /tmp/opencode-restore/intel.db <intel-data-volume>/intel.db (stack down)"
  echo "DR drill: restore to a scratch host, run bb-docker.sh + bb-api.sh, compare."
  exit 0
fi
OUT="${1:-/tmp/opencode-backups}"
mkdir -p "$OUT"
TS=$(date +%Y%m%d-%H%M%S)
STAGE="/tmp/opencode-backup-$TS"
mkdir -p "$STAGE"
docker compose -f infra/local/docker-compose.yml exec -T postgres pg_dump -U lab lab > "$STAGE/postgres.sql" 2>/dev/null \
  || echo "-- pg_dump unavailable (stack down?)" > "$STAGE/postgres.sql"
docker cp local-intel-1:/data/intel.db "$STAGE/intel.db" 2>/dev/null || echo "no intel db yet"
cp -r labs "$STAGE/labs-manifests"
tar -czf "$OUT/lab-backup-$TS.tgz" -C "$STAGE" .
rm -rf "$STAGE"
echo "backup: $OUT/lab-backup-$TS.tgz"
ls -la "$OUT" | tail -n 3
