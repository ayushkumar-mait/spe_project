#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "Starting Elasticsearch..."
docker compose up -d elasticsearch

echo "Waiting for Elasticsearch on http://localhost:9200 ..."
for _ in $(seq 1 90); do
  if curl -fsS "http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=5s" >/dev/null 2>&1; then
    curl -fsS "http://localhost:9200/_cluster/health?pretty"
    break
  fi
  sleep 2
done

if ! curl -fsS "http://localhost:9200/_cluster/health?wait_for_status=yellow&timeout=5s" >/dev/null 2>&1; then
  echo "Elasticsearch did not become healthy. Check: docker compose logs elasticsearch" >&2
  exit 1
fi

echo "Starting Kibana..."
docker compose up -d kibana

echo "Waiting for Kibana on http://localhost:5601 ..."
for _ in $(seq 1 120); do
  body="$(curl -s --max-time 15 "http://localhost:5601" 2>/dev/null || true)"
  if printf "%s" "$body" | grep -q "<title>Elastic</title>"; then
    break
  fi
  sleep 2
done

body="$(curl -s --max-time 15 "http://localhost:5601" 2>/dev/null || true)"
if ! printf "%s" "$body" | grep -q "<title>Elastic</title>"; then
  echo "Kibana did not become ready. Check: docker compose logs kibana" >&2
  exit 1
fi

echo "Starting Logstash..."
docker compose up -d logstash

echo "ELK is ready:"
docker compose ps elasticsearch logstash kibana
echo
echo "Open Kibana: http://localhost:5601"
