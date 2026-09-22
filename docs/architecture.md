# Architecture (Phase 0)

## Control plane vs data plane
- `services/api` (FastAPI): auth/RBAC, catalogue, sessions, scoring. No Docker socket.
- `services/orchestrator`: sole Docker/K8s caller. Allowlisted digest-pinned images only, signed manifest verification.
- `services/worker`: expiry, cleanup reconciliation, report rendering.
- `services/intelligence`: NVD/CWE/KEV/EPSS pull → review queue.
- `apps/web`: Next.js; HTTP console proxies via API (never direct to target from browser except via short-lived token URL).

## Data
- Postgres: durable (users, labs, sessions, submissions, audit).
- Redis: leases, idempotency keys, short-lived target tokens.
- S3-compatible: evidence + reports.

## Decisions (ADRs)
- ADR-001: npm workspaces + Python services (JS for UI velocity, Python for security tooling ecosystem).
- ADR-002: Orchestrator split from API — blast-radius reduction; API compromise ≠ host compromise.
- ADR-003: Per-session network + HMAC flag seed — prevents cross-learner flag sharing.
- ADR-004: Structured HTTP console, no shell — SSRF containment.
- ADR-005: Manifest semver immutable — reproducible scoring + safe rollback.
- ADR-006: Intel never auto-deploys — supply-chain safety.

## Production (Phase 10 preview)
K8s namespaces per tenant cohort, default-deny NetworkPolicy, wildcard lab-domain + short-lived tokens, SBOM + cosign, external pentest gate.
