# Product Requirements (Phase 0)

## 1. Goal
Authorized learning environment for OWASP Web Top 10 + API Top 10. Guided lessons, unguided challenges, scored assessments. Each session = isolated, temporary vulnerable environment testable via Burp/ZAP/curl/safe browser HTTP console.

Not a general-purpose attack platform.

## 2. Users & roles
See `docs/roles.md`. Learner, instructor, content-author, platform-admin.

## 3. Core journeys
1. Browse catalogue (filter: OWASP category, difficulty, tool) → lab detail → Launch → isolated target in <60s
2. Guided mode: steps + checkpoints + staged hints → submit flags → remediation exercise → report export
3. Challenge mode: objectives only, no procedure
4. Assessment mode: timed, limited hints, immutable scoring
5. Instructor: create path → assign → review evidence → certify

## 4. Functional requirements
- Catalogue versioning: labs immutable by (slug, semver); sessions pin version
- Sessions: 60 min default TTL (manifest may lower), extend once, reset = destroy+recreate
- Flags: per-session HMAC (see `anti-cheat-flags.md`), server-side validation only
- Scoring: objectives + hint penalty + attempts + time; rewards remediation, not just capture
- Evidence: notes + redacted snippets + finding templates → PDF/HTML export
- HTTP console: structured builder, target-allowlisted, timeout + size limits
- Intel: NVD/CWE/KEV/EPSS sync → human review queue, never auto-deploy images

## 5. Non-functional
- Isolation: per-session network, non-root, CPU/mem/pid/disk limits, ro-fs, no egress by default
- A11y: WCAG 2.2 AA, keyboard, focus, reduced-motion
- I18n: English first; Kiswahili later
- Observability: OTel logs/metrics/traces; audit immutable
- Perf: p95 launch <60s local; 50 concurrent launches without cleanup leak
