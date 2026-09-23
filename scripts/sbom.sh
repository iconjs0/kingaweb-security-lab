#!/usr/bin/env bash
# SBOM-lite: dependency inventory + image digests. (Full CycloneDX/Sigstore at signing time.)
# Usage: ./scripts/sbom.sh
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
OUT="sbom.json"
python3 - <<'EOF' > "$OUT"
import json, subprocess
def reqs(p):
    try:
        return [l.strip() for l in open(p) if l.strip() and not l.startswith("#")]
    except FileNotFoundError:
        return []
imgs = subprocess.run(["docker", "images", "--format", "{{.Repository}}:{{.Tag}} {{.Digest}}"],
                      capture_output=True, text=True).stdout.splitlines()
print(json.dumps({
    "tool": "sbom-lite",
    "python": {s: reqs(f"services/{s}/requirements.txt") for s in ["api", "orchestrator", "intelligence"]},
    "node": "see package-lock.json",
    "images": [dict(zip(("ref", "digest"), l.rsplit(" ", 1))) for l in imgs if l.startswith("local-")],
}, indent=2))
EOF
echo "wrote $OUT"
