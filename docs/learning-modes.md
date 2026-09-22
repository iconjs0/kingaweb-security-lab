# Learning Modes & Scoring (Phase 4)

Launch-time `mode` (default `guided`):

| Mode | Hints | Tutor | Timing | Scoring |
|---|---|---|---|---|
| guided | staged unlocks, cost deducted | next-step nudges ≤ unlocked level | par time shown, no penalty | objectives − hints + remediation bonus |
| challenge | staged unlocks, cost deducted | methodology only | par shown | same as guided (no procedural help given) |
| assessment | max 1 unlock, then 403 | refusal (timer/tool docs only) | TTL capped ≤30 min, `finalize` freezes score | + time bonus (≤20) for finishing under par |
| demo | free, no cost | full walkthrough | resettable anytime | not scored |

## Rules
- Hint unlocks are sequential per session; each deducts its manifest `cost` from the final score.
- Assessment `finalize` sets status `finalized`: submissions and unlocks rejected (409), score immutable.
- Remediation bonus (+25) rewards the fix + retest, not just capture.
- Flags stay per-session HMAC; reset rotates seed AND re-provisions targets.
