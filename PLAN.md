# KingaWeb Security Lab — Complete Implementation Roadmap

## Summary

Build a standalone, professional training and authorized-testing platform from scratch at:

`/home/icon_js0/Documents/PROJECTS/kingaweb-security-lab`

KingaWeb remains paused and technically independent. The lab will support personal learners and teams through guided lessons, unguided challenges and scored assessments. Each practice session launches an isolated, temporary vulnerable environment that can be tested through Burp Suite, OWASP ZAP, curl and a safe browser-based HTTP console.

Initial coverage will focus on:

- OWASP Web Top 10
- OWASP API Security Top 10
- CWE mappings
- CVSS severity
- CISA KEV and EPSS prioritization
- Selected current CVE reproduction labs

The platform must remain an authorized learning environment—not a general-purpose attack platform.

## Architecture and Product Design

### Technical stack

Use an npm-workspace monorepo:

```text
kingaweb-security-lab/
├── apps/
│   └── web/                 # Next.js, React, TypeScript
├── services/
│   ├── api/                 # FastAPI control plane
│   ├── orchestrator/        # Isolated container lifecycle service
│   ├── intelligence/        # CVE/CWE/OWASP/KEV/EPSS synchronization
│   └── worker/              # Background jobs and cleanup
├── packages/
│   ├── contracts/           # Shared API schemas
│   ├── design-system/       # Tokens and reusable UI components
│   └── lab-sdk/             # Lab manifest and flag-validation SDK
├── labs/
│   ├── kingaweb-native/     # Original training targets
│   └── curated/             # Pinned Juice Shop, crAPI and similar targets
├── infra/
│   ├── local/               # Docker Compose environment
│   └── production/          # Kubernetes and network policies
└── docs/                    # Architecture, threat model and curriculum
```

Core technology:

- Next.js 16, React and TypeScript
- FastAPI, Python and Pydantic
- PostgreSQL for durable state
- Redis for queues, leases and short-lived sessions
- Docker locally; Kubernetes for production
- S3-compatible storage for evidence and reports
- OpenTelemetry-compatible logs, metrics and traces
- OIDC authentication in production; seeded local identities during development

### Security and isolation model

- The API must never receive direct Docker socket access.
- A narrow orchestrator service controls only allowlisted, digest-pinned lab images.
- Every session gets its own network, containers, credentials, flag seed and expiry.
- Containers run non-root with CPU, memory, process and storage limits.
- Filesystems are read-only except explicitly mounted temporary directories.
- Outbound internet access is disabled unless a scenario explicitly requires an allowlisted mock dependency.
- Sessions expire after 60 minutes by default, with a controlled extension option.
- Reset destroys and recreates the environment instead of attempting partial cleanup.
- The web HTTP console may contact only the learner’s assigned target, on manifest-approved ports, with strict timeouts and response-size limits.
- No real credentials, personal data, malware, phishing infrastructure or uncontrolled command execution may exist inside lab content.

### User experience and visual system

Adopt a technical editorial design rather than a generic neon “hacker” dashboard:

- Deep ink background, warm off-white reading surfaces and restrained signal green, amber and red.
- Space Grotesk for interface typography and IBM Plex Mono for evidence, requests and terminal-style content.
- Asymmetric editorial workspace with a compact navigation rail and resizable evidence panels.
- Nested machined-panel construction for major cards instead of generic floating cards.
- Thin-line Remix icons; no thick default icon library.
- Motion uses restrained transform/opacity transitions and respects reduced-motion settings.
- Desktop-first workspace for penetration-testing tools, with responsive lesson reading and progress views for mobile.
- WCAG 2.2 AA contrast, keyboard navigation, visible focus and accessible status announcements.

Primary interfaces:

- Public introduction and platform documentation
- Lab catalogue with OWASP category, difficulty and tool filters
- Lab detail and learning objectives
- Active workspace: brief, topology, target access, notes, hints, HTTP console and evidence
- Guided lesson mode
- Unguided challenge mode
- Timed assessment mode
- Learner progress and skill matrix
- Team classroom, assignments and instructor review
- Content and infrastructure administration
- Vulnerability-intelligence review queue

## Delivery Roadmap

### Phase 0 — Product and security foundation

- Initialize Git, repository conventions, environment templates and protected branches.
- Write the product requirements, architecture decisions, threat model and acceptable-use policy.
- Define learner, instructor, content-author and platform-admin roles.
- Define the lab manifest schema, lifecycle states and versioning rules.
- Establish coding, testing, accessibility and content-review standards.

Exit criteria:

- Architecture and threat model approved.
- Local setup documented.
- CI validates an otherwise minimal monorepo.

### Phase 1 — Design system and application shell

- Create the visual tokens, typography, spacing, status colors and motion system.
- Build public landing, authentication, catalogue shell and application navigation.
- Create the session-workspace layout with brief, evidence and tools panels.
- Establish reusable tables, filters, dialogs, command blocks, findings and risk components.
- Add light/dark accessibility testing, with the dark editorial theme as the primary presentation.

Exit criteria:

- Responsive application shell matches the visual system.
- Keyboard navigation and WCAG AA checks pass.
- Storybook or an equivalent component gallery documents every shared component.

### Phase 2 — Control-plane backend

Implement:

- Authentication and RBAC
- Users, teams and memberships
- Lab catalogue and versioned content
- Enrolments, sessions and session events
- Objectives, hints, flags and submissions
- Progress, achievements and assessments
- Evidence notes and exported reports
- Immutable security-sensitive audit records

Initial public interfaces:

- `GET /v1/labs`
- `GET /v1/labs/{slug}`
- `POST /v1/sessions`
- `GET /v1/sessions/{id}`
- `POST /v1/sessions/{id}/extend`
- `POST /v1/sessions/{id}/reset`
- `DELETE /v1/sessions/{id}`
- `POST /v1/sessions/{id}/submissions`
- `POST /v1/sessions/{id}/requests`
- `GET /v1/progress`
- Team assignment and instructor-review endpoints

All state-changing endpoints require authorization, audit metadata and idempotency where retries are expected.

### Phase 3 — Secure lab orchestrator

- Build the isolated orchestration service.
- Validate signed, versioned manifests before launch.
- Pull only allowlisted images pinned by digest.
- Create per-session network, secrets and containers.
- Run readiness probes before returning target access.
- Issue short-lived target URLs or local connection details.
- Enforce expiry, reset and cleanup through renewable leases.
- Reconcile abandoned containers after crashes or restarts.
- Record lifecycle events without storing exploit payloads unnecessarily.

Exit criteria:

- Two learners can run the same lab without sharing state.
- Expired sessions are destroyed automatically.
- Targets cannot reach the host, control plane, other sessions or public internet.
- Container escape, resource-exhaustion and SSRF-oriented isolation tests pass.

### Phase 4 — Learning and assessment engine

Every lab manifest contains:

- Stable ID and semantic version
- Title, summary and difficulty
- OWASP Web/API category and CWE mapping
- Learning objectives and prerequisites
- Estimated completion time
- Architecture/topology description
- Image digests, ports and health checks
- Guided steps, optional hints and remediation
- Server-side flag validators
- Reset strategy and expected evidence
- Author, reviewer and change history

Learning modes:

- Guided: explanations, checkpoints and staged hints
- Challenge: objectives without procedural instructions
- Assessment: timed, limited hints, immutable scoring
- Instructor demonstration: resettable environment with walkthrough controls

Scoring combines completed objectives, hint usage, attempts and time. It must reward understanding and remediation, not just flag capture.

### Phase 5 — First-party Web and API curriculum

Wave 1 — foundations:

- HTTP request/response analysis
- Cookies, sessions and browser security
- TLS, headers, CORS and CSP
- Authentication and authorization boundaries
- Evidence collection and professional reporting

Wave 2 — OWASP Web:

- Broken access control and IDOR
- Authentication and session failures
- SQL, command and template injection
- Reflected, stored and DOM XSS
- CSRF
- SSRF using internal mock services
- Path traversal and controlled file inclusion
- Unsafe file uploads
- Security misconfiguration
- Cryptographic and secret-management failures
- Vulnerable/outdated component identification
- Logging, monitoring and exception-handling failures

Wave 3 — OWASP API:

- BOLA and object-property authorization
- Broken function-level authorization
- Unrestricted resource consumption
- Unsafe API consumption
- Mass assignment
- Improper inventory management
- Rate-limit and business-flow abuse
- JWT and API-key mistakes
- GraphQL authorization and query-cost controls

Each topic receives at least:

- One guided beginner lab
- One intermediate challenge
- One remediation exercise
- One automated regression test
- A defensive explanation and reporting template

### Phase 6 — Curated third-party targets

Integrate selected projects such as OWASP Juice Shop and OWASP crAPI only after:

- License review
- Image digest pinning
- Local security review
- Network-isolation validation
- Version compatibility testing
- KingaWeb wrapper documentation
- Explicit distinction between KingaWeb-native and third-party content

Third-party targets supplement rather than replace the original curriculum.

### Phase 7 — Safe web console and evidence workspace

- Provide a structured HTTP request builder rather than an unrestricted shell.
- Support methods, paths, headers and bodies within the assigned target boundary.
- Display formatted requests, responses, timing and redirect chains.
- Allow redacted evidence snippets to be saved to learner notes.
- Provide copyable connection instructions for Burp, ZAP and curl.
- Add finding templates: description, evidence, impact, CWE/OWASP mapping, remediation and retest.
- Export a professional PDF/HTML assessment report.

### Phase 8 — Vulnerability intelligence

Synchronize:

- NVD CVE and CVSS records
- CWE taxonomy
- CISA Known Exploited Vulnerabilities
- FIRST EPSS probability
- OWASP Web and API category versions

Behavior:

- Preserve every upstream severity revision rather than overwriting history.
- Calculate an effective priority using CVSS, KEV, EPSS and lab relevance.
- Place new or changed vulnerabilities into a human-review queue.
- Never automatically deploy vulnerable images from a feed.
- Permit reviewed CVEs to become versioned learning modules.
- Notify administrators when an existing lab’s CVE severity or exploitation status changes.
- Show source, publication date, last modification, previous severity and reason for change.

### Phase 9 — Teams and professional learning

- Team workspaces and invitations
- Instructor-created learning paths
- Assignments and deadlines
- Cohort progress dashboards
- Private leaderboards
- Evidence-based instructor review
- Completion certificates with verifiable identifiers
- Organisation-level audit history
- Data-retention and export controls

### Phase 10 — Production hardening and launch

- Kubernetes namespaces or equivalent isolation boundaries
- Default-deny network policies
- Wildcard lab-domain routing with short-lived access tokens
- Rate limits, quotas and abuse detection
- Backups and disaster-recovery testing
- Dependency scanning, SBOM generation and signed images
- Secrets management and automated rotation
- Central metrics, tracing and alerting
- External penetration test before public access
- Staged launch: personal alpha → invited teams → private beta → controlled public release

## Test Strategy and Acceptance

Required automated coverage:

- Unit tests for permissions, scoring, manifests and validators
- API contract and tenant-isolation tests
- Real container lifecycle integration tests
- Browser end-to-end tests for catalogue, launch, reset, submission and reports
- Golden tests for every vulnerable and remediated state
- Isolation tests for cross-session access, host access, internet egress and resource abuse
- Security tests for SSRF, traversal, unsafe redirects and malicious manifests
- Accessibility and keyboard-navigation tests
- Responsive visual-regression tests
- Load tests for concurrent session launches and cleanup
- Upgrade tests for database and lab-manifest migrations

A lab is publishable only when:

- Its vulnerability and remediation are both reproducible.
- No unintended solution path or real external dependency exists.
- Isolation and cleanup tests pass.
- OWASP/CWE/CVE mappings are reviewed.
- Hints, evidence and reporting instructions are complete.
- The lab image is pinned, scanned and signed.

## Assumptions and Defaults

- KingaWeb development is paused; the two repositories share no runtime code initially.
- Integration with KingaWeb may later use a versioned API, never direct database coupling.
- English is the initial interface and curriculum language; Kiswahili localization comes later.
- Local development uses Docker; the Docker Compose plugin must be installed during bootstrap.
- Sessions expire after 60 minutes unless the manifest sets a lower limit.
- External tool access and the safe web console are included; a browser-based attack desktop is deferred.
- Web and API security come first. Network, cloud, Active Directory, mobile and reverse-engineering tracks are future expansions.
- The first release is private-first. Public availability requires the Phase 10 security gates.
