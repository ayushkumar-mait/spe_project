#!/usr/bin/env bash
set -euo pipefail

if [[ -S "${HOME}/.docker/run/docker.sock" ]]; then
  export DOCKER_HOST_SOCK="${HOME}/.docker/run/docker.sock"
elif [[ -S "/var/run/docker.sock" ]]; then
  export DOCKER_HOST_SOCK="/var/run/docker.sock"
else
  echo "Docker socket not found. Start Docker Desktop first." >&2
  exit 1
fi

docker compose -f docker-compose.jenkins.yml up --build -d

echo "Jenkins is starting at http://localhost:8080"
echo "Seeded pipeline job: automated-chaos-platform"

