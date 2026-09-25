#!/usr/bin/env bash
# Blackbox: load. Parallel learners through launch/solve/destroy.
# Usage: ./scripts/blackbox/bb-load.sh [users] [rounds]
# Requires: stack up. Default 8x2 (~2 min). Capacity note: 12 concurrent ≈ p95 25s here.
set -u
U="${1:-8}"
R="${2:-2}"
python3 scripts/load/soak.py --users "$U" --rounds "$R"
