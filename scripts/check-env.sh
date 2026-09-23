#!/usr/bin/env bash
# Validate .env for production: no placeholders, minimum lengths.
# Usage: ./scripts/check-env.sh [.env]
set -u
F="${1:-.env}"
fail=0
need() { grep -q "^$1=" "$F" || { echo "missing: $1"; fail=1; }; }
checklen() {
  v=$(grep "^$1=" "$F" | cut -d= -f2)
  [ "${#v}" -ge "$2" ] || { echo "too short (<$2): $1"; fail=1; }
}
[ -f "$F" ] || { echo "no $F (cp .env.example .env)"; exit 1; }
grep -q "change-me" "$F" && { echo "placeholders present"; fail=1; }
need FLAG_HMAC_SECRET; checklen FLAG_HMAC_SECRET 32
need ORCHESTRATOR_TOKEN; checklen ORCHESTRATOR_TOKEN 16
need INTEL_TOKEN; checklen INTEL_TOKEN 16
[ "$fail" = "0" ] && echo "env OK" || exit 1
