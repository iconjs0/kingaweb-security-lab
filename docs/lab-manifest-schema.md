# Lab Manifest Schema (v0.1 draft)

All manifests: `labs/<track>/<slug>/lab.yaml`, semver immutable. Signed before publish (Phase 3).

```yaml
apiVersion: lab.kingaweb.io/v1
kind: Lab
metadata:
  id: web-idor-01
  slug: web-idor-01
  version: 0.1.0
  title: "Broken Access Control: IDOR"
  summary: "Enumerate order IDs and enforce server-side authorization."
  difficulty: beginner # beginner | intermediate | advanced
  timeMinutes: 45
  author: "platform"
  reviewer: "tbd"
tracks: [web]
owasp: { web: ["A01:2021-Broken Access Control"], api: [] }
cwe: [639]
prerequisites: [http-foundations]
topology: "single container: vulnerable shop + mock auth"
targets:
  - name: shop
    image: "ghcr.io/kingaweb/lab-idor@sha256:PIN_ME"
    ports: [8080]
    healthcheck: { path: /healthz, port: 8080, timeoutSeconds: 5 }
    resources: { cpu: "0.5", memory: "256Mi", pids: 64, diskMb: 512 }
    readonlyFs: true
network: { egress: deny, allowMocks: [] }
session: { ttlMinutes: 60, maxExtendOnceMinutes: 30 }
objectives:
  - id: read-other-order
    title: "Read another user's order via IDOR"
    flag: { validator: hmac, objectiveId: read-other-order } # server-computed, never stored plaintext
    evidenceRequired: true
hints:
  - { level: 1, text: "Compare your order URL with another...", cost: 5 }
  - { level: 2, text: "Intercept with Burp Repeater...", cost: 15 }
guidedSteps: [...]
remediation: { summary: "Enforce server-side authz...", retest: "Repeat request → expect 403" }
resetStrategy: recreate
```

## Validation rules
- `id/slug` stable; version semver; no `latest` tags — digest required (`@sha256:`)
- ports allowlisted; no `privileged`, no `hostNetwork`, no `mountDockerSock`
- `ttlMinutes <= 60`
- every objective has server-side validator (hmac | regex | http-check), never client-side flag string
- OWASP/CWE required; change history required to publish

## Lifecycle states
`draft → in_review → published → deprecated → archived`. Sessions pin (slug, version). Reset = destroy+recreate.
