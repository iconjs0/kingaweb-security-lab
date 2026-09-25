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
build web-idor-01
build web-sqli-01
build web-xss-01
build web-ssrf-01
build api-bola-01
build api-mass-01
build api-jwt-01
build api-ratelimit-01
build api-graphql-01
build web-csrf-01
build web-traversal-01
build web-upload-01
build web-crypto-01
docker build -f labs/mocks/mpesa/Dockerfile -t local-mpesa-mock labs/mocks/mpesa
docker build -f labs/mocks/internal-meta/Dockerfile -t local-internal-meta labs/mocks/internal-meta
docker images --format "{{.Repository}}" | grep -E "^local-" | sort
