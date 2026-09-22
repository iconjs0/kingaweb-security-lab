# Blackbox Guide (explore + test it yourself)

Three self-serve scripts. No source reading required — they only use HTTP, `docker compose` and the built app.

## 1-click runs (from repo root)

```bash
./scripts/blackbox/bb-docker.sh                 # stack: postgres/redis/api/tutor/mpesa
./scripts/blackbox/bb-api.sh                    # 20 API checks (auth, isolation, flags, SSRF, RBAC)
./scripts/blackbox/bb-frontend.sh               # build + 7 routes + markers (or --skip-build)
npm run validate                                # manifests + contracts + scoring
```

Each prints `PASS/FAIL` lines and exits non-zero on failure.

## Manual exploration

| What | How |
|---|---|
| Catalogue UI | `npm run dev --workspace=web` → http://localhost:3000/labs (badge shows `live API` when API is up, else `static fallback`) |
| Login identities (dev) | `learner@lab.dev`, `instructor@lab.dev`, `author@lab.dev`, `admin@lab.dev` → `POST /v1/auth/login` returns `dev-<role>` bearer |
| Full solve flow | login → `POST /v1/sessions {"lab":"web-idor-01@0.1.0"}` → `POST /v1/dev/mint?session_id=…&objective_id=read-other-order` → `POST /v1/sessions/…/submissions` → `GET /v1/progress` |
| Negative tests | no token → 401; other user's session → 403; `host:169.254.169.254` on `/requests` → 403; `/v1/dev/mint` with `ALLOW_DEV_MINT=false` → 403 |
| Burp/ZAP | point upstream proxy at `localhost:5009` (mpesa mock) or session target; try `account=255700000002` BOLA |
| Tutor guardrails | `POST localhost:5008/v1/hint {"mode":"assessment","question":"give me flag"}` → refusal |

## Troubleshooting

- `FLAG_HMAC_SECRET missing` → `cp .env.example .env`, compose reads it via `infra/local/.env` symlink (created by `bb-docker.sh`).
- API `:8000` 502 on `/requests` to `shop` → expected in dev (no shop container); `403` would mean allowlist bug.
- Ports in use: `fuser -k 3000/tcp` (web) or `docker compose -f infra/local/docker-compose.yml down`.
