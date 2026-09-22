#!/usr/bin/env bash
# Build all first-party lab target images (root context: Dockerfiles COPY the shared flag SDK).
# Usage: ./scripts/build-lab-images.sh
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
build() { docker build -f "labs/kingaweb-native/$1/Dockerfile" -t "local-lab-$1" .; }
build web-http-01
build web-cookies-01
build web-headers-01
build web-authz-01
build web-report-01
docker build -f labs/mocks/mpesa/Dockerfile -t local-mpesa-mock labs/mocks/mpesa
docker images --format "{{.Repository}}" | grep -E "^local-(lab|mpesa)" | sort
