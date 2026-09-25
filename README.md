# KingaWeb Security Lab

Authorized web/API security training: guided lessons, challenges, assessments.
Every session launches an **isolated, temporary vulnerable environment** —
per-session network, credentials, flag seed and expiry — testable via Burp/ZAP,
curl and a safe in-browser console. KingaWeb (CMS) stays paused and independent.

## Quick start

```bash
cp .env.example .env
docker compose -f infra/local/docker-compose.yml up -d   # postgres, redis, api, orchestrator, intel, mocks
./scripts/build-lab-images.sh                            # 19 target images
npm install && npm run validate                          # manifests + contracts + scoring
./scripts/blackbox/bb-docker.sh && ./scripts/blackbox/bb-api.sh   # prove it
```

Full self-serve verification: `docs/blackbox-guide.md` (10 scripts, all HTTP-only).

## Lab catalogue (19)

| Track | Labs |
|---|---|
| Foundations | http-01, cookies-01, headers-01, authz-01, report-01 |
| OWASP Web | idor-01, sqli-01, xss-01, ssrf-01, csrf-01, traversal-01, upload-01, crypto-01 |
| OWASP API | bola-01, mass-01, jwt-01, ratelimit-01 |
| TZ-local | mpesa-bola-01 (M-Pesa mock, Kiswahili i18n) |
| Curated | juice-shop (pinned digest, evidence-graded) |

Every lab: versioned manifest, staged hints with costs, guided/checkpoint flow,
remediation + retest, blue-team detection twin, golden vuln/fixed regression.

## Architecture

```
browser → apps/web (Next.js) ─┐
                              ├→ services/api (FastAPI: auth/RBAC, sessions, flags, scoring, audit)
learner tools → orchestrator loopback relays → per-session internal nets (targets)
services/intelligence (KEV/EPSS/NVD → priority + review queue, never auto-deploys)
```

Security highlights: API never touches the Docker socket (sole orchestrator
holds it); per-session HMAC-seed flags (sharing fails); allowlisted
digest-pinned images; non-root read-only capped containers; no egress;
rate limits + quotas; immutable audit; prod overlay kills all dev escapes.

## Layout

```
apps/web                 # Next.js 16: catalogue, workspace, teams, intel, gallery
services/api             # control plane (FastAPI)
services/orchestrator    # isolated lifecycle (sole Docker access)
services/intelligence    # vuln intel (FastAPI + sqlite)
services/worker          # reserved (reaper lives in orchestrator today)
packages/contracts       # OpenAPI stub · design-system: tokens/components · lab-sdk: flags/validators
labs/kingaweb-native     # 18 first-party labs (app + manifest + blue twin + tests)
labs/curated             # pinned third-party wrappers (juice-shop live, crAPI queued)
labs/mocks               # mpesa, internal-meta
infra/local              # compose dev · infra/production: prod overlay + launch gates
scripts/                 # build-lab-images, backup, rotate-secrets, check-env, sbom, verify-digests
docs/                    # PRD, ADRs, threat model, AUP, schema v0.3, learning modes, guides
```

## Status: all PLAN phases built (71 commits)

Phase 0 foundation → 1 shell → 2 API → 3 orchestrator → 4 learning engine →
5 curriculum (Waves 1–3) → 6 curated → 7 evidence → 8 intel → 9 classroom → 10 hardening.
Remaining before public: `docs/launch-gates.md` (pentest, digests, OIDC, signing).
