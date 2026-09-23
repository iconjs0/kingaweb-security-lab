#!/usr/bin/env bash
# Verify every lab target is digest-pinned (no LOCAL_BUILD / latest) — publish gate.
# Usage: ./scripts/verify-digests.sh [labsdir]
set -u
D="${1:-labs}"
fails=0
for f in $(find "$D" -name lab.yaml); do
  while IFS= read -r img; do
    case "$img" in
      *@sha256:*LOCAL_BUILD*|*@sha256:*0000*|*:latest*)
        echo "UNPINNED: $f -> $img"; fails=1;;
    esac
  done < <(grep -o 'image: "[^"]*"' "$f" | cut -d'"' -f2)
done
[ "$fails" = "0" ] && echo "digests OK (or no labs)" || { echo "publish blocked: pin digests"; exit 1; }
