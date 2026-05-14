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

mkdir -p .jenkins
KUBECONFIG_SOURCE="${KUBECONFIG:-${HOME}/.kube/config}"
export JENKINS_KUBECONFIG="${PWD}/.jenkins/kubeconfig"

if [[ -f "$KUBECONFIG_SOURCE" ]] && command -v kubectl >/dev/null 2>&1; then
  kubectl config view --raw --flatten > "$JENKINS_KUBECONFIG"
  python3 - "$JENKINS_KUBECONFIG" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()
rewritten = re.sub(
    r"server: https://(?:127\.0\.0\.1|localhost):",
    "server: https://host.docker.internal:",
    text,
)
if rewritten != text and "tls-server-name:" not in rewritten:
    rewritten = re.sub(
        r"(^\s+server: https://host\.docker\.internal:\d+\s*$)",
        r"\1\n    tls-server-name: localhost",
        rewritten,
        flags=re.MULTILINE,
    )
path.write_text(rewritten)
PY
  echo "Prepared Jenkins kubeconfig at ${JENKINS_KUBECONFIG}"
else
  cat > "$JENKINS_KUBECONFIG" <<'EOF'
apiVersion: v1
clusters: []
contexts: []
current-context: ""
kind: Config
preferences: {}
users: []
EOF
  echo "No kubeconfig found; Jenkins will start, but Kubernetes deploy needs a cluster."
fi

docker compose -f docker-compose.jenkins.yml up --build -d

echo "Jenkins is starting at http://localhost:8080"
echo "Seeded pipeline job: automated-chaos-platform"
