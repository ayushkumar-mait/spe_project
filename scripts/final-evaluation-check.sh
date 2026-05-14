#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

pass() {
  printf 'PASS: %s\n' "$1"
}

warn() {
  printf 'WARN: %s\n' "$1"
}

need_command() {
  if command -v "$1" >/dev/null 2>&1; then
    pass "$1 available"
  else
    warn "$1 not installed; related live demo step must be run on a machine with $1"
  fi
}

select_pytest_python() {
  local candidate
  for candidate in "${PYTHON_BIN:-}" python3 /opt/anaconda3/bin/python3; do
    if [ -n "$candidate" ] && command -v "$candidate" >/dev/null 2>&1 && "$candidate" -m pytest --version >/dev/null 2>&1; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

printf '\n== Tooling ==\n'
need_command git
need_command docker
need_command kubectl
need_command ansible-playbook
need_command python3
need_command mvn

printf '\n== Git / Jenkins SCM ==\n'
git rev-parse --is-inside-work-tree >/dev/null
pass "repository is a Git working tree"
if git remote -v | grep -q .; then
  git remote -v
  pass "Git remote configured"
else
  warn "no Git remote configured yet; add GitHub remote before final webhook demo"
fi
grep -q "githubPush()" Jenkinsfile
pass "Jenkinsfile declares GitHub push trigger"
grep -q "SCMTrigger" infra/jenkins/init.groovy.d/seed-platform-job.groovy
pass "local Jenkins job has SCM polling fallback"

printf '\n== Tests ==\n'
PYTEST_PYTHON="$(select_pytest_python)"
pass "using ${PYTEST_PYTHON} for Python tests"
"$PYTEST_PYTHON" -m pytest
pass "Python tests passed"
mvn -q -f services/order-api/pom.xml test
pass "Spring Boot tests passed"

printf '\n== Docker Compose ==\n'
docker compose -p chaos-demo -f docker-compose.demo.yml config >/tmp/chaos-demo-compose-check.yml
pass "lean Docker Compose demo config is valid"
docker compose -f docker-compose.yml config >/tmp/chaos-full-compose-check.yml
pass "full Docker Compose config with ELK/Vault is valid"
grep -q "topic-init" /tmp/chaos-demo-compose-check.yml
grep -q "topic-init" /tmp/chaos-full-compose-check.yml
pass "Docker Compose initializes Kafka topic partitions for real worker scaling"

printf '\n== Kubernetes Manifests ==\n'
kubectl kustomize k8s/base >/tmp/job-platform-kustomize-base.yml
kubectl kustomize k8s/overlays/local >/tmp/job-platform-kustomize-local.yml
kubectl kustomize k8s/overlays/dev >/tmp/job-platform-kustomize-dev.yml
kubectl kustomize k8s/overlays/prod >/tmp/job-platform-kustomize-prod.yml
pass "Kubernetes base/local/dev/prod manifests render successfully"
grep -q "kind: HorizontalPodAutoscaler" /tmp/job-platform-kustomize-base.yml
pass "Kubernetes HPA is included"
grep -q "name: redpanda-topic-init" /tmp/job-platform-kustomize-base.yml
pass "Kubernetes initializes Kafka topic partitions"
grep -q "vault.hashicorp.com/agent-inject" /tmp/job-platform-kustomize-base.yml
pass "Vault Agent annotations are included"

printf '\n== Ansible ==\n'
if command -v ansible-playbook >/dev/null 2>&1; then
  (cd ansible && ansible-playbook --syntax-check site.yml)
  pass "Ansible playbook syntax is valid"
fi

printf '\n== Observability / ELK ==\n'
test -f observability/k8s/elk-stack.yaml
test -f observability/k8s/filebeat-daemonset.yaml
test -f observability/logstash/pipeline/logstash.conf
pass "ELK and Filebeat manifests/config exist"

printf '\n== Security ==\n'
test -f vault/policies/job-platform.hcl
test -x vault/scripts/bootstrap-vault.sh
grep -q "optional:file.*platform.env" services/order-api/src/main/resources/application.yml
pass "Vault policy, bootstrap script, and Spring Boot Vault env import are present"

printf '\n== Runtime Smoke Check ==\n'
if curl -fsS http://localhost:8000/healthz >/tmp/order-api-health.json 2>/dev/null; then
  cat /tmp/order-api-health.json
  printf '\n'
  curl -fsS http://localhost:8000/readyz
  printf '\n'
  curl -fsS http://localhost:8000/metrics
  printf '\n'
  pass "local Order API runtime is healthy"
else
  warn "local Order API not running; start with docker compose -p chaos-demo -f docker-compose.demo.yml up -d --scale worker=3"
fi

printf '\nFinal evaluation readiness check complete.\n'
