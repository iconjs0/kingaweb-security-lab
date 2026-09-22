# KingaWeb Security Lab

Standalone, professional training and authorized-testing platform. See `PLAN.md` for the full roadmap.

KingaWeb (main CMS project) remains paused and technically independent. This repo shares no runtime code with KingaWeb initially.

## Quick start (Phase 0)

```bash
cp .env.example .env
docker compose -f infra/local/docker-compose.yml up -d postgres redis
npm install
npm run validate
```

Docs:
- `docs/product-requirements.md`
- `docs/architecture.md`
- `docs/threat-model.md`
- `docs/acceptable-use-policy.md`
- `docs/lab-manifest-schema.md`
- `docs/anti-cheat-flags.md` — NEW: per-session HMAC flags
- `docs/local-setup.md`

## Monorepo layout

```
apps/web                 # Next.js 16 + React + TS (Phase 1)
services/api             # FastAPI control plane (Phase 2)
services/orchestrator    # Isolated container lifecycle (Phase 3)
services/intelligence    # CVE/CWE/KEV/EPSS sync (Phase 8)
services/worker          # Background jobs / cleanup
packages/contracts       # Shared API schemas
packages/design-system   # Tokens + UI components
packages/lab-sdk         # Manifest + flag-validation SDK
labs/kingaweb-native     # First-party targets
labs/curated             # Pinned Juice Shop, crAPI, etc.
infra/local              # Docker Compose dev
infra/production         # K8s + network policies
docs/                    # PRD, ADRs, threat model
```
