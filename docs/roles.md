# Roles (RBAC)

- `learner`: browse, launch own sessions, submit, notes, reports
- `instructor`: + create paths/assignments, review cohort evidence, issue certs
- `content-author`: + draft labs, submit for review; cannot publish
- `platform-admin`: + publish labs, manage intel queue, quotas, audit export

Enforced server-side per endpoint + per object (team membership, session owner). Seeded local identities in dev; OIDC in prod.
