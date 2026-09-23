# Curated Third-Party Review (Phase 6)

Wrappers live in `labs/curated/`. Native curriculum always comes first; curated
targets supplement it and are badged third-party everywhere.

## License findings (checked 2026-09-23)

| Project | License | Source | Wrapping allowed? |
|---|---|---|---|
| OWASP Juice Shop | MIT (© Bjoern Kimminich & contributors 2014–2026) | github.com/juice-shop/juice-shop LICENSE | Yes, with copyright notice + attribution |
| OWASP crAPI | Apache-2.0 | github.com/OWASP/crapi LICENSE.md | Yes, with license + notices |

## Per-target checklist

| Gate | juice-shop@2026-08-11 | crAPI |
|---|---|---|
| Version + digest pinned | ✅ `bkimminich/juice-shop@sha256:73c53fbf…f36b75430e` | ⏳ queued (multi-image) |
| License review | ✅ MIT, attribution in wrapper | ✅ Apache-2.0 |
| Local security review | ✅ serves; sqlite/logs need writes (see exception) | ⏳ pending |
| Network isolation | ✅ internal net, no egress (validated) | ⏳ pending |
| Non-root | ✅ runs as 65532 | ⏳ pending |
| Read-only fs | ❌ exception: sqlite+seed data share one tree (see below) | ⏳ pending |
| Wrapper docs | ✅ `labs/curated/juice-shop/` | ⏳ pending |

## Documented exception: writable layer for Juice Shop

Juice Shop keeps its sqlite DB, seed data, ftp, uploads and logs under one
tree, so tmpfs mounts either shadow seed data or miss writers. The wrapper runs
it with a container-writable layer (`writableFs: true` + justification), keeping:
non-root user, internal network, CPU/mem/pid caps, dropped capabilities,
no-new-privileges, digest pin. State stays ephemeral — reset destroys the
container, same training semantics as read-only targets. First-party images keep
read-only; only curated wrappers with a written justification may opt out
(enforced in `policy.py` + validator).

## crAPI status: queued

crAPI is a multi-service compose project (web, api, identity, db, mailhog…).
Each service image must be individually pinned, reviewed and mapped before a
wrapper lands. The same checklist above applies; nothing runs until all gates
are green.
