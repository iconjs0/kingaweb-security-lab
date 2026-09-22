# TZ-Local Track: M-Pesa Mock + Kiswahili Early

Why: generic Juice Shop doesn't teach what TZ juniors will actually test — mobile-money callbacks, USSD, price-in-KES logic. All mocks, no real money, no real telco.

## Mock (`labs/mocks/mpesa/`, runs in compose as `mpesa-mock:5009`)
- `POST /c2b/validate` — BOLA lab: `account` param must be server-bound to authenticated user (vuln version trusts client `account`).
- `POST /stk/callback` — signature lab: accepts `signature` header; vuln version skips HMAC check → forged "payment success".
- `GET /healthz`, `GET /rates` (KES). All data in-memory, reset on session recreate. No egress.
- Image built locally (`Dockerfile`), never pushed with vulns; digest pinned at publish.

## Lab (`labs/kingaweb-native/mpesa-bola/lab.yaml`)
BOLA on `account` + callback forgery, then remediation (server-side binding + HMAC verify). Includes `i18n/en.json` + `i18n/sw.json` — Kiswahili from day one for this track (rest of platform follows later).

## Safety
Mock binds to session network only; callback secret per-session (same HMAC scheme as flags); amount caps; no real phone numbers (test MSISDN `255700000000` only).
