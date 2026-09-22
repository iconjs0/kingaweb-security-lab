# Threat Model (Phase 0, STRIDE-lite)

## Trust boundaries
1. Learner browser → API
2. API → Orchestrator (mTLS/token, narrow schema)
3. Orchestrator → Docker/K8s
4. Session container → (deny by default) internet / host / other sessions
5. HTTP console → target (allowlist ports/hosts only)

## Key threats & mitigations
| Threat | Mitigation |
|---|---|
| Container escape → host | non-root, ro-fs, seccomp/apparmor, no docker.sock in API, resource limits |
| Cross-session access | per-session network, random creds/ports, flag HMAC seed per session |
| SSRF via console/lab | console allowlists assigned target only; labs get mock internal services, no real egress |
| Flag sharing / cheating | per-session HMAC flags, server-side check, attempt rate-limit, plagiarism signals (see anti-cheat doc) |
| Malicious manifest (author) | JSON-schema validation, digest pin, signature, review gate, no privileged flags |
| Resource exhaustion | CPU/mem/pids/disk quotas, global concurrent-session cap, lease reaper |
| Secrets leak | .env never committed, orchestrator-only secrets, rotation runbook |
| Upstream image trojan | digest pin + Trivy scan + cosign verify + license review |
| Audit tamper | append-only audit table, no UPDATE/DELETE grants to app role |

## Out of scope (must not build)
Real credentials, PII, malware, phishing infra, open proxy, unrestricted exec.

## Isolation tests (Phase 3 gates)
- cross-session fetch denied
- host metadata (169.254.169.254) denied
- egress denied by default
- manifest with `privileged:true` rejected
- expired session containers gone within 5 min
