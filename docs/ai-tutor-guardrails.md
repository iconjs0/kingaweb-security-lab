# AI Tutor Guardrails (no solution leak)

Goal: helpful hints without killing challenge/assessment integrity.

## Policy by mode (enforced server-side in `services/tutor/`, never in browser)
| Mode | Tutor may | Tutor must not |
|---|---|---|
| guided | explain concept, next-step nudge (hint level ≤ unlocked), remediation help | reveal flag / full payload |
| challenge | concept + methodology only (e.g. "test IDOR via Repeater"), point to docs | give exact ID/parameter/payload |
| assessment | morale + time management + tool docs | any lab-specific hint; respond with canned refusal + timer |
| instructor-demo | full walkthrough allowed | — |

## Enforcement
1. Tutor receives only: `mode, lab_slug/version, unlocked_hint_level, objective_ids (no flags), learner question`. Never `flag_seed`, never expected flag, never other sessions.
2. Output filter (regex + denylist): blocks `KW{`, `flag`, exact payload patterns from manifest `solutions:` (solutions stored separately, tutor has no read grant).
3. Rate limit 10/hr (challenge), 0/hr lab-specific in assessment. All Q/A audit-logged, excludable from evidence export.
4. No external LLM in dev: stub returns level-appropriate canned hint from manifest. Prod: self-hosted or allowlisted API, no training on learner data, PII redacted.

See `services/tutor/app.py` (stub, runs in compose, no internet needed).
