# Standards (coding, testing, content)

- TS strict + Python 3.12 + Ruff + Pydantic v2; conventional commits; PR template with security checklist.
- Tests required: unit (perms, scoring, validators), contract, isolation, golden vuln/fixed, a11y.
- Content review: author ≠ reviewer; OWASP/CWE mapping checked; no real secrets; image pinned+scanned+signed.
- Branches: `main` protected (CI + 1 review). `feat/*`, `labs/*`.
