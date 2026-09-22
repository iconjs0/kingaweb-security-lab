# CTF Competition Mode (Docker-backed)

Reuses sessions/scoring — no separate infra.

## Model
- `Competition`: id, name, lab_set [(slug, version)], startsAt/endsAt, teamMode (solo|team≤4), scoring `dynamic` (default), private leaderboard.
- `Enrollment`: team ↔ competition. Each solve still launches an isolated session (per-member session, same flag_seed scheme → sharing useless across teams).
- Dynamic scoring (decay): `points = max(floor, base * (0.9 ^ solves_before_you))`. First blood bonus +10%. Hint cost deducted. Remediation bonus counts (rewards understanding, per PLAN Phase 4).
- Freeze: last 15 min leaderboard frozen; audit immutable; flag rotation on reset.

## API (added to `openapi.v1.json`)
- `POST /v1/competitions` (admin/instructor), `POST /v1/competitions/{id}/join`
- `GET /v1/competitions/{id}/leaderboard` (frozen-aware)
- Solves go through existing `POST /v1/sessions/{id}/submissions` with `competitionId` — no new flag path.

## Anti-cheat tie-in
Per-session HMAC flags (see `anti-cheat-flags.md`) make cross-team sharing fail. Velocity checks: >5 submits/min → cooldown. Identical evidence across teams → instructor review queue.

## Implementation
`packages/lab-sdk/scoring.py`: pure functions `dynamic_points()`, `score_solve()` — unit-tested, no DB/docker needed. Orchestrator enforces one live session per (user, competition, lab).
