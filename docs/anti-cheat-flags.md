# Anti-Cheat Flags (NEW — folded in per your choice)

Static flags (`flag{...}` in image) fail: learners share them. We use per-session HMAC flags.

## Design
- At session launch, orchestrator generates `flag_seed = rand(16 bytes)` per session, stores only in Redis + Postgres (restricted column), never in image env readable by enumeration? Actually injected as env `FLAG_SEED` inside target, but app computes expected flag at runtime.
- Expected flag for objective `o`: `FLAG = "KW{" + hex(HMAC_SHA256(secret=FLAG_HMAC_SECRET + session_seed, msg=session_id + ":" + lab_version + ":" + o))[0:16] + "}"`
  - `FLAG_HMAC_SECRET` lives only in API/orchestrator, rotated per env.
  - Learner cannot forge without secret; each session's flags differ → sharing useless.
- Validation server-side only: `POST /v1/sessions/{id}/submissions {objectiveId, flag}` → constant-time compare, rate-limited (5/min), audit logged. Never log flag plaintext on failure? Log hash only.
- Target app validates same way via `packages/lab-sdk` (reads seed, recomputes) or calls back to orchestrator sidecar — SDK provided so authors never hand-roll crypto.

## Additional signals
- Attempt velocity + hint usage feed scoring (PLAN Phase 4) — rewards understanding.
- Plagiarism: identical evidence snippets across sessions flagged for instructor review.
- Assessment mode: flags rotate on reset; copy-paste of old flag fails.

## SDK contract (to build in Phase 4)
`lab_sdk.mint(objective_id, session_id, seed) / lab_sdk.verify(candidate, ...)` — constant-time, no plaintext storage.
