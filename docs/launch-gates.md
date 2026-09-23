# Launch Gates (Phase 10)

Staged release. No stage advances with failing blackbox or open review items.

## Gates per stage

| Stage | Who | Entry requirements |
|---|---|---|
| personal alpha | you | all bb-*.sh green on this host; `check-env.sh` passes |
| invited teams | +5 users | prod overlay on; `verify-digests.sh` clean OR documented dev-digest exceptions; backup+restore drill done; rate limits observed (bb-prod) |
| private beta | +50 users | external pentest findings closed; SBOM filed (`sbom.sh`); secrets rotated post-test; abuse alerts (metrics submit_fails) reviewed |
| controlled public | open signup | OIDC enforced (no dev tokens); signed images (cosign) + K8s policies per `infra/production/`; 30-day incident drill |

## Hard requirements (any stage beyond alpha)

1. `ALLOW_DEV_MINT=false`, `ALLOW_UNSIGNED_MANIFESTS=false`, `ALLOW_DEV_DIGESTS=false` (prod overlay enforces).
2. No `change-me` secrets (`check-env.sh`).
3. Backups restorable (documented drill output).
4. Pentest before public (report filed; retest closed).

## K8s notes (when leaving compose)

`infra/production/` holds the compose prod overlay today. K8s migration keeps the
same contracts: orchestrator alone mounts the runtime socket (or uses a node-limited
CRI proxy), default-deny NetworkPolicy per session namespace, short-lived ingress
tokens instead of relay ports. See PLAN Phase 10.
