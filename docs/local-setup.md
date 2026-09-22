# Local Setup

Prereqs: Node 20+, Python 3.12+, Docker + Compose plugin, openssl.

```bash
cp .env.example .env
# generate secret:
openssl rand -hex 32  # paste into FLAG_HMAC_SECRET
docker compose -f infra/local/docker-compose.yml up -d
npm install
npm run validate
```

Verified 2026-09-22: Docker 29.8.1 + Compose v5.5.1 — postgres:16-alpine + redis:7-alpine both healthy.

CI (`npm run validate`) checks manifests + contracts without DB.
