#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"

curl -fsS "$BASE_URL/healthz"
echo
python3 tools/load-generator/load_generator.py --url "$BASE_URL" --jobs 10 --concurrency 3
curl -fsS "$BASE_URL/metrics"
echo
